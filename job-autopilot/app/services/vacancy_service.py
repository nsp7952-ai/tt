from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.models import Vacancy, Application, Contact, EventLog
from app.database import engine
from loguru import logger


class VacancyService:
    """Сервис для управления вакансиями."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_vacancy_id(self, source: str, url: str) -> str:
        """Сгенерировать уникальный ID для вакансии на основе source + url hash."""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        return f"{source}_{url_hash}"
    
    def get_by_url(self, source: str, url: str) -> Optional[Vacancy]:
        """Проверить, существует ли вакансия с таким URL."""
        vacancy_id = self.generate_vacancy_id(source, url)
        return self.session.get(Vacancy, vacancy_id)

    async def process_telegram_vacancies(
        self,
        messages: List[Dict[str, Any]],
        llm_service
    ) -> Dict[str, Any]:
        """
        Обработать сообщения из Telegram и создать вакансии/контакты.
        Возвращает статистику обработки.
        """
        stats = {
            "processed": 0,
            "vacancies_created": 0,
            "contacts_created": 0,
            "duplicates": 0,
            "errors": 0
        }

        for msg in messages:
            try:
                stats["processed"] += 1

                # Парсим пост через LLM
                parsed = await llm_service.parse_telegram_post(msg["text"])

                if not parsed or not parsed.get("is_vacancy"):
                    logger.debug(f"Message {msg['message_id']} is not a vacancy")
                    continue

                # Создаем URL (для Telegram используем ссылку на сообщение)
                url = f"https://t.me/{msg['channel']}/{msg['message_id']}"

                # Создаем или обновляем вакансию
                vacancy = self.create_or_update(
                    source="telegram_channels",
                    url=url,
                    title=parsed.get("title") or "Unknown",
                    company=parsed.get("company"),
                    location=None,
                    remote=parsed.get("remote", False),
                    grade_hint=parsed.get("grade"),
                    salary_text=parsed.get("salary_text"),
                    description_text=msg["text"],
                    raw_json=parsed,
                    status="new"
                )

                if vacancy:
                    stats["vacancies_created"] += 1

                    # Извлекаем контакты
                    if parsed.get("contact_tg"):
                        from app.services.contact_service import ContactService
                        contact_service = ContactService(self.session)
                        contact, is_new = contact_service.create_or_get(
                            source="telegram_channels",
                            contact_type="telegram",
                            value_raw=parsed["contact_tg"],
                            vacancy_id=vacancy.id,
                            company=parsed.get("company")
                        )
                        if is_new:
                            stats["contacts_created"] += 1
                        else:
                            stats["duplicates"] += 1

                    if parsed.get("contact_email"):
                        from app.services.contact_service import ContactService
                        contact_service = ContactService(self.session)
                        contact, is_new = contact_service.create_or_get(
                            source="telegram_channels",
                            contact_type="email",
                            value_raw=parsed["contact_email"],
                            vacancy_id=vacancy.id,
                            company=parsed.get("company")
                        )
                        if is_new:
                            stats["contacts_created"] += 1
                        else:
                            stats["duplicates"] += 1

            except Exception as e:
                logger.error(f"Error processing Telegram message: {e}")
                stats["errors"] += 1

        return stats
    
    def create_or_update(
        self,
        source: str,
        url: str,
        title: str,
        company: Optional[str] = None,
        location: Optional[str] = None,
        remote: Optional[bool] = None,
        grade_hint: Optional[str] = None,
        salary_text: Optional[str] = None,
        description_text: Optional[str] = None,
        raw_json: Optional[Dict[str, Any]] = None,
        status: str = "new"
    ) -> Vacancy:
        """Создать или обновить вакансию (идемпотентность)."""
        vacancy_id = self.generate_vacancy_id(source, url)
        existing = self.session.get(Vacancy, vacancy_id)
        
        if existing:
            # Обновляем существующую
            existing.title = title
            existing.company = company
            existing.location = location
            existing.remote = remote
            existing.grade_hint = grade_hint
            existing.salary_text = salary_text
            existing.description_text = description_text
            if raw_json:
                existing.raw_json = raw_json
            existing.status = status
            existing.updated_at = datetime.utcnow()
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # Создаем новую
            vacancy = Vacancy(
                id=vacancy_id,
                source=source,
                source_id=None,
                url=url,
                title=title,
                company=company,
                location=location,
                remote=remote,
                grade_hint=grade_hint,
                salary_text=salary_text,
                description_text=description_text,
                raw_json=raw_json or {},
                status=status
            )
            self.session.add(vacancy)
            self.session.commit()
            self.session.refresh(vacancy)
            
            # Log event
            self.log_event("vacancy_created", vacancy.id, {"title": title, "company": company})
            
            return vacancy
    
    def update_status(self, vacancy_id: str, status: str, match_score: Optional[int] = None, 
                      match_reason: Optional[str] = None, skip_reason: Optional[str] = None) -> Vacancy:
        """Обновить статус вакансии."""
        vacancy = self.session.get(Vacancy, vacancy_id)
        if not vacancy:
            raise ValueError(f"Vacancy {vacancy_id} not found")
        
        vacancy.status = status
        if match_score is not None:
            vacancy.match_score = match_score
        if match_reason:
            vacancy.match_reason = match_reason
        if skip_reason:
            vacancy.skip_reason = skip_reason
        vacancy.updated_at = datetime.utcnow()
        
        self.session.add(vacancy)
        self.session.commit()
        self.session.refresh(vacancy)
        
        self.log_event("vacancy_status_updated", vacancy_id, {"status": status})
        
        return vacancy
    
    def get_all(self, limit: int = 100, offset: int = 0, status_filter: Optional[str] = None,
                source_filter: Optional[str] = None) -> List[Vacancy]:
        """Получить список вакансий."""
        query = select(Vacancy).order_by(Vacancy.created_at.desc())
        
        if status_filter:
            query = query.where(Vacancy.status == status_filter)
        if source_filter:
            query = query.where(Vacancy.source == source_filter)
        
        query = query.offset(offset).limit(limit)
        return self.session.exec(query).all()
    
    def get_by_id(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получить вакансию по ID."""
        return self.session.get(Vacancy, vacancy_id)
    
    def log_event(self, event_type: str, entity_id: str, data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="vacancy",
            entity_id=entity_id,
            message=f"Vacancy event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить статистику по вакансиям."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(Vacancy).where(Vacancy.created_at >= cutoff)
        vacancies = self.session.exec(query).all()
        
        stats = {
            "total": len(vacancies),
            "by_status": {},
            "by_source": {},
            "matched": 0,
            "filtered_out": 0,
            "applied": 0
        }
        
        for v in vacancies:
            # By status
            stats["by_status"][v.status] = stats["by_status"].get(v.status, 0) + 1
            
            # By source
            stats["by_source"][v.source] = stats["by_source"].get(v.source, 0) + 1
            
            # Counters
            if v.status == "matched":
                stats["matched"] += 1
            elif v.status == "filtered_out":
                stats["filtered_out"] += 1
            elif v.status == "applied":
                stats["applied"] += 1
        
        return stats


class ApplicationService:
    """Сервис для управления откликами."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_application_id(self, vacancy_id: str) -> str:
        """Сгенерировать ID для отклика."""
        return f"app_{uuid.uuid4().hex[:12]}"
    
    def create_or_get(
        self,
        vacancy_id: str,
        source: str,
        cover_letter: Optional[str] = None,
        generated_answers_json: Optional[Dict[str, Any]] = None,
        agent_task_id: Optional[str] = None
    ) -> Application:
        """Создать или получить существующий отклик."""
        # Check if application already exists for this vacancy
        existing = self.session.exec(
            select(Application).where(Application.vacancy_id == vacancy_id)
        ).first()
        
        if existing:
            return existing
        
        application = Application(
            id=self.generate_application_id(vacancy_id),
            vacancy_id=vacancy_id,
            source=source,
            status="pending",
            cover_letter=cover_letter,
            generated_answers_json=generated_answers_json,
            agent_task_id=agent_task_id
        )
        
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        
        return application
    
    def update_status(self, application_id: str, status: str, 
                      external_status: Optional[str] = None,
                      error: Optional[str] = None) -> Application:
        """Обновить статус отклика."""
        application = self.session.get(Application, application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        application.status = status
        if external_status:
            application.external_status = external_status
        if error:
            application.error = error
        application.updated_at = datetime.utcnow()
        
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        
        return application
    
    def get_all(self, limit: int = 100, status_filter: Optional[str] = None) -> List[Application]:
        """Получить список откликов."""
        query = select(Application).order_by(Application.created_at.desc())
        
        if status_filter:
            query = query.where(Application.status == status_filter)
        
        query = query.limit(limit)
        return self.session.exec(query).all()
    
    def get_by_id(self, application_id: str) -> Optional[Application]:
        """Получить отклик по ID."""
        return self.session.get(Application, application_id)
    
    def get_by_vacancy(self, vacancy_id: str) -> Optional[Application]:
        """Получить отклик по vacancy_id."""
        return self.session.exec(
            select(Application).where(Application.vacancy_id == vacancy_id)
        ).first()
