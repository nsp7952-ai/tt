from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import re

from app.models import Contact, EventLog


class ContactService:
    """Сервис для управления контактами."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_contact_id(self) -> str:
        """Сгенерировать ID для контакта."""
        return f"cnt_{uuid.uuid4().hex[:12]}"
    
    def normalize_contact_value(self, contact_type: str, value: str) -> str:
        """Нормализовать значение контакта."""
        value = value.strip()
        
        if contact_type == "telegram":
            # Normalize Telegram username
            value = value.lstrip("@")
            value = re.sub(r'[^a-zA-Z0-9_]', '', value)
            return value.lower()
        
        elif contact_type == "email":
            return value.lower()
        
        elif contact_type == "phone":
            # Remove all non-digit characters except +
            value = re.sub(r'[^\d+]', '', value)
            return value
        
        return value.lower()
    
    def find_duplicate(self, contact_type: str, normalized_value: str) -> Optional[Contact]:
        """Проверить на дубликат."""
        existing = self.session.exec(
            select(Contact).where(
                (Contact.contact_type == contact_type) &
                (Contact.value_normalized == normalized_value)
            )
        ).first()
        return existing
    
    def create_or_get(
        self,
        source: str,
        contact_type: str,
        value_raw: str,
        vacancy_id: Optional[str] = None,
        company: Optional[str] = None,
        person_name: Optional[str] = None,
        role_hint: Optional[str] = None
    ) -> tuple[Contact, bool]:
        """
        Создать или получить существующий контакт.
        Возвращает (contact, is_new) - контакт и флаг是新ый ли он.
        """
        normalized = self.normalize_contact_value(contact_type, value_raw)
        
        # Check for duplicate
        existing = self.find_duplicate(contact_type, normalized)
        
        if existing:
            # Update related info if needed
            if vacancy_id and not existing.vacancy_id:
                existing.vacancy_id = vacancy_id
            if company and not existing.company:
                existing.company = company
            self.session.add(existing)
            self.session.commit()
            return existing, False
        
        # Create new contact
        contact = Contact(
            id=self.generate_contact_id(),
            source=source,
            vacancy_id=vacancy_id,
            company=company,
            person_name=person_name,
            role_hint=role_hint,
            contact_type=contact_type,
            value_normalized=normalized,
            value_raw=value_raw,
            status="new"
        )
        
        self.session.add(contact)
        self.session.commit()
        self.session.refresh(contact)
        
        # Log event
        self.log_event("contact_created", contact.id, {
            "type": contact_type,
            "company": company,
            "person_name": person_name
        })
        
        return contact, True
    
    def update_status(self, contact_id: str, status: str) -> Contact:
        """Обновить статус контакта."""
        contact = self.session.get(Contact, contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        contact.status = status
        contact.updated_at = datetime.utcnow()
        
        self.session.add(contact)
        self.session.commit()
        self.session.refresh(contact)
        
        return contact
    
    def get_all(self, limit: int = 100, status_filter: Optional[str] = None,
                contact_type_filter: Optional[str] = None) -> List[Contact]:
        """Получить список контактов."""
        query = select(Contact).order_by(Contact.created_at.desc())
        
        if status_filter:
            query = query.where(Contact.status == status_filter)
        if contact_type_filter:
            query = query.where(Contact.contact_type == contact_type_filter)
        
        query = query.limit(limit)
        return self.session.exec(query).all()
    
    def get_by_id(self, contact_id: str) -> Optional[Contact]:
        """Получить контакт по ID."""
        return self.session.get(Contact, contact_id)
    
    def get_queued_for_outreach(self, limit: int = 50) -> List[Contact]:
        """Получить контакты, ожидающие outreach."""
        return self.session.exec(
            select(Contact)
            .where(Contact.status == "new")
            .order_by(Contact.created_at)
            .limit(limit)
        ).all()
    
    def log_event(self, event_type: str, entity_id: str, data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="contact",
            entity_id=entity_id,
            message=f"Contact event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить статистику по контактам."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = select(Contact).where(Contact.created_at >= cutoff)
        contacts = self.session.exec(query).all()
        
        stats = {
            "total": len(contacts),
            "by_status": {},
            "by_type": {},
            "outreach_sent": 0,
            "replied": 0
        }
        
        for c in contacts:
            stats["by_status"][c.status] = stats["by_status"].get(c.status, 0) + 1
            stats["by_type"][c.contact_type] = stats["by_type"].get(c.contact_type, 0) + 1
            
            if c.status == "outreach_sent":
                stats["outreach_sent"] += 1
            elif c.status == "replied":
                stats["replied"] += 1
        
        return stats
