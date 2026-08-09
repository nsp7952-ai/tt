from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.models import Contact, OutreachMessage, EventLog
from app.services.llm_service import LLMService
from app.telegram.client import TelegramClientService
from loguru import logger


class OutreachService:
    """Сервис для отправки outreach сообщений контактам."""

    def __init__(self, session: Session):
        self.session = session
        self.llm_service = LLMService()
        self.telegram_service = TelegramClientService(session)

    def generate_message_id(self) -> str:
        """Сгенерировать ID для сообщения."""
        return f"out_{uuid.uuid4().hex[:12]}"

    async def generate_outreach_message(
        self,
        contact: Contact,
        profile_context: str,
        cv_text: str,
        vacancy_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Сгенерировать outreach сообщение для контакта."""
        if not vacancy_data:
            vacancy_data = {
                "title": contact.role_hint or "Developer",
                "company": contact.company or "Unknown",
                "description_text": ""
            }

        result = await self.llm_service.generate_outreach(
            profile_context=profile_context,
            vacancy_data=vacancy_data,
            contact_data={
                "person_name": contact.person_name,
                "role_hint": contact.role_hint,
                "contact_type": contact.contact_type
            }
        )

        return result

    async def send_telegram_outreach(
        self,
        contact: Contact,
        message_text: str,
        account_name: str = "outreach",
        attach_cv: bool = False,
        cv_file_path: Optional[str] = None
    ) -> bool:
        """Отправить outreach сообщение в Telegram."""
        if contact.contact_type != "telegram":
            logger.warning(f"Contact {contact.id} is not a Telegram contact")
            return False

        # Формируем username
        username = contact.value_normalized
        if not username.startswith("@"):
            username = f"@{username}"

        success = await self.telegram_service.send_message(
            account_name=account_name,
            recipient=username,
            text=message_text,
            file_path=cv_file_path if attach_cv else None
        )

        if success:
            # Обновляем статус контакта
            contact.status = "outreach_sent"
            self.session.add(contact)

            # Создаем запись о сообщении
            outreach_msg = OutreachMessage(
                id=self.generate_message_id(),
                contact_id=contact.id,
                channel="telegram",
                subject=None,
                body=message_text,
                cv_attached=attach_cv,
                status="sent",
                sent_at=datetime.utcnow()
            )
            self.session.add(outreach_msg)
            self.session.commit()

            self.log_event("outreach_sent", contact.id, {
                "channel": "telegram",
                "recipient": username,
                "account": account_name
            })

            logger.info(f"Outreach sent to {username} via {account_name}")
        else:
            # Записываем ошибку
            outreach_msg = OutreachMessage(
                id=self.generate_message_id(),
                contact_id=contact.id,
                channel="telegram",
                subject=None,
                body=message_text,
                cv_attached=attach_cv,
                status="failed",
                error="Failed to send message"
            )
            self.session.add(outreach_msg)

            contact.status = "failed"
            self.session.add(contact)
            self.session.commit()

            self.log_event("outreach_failed", contact.id, {
                "channel": "telegram",
                "recipient": username,
                "error": "Failed to send message"
            })

        return success

    def create_draft(
        self,
        contact: Contact,
        message_text: str,
        subject: Optional[str] = None
    ) -> OutreachMessage:
        """Создать черновик сообщения."""
        outreach_msg = OutreachMessage(
            id=self.generate_message_id(),
            contact_id=contact.id,
            channel="telegram" if contact.contact_type == "telegram" else "email",
            subject=subject,
            body=message_text,
            cv_attached=False,
            status="draft"
        )

        self.session.add(outreach_msg)
        self.session.commit()
        self.session.refresh(outreach_msg)

        self.log_event("outreach_draft_created", contact.id, {
            "message_id": outreach_msg.id
        })

        return outreach_msg

    def get_pending_outreach(self, limit: int = 50) -> List[Contact]:
        """Получить контакты, ожидающие outreach."""
        contacts = self.session.exec(
            select(Contact)
            .where(Contact.status == "new")
            .order_by(Contact.created_at)
            .limit(limit)
        ).all()

        return contacts

    def update_message_status(
        self,
        message_id: str,
        status: str,
        error: Optional[str] = None
    ) -> OutreachMessage:
        """Обновить статус сообщения."""
        message = self.session.get(OutreachMessage, message_id)
        if not message:
            raise ValueError(f"OutreachMessage {message_id} not found")

        message.status = status
        if error:
            message.error = error
        if status == "sent":
            message.sent_at = datetime.utcnow()

        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)

        return message

    def get_all_messages(
        self,
        limit: int = 100,
        status_filter: Optional[str] = None,
        contact_id: Optional[str] = None
    ) -> List[OutreachMessage]:
        """Получить список outreach сообщений."""
        query = select(OutreachMessage).order_by(OutreachMessage.created_at.desc())

        if status_filter:
            query = query.where(OutreachMessage.status == status_filter)
        if contact_id:
            query = query.where(OutreachMessage.contact_id == contact_id)

        query = query.limit(limit)
        return self.session.exec(query).all()

    def get_message_by_id(self, message_id: str) -> Optional[OutreachMessage]:
        """Получить сообщение по ID."""
        return self.session.get(OutreachMessage, message_id)

    def log_event(self, event_type: str, entity_id: str, data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="outreach",
            entity_id=entity_id,
            message=f"Outreach event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить статистику по outreach."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(OutreachMessage).where(OutreachMessage.created_at >= cutoff)
        messages = self.session.exec(query).all()

        stats = {
            "total": len(messages),
            "by_status": {},
            "by_channel": {},
            "sent": 0,
            "failed": 0,
            "replied": 0,
            "cv_attached": 0
        }

        for m in messages:
            stats["by_status"][m.status] = stats["by_status"].get(m.status, 0) + 1
            stats["by_channel"][m.channel] = stats["by_channel"].get(m.channel, 0) + 1

            if m.status == "sent":
                stats["sent"] += 1
            elif m.status == "failed":
                stats["failed"] += 1
            elif m.status == "replied":
                stats["replied"] += 1

            if m.cv_attached:
                stats["cv_attached"] += 1

        return stats
