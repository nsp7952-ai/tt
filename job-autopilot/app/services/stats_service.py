from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models import EventLog


class StatsService:
    """Сервис для сбора и агрегации статистики."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_dashboard_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Получить статистику для dashboard."""
        from datetime import timedelta
        from app.models import Vacancy, Application, Contact, OutreachMessage
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Vacancies stats
        vacancies_query = select(Vacancy).where(Vacancy.created_at >= cutoff)
        vacancies = self.session.exec(vacancies_query).all()
        
        # Applications stats
        apps_query = select(Application).where(Application.created_at >= cutoff)
        applications = self.session.exec(apps_query).all()
        
        # Contacts stats
        contacts_query = select(Contact).where(Contact.created_at >= cutoff)
        contacts = self.session.exec(contacts_query).all()
        
        # Outreach stats
        outreach_query = select(OutreachMessage).where(OutreachMessage.created_at >= cutoff)
        outreach_messages = self.session.exec(outreach_query).all()
        
        return {
            "period_hours": hours,
            "vacancies": {
                "total": len(vacancies),
                "by_status": self._count_by_field(vacancies, "status"),
                "by_source": self._count_by_field(vacancies, "source")
            },
            "applications": {
                "total": len(applications),
                "by_status": self._count_by_field(applications, "status"),
                "submitted": sum(1 for a in applications if a.status == "submitted")
            },
            "contacts": {
                "total": len(contacts),
                "by_type": self._count_by_field(contacts, "contact_type"),
                "outreach_sent": sum(1 for c in contacts if c.status == "outreach_sent")
            },
            "outreach": {
                "total": len(outreach_messages),
                "sent": sum(1 for m in outreach_messages if m.status == "sent"),
                "failed": sum(1 for m in outreach_messages if m.status == "failed")
            }
        }
    
    def _count_by_field(self, items: list, field: str) -> Dict[str, int]:
        """Подсчитать количество по полю."""
        result = {}
        for item in items:
            value = getattr(item, field, None)
            if value:
                result[value] = result.get(value, 0) + 1
        return result
    
    def get_vacancy_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить детальную статистику по вакансиям."""
        from datetime import timedelta
        from app.models import Vacancy
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = select(Vacancy).where(Vacancy.created_at >= cutoff)
        vacancies = self.session.exec(query).all()
        
        stats = {
            "total": len(vacancies),
            "by_status": {},
            "by_source": {},
            "matched": 0,
            "filtered_out": 0,
            "applied": 0,
            "avg_match_score": 0,
            "top_skip_reasons": []
        }
        
        match_scores = []
        skip_reasons = {}
        
        for v in vacancies:
            stats["by_status"][v.status] = stats["by_status"].get(v.status, 0) + 1
            stats["by_source"][v.source] = stats["by_source"].get(v.source, 0) + 1
            
            if v.status == "matched":
                stats["matched"] += 1
            elif v.status == "filtered_out":
                stats["filtered_out"] += 1
            elif v.status == "applied":
                stats["applied"] += 1
            
            if v.match_score:
                match_scores.append(v.match_score)
            
            if v.skip_reason:
                skip_reasons[v.skip_reason] = skip_reasons.get(v.skip_reason, 0) + 1
        
        if match_scores:
            stats["avg_match_score"] = sum(match_scores) / len(match_scores)
        
        # Top skip reasons
        sorted_reasons = sorted(skip_reasons.items(), key=lambda x: x[1], reverse=True)
        stats["top_skip_reasons"] = [{"reason": r, "count": c} for r, c in sorted_reasons[:5]]
        
        return stats
    
    def get_application_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить детальную статистику по откликам."""
        from datetime import timedelta
        from app.models import Application
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = select(Application).where(Application.created_at >= cutoff)
        applications = self.session.exec(query).all()
        
        stats = {
            "total": len(applications),
            "by_status": {},
            "by_source": {},
            "submitted": 0,
            "failed": 0,
            "pending": 0
        }
        
        for app in applications:
            stats["by_status"][app.status] = stats["by_status"].get(app.status, 0) + 1
            stats["by_source"][app.source] = stats["by_source"].get(app.source, 0) + 1
            
            if app.status == "submitted":
                stats["submitted"] += 1
            elif app.status == "failed":
                stats["failed"] += 1
            elif app.status == "pending":
                stats["pending"] += 1
        
        return stats
    
    def get_contact_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить детальную статистику по контактам."""
        from datetime import timedelta
        from app.models import Contact
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = select(Contact).where(Contact.created_at >= cutoff)
        contacts = self.session.exec(query).all()
        
        stats = {
            "total": len(contacts),
            "by_type": {},
            "by_status": {},
            "by_source": {},
            "outreach_sent": 0,
            "replied": 0
        }
        
        for c in contacts:
            stats["by_type"][c.contact_type] = stats["by_type"].get(c.contact_type, 0) + 1
            stats["by_status"][c.status] = stats["by_status"].get(c.status, 0) + 1
            stats["by_source"][c.source] = stats["by_source"].get(c.source, 0) + 1
            
            if c.status == "outreach_sent":
                stats["outreach_sent"] += 1
            elif c.status == "replied":
                stats["replied"] += 1
        
        return stats
    
    def get_event_log_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получить статистику по событиям в логе."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = select(EventLog).where(EventLog.created_at >= cutoff)
        events = self.session.exec(query).all()
        
        stats = {
            "total": len(events),
            "by_type": {},
            "by_entity_type": {}
        }
        
        for e in events:
            stats["by_type"][e.event_type] = stats["by_type"].get(e.event_type, 0) + 1
            if e.entity_type:
                stats["by_entity_type"][e.entity_type] = stats["by_entity_type"].get(e.entity_type, 0) + 1
        
        return stats
