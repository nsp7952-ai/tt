from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models import EventLog


class AlertService:
    """Сервис для отправки алертов через Telegram bot."""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def send_alert(self, alert_type: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Отправить алерт в Telegram."""
        from app.config import settings
        
        bot_token = settings.TELEGRAM_ALERTS_BOT_TOKEN
        chat_id = settings.TELEGRAM_ALERTS_CHAT_ID
        
        if not bot_token or not chat_id:
            # Log but don't fail
            self.log_event("alert_skipped", None, {"reason": "telegram_not_configured"})
            return False
        
        # Format message with emoji based on type
        emoji_map = {
            "hr_message_received": "📨",
            "application_submitted": "✅",
            "application_failed": "❌",
            "contact_found": "🎯",
            "outreach_sent": "📤",
            "outreach_failed": "⚠️",
            "vacancy_matched": "💼",
            "vacancy_filtered": "🚫",
            "summary": "📊",
            "error": "🔴"
        }
        
        emoji = emoji_map.get(alert_type, "📢")
        formatted_message = f"{emoji} {message}"
        
        try:
            import httpx
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": formatted_message,
                        "parse_mode": "HTML"
                    }
                )
                response.raise_for_status()
                
            self.log_event("alert_sent", None, {"type": alert_type})
            return True
            
        except Exception as e:
            self.log_event("alert_failed", None, {"type": alert_type, "error": str(e)})
            return False
    
    async def send_summary(self, stats: Dict[str, Any], hours: int = 24):
        """Отправить сводку за период."""
        summary_lines = [
            f"📊 <b>Сводка за последние {hours}ч</b>",
            ""
        ]
        
        # Vacancies
        v_stats = stats.get("vacancies", {})
        summary_lines.append(f"💼 Вакансии: {v_stats.get('total', 0)}")
        
        # Applications
        a_stats = stats.get("applications", {})
        summary_lines.append(f"✅ Отклики: {a_stats.get('submitted', 0)}")
        
        # Contacts
        c_stats = stats.get("contacts", {})
        summary_lines.append(f"🎯 Контакты: {c_stats.get('total', 0)}")
        
        # Outreach
        o_stats = stats.get("outreach", {})
        summary_lines.append(f"📤 Outreach: {o_stats.get('sent', 0)}")
        
        message = "\n".join(summary_lines)
        
        return await self.send_alert("summary", message, stats)
    
    async def notify_hr_message(self, contact_info: str, message_preview: str):
        """Уведомить о входящем сообщении от HR."""
        message = f"<b>Новое сообщение от HR</b>\n\nКонтакт: {contact_info}\n\n{message_preview[:200]}"
        return await self.send_alert("hr_message_received", message)
    
    async def notify_application_submitted(self, vacancy_title: str, company: str):
        """Уведомить об успешном отклике."""
        message = f"<b>Отклик отправлен</b>\n\n{vacancy_title}\n{company}"
        return await self.send_alert("application_submitted", message)
    
    async def notify_application_failed(self, vacancy_title: str, error: str):
        """Уведомить о неудачном отклике."""
        message = f"<b>Отклик не удался</b>\n\n{vacancy_title}\n\nОшибка: {error}"
        return await self.send_alert("application_failed", message)
    
    async def notify_contact_found(self, company: str, contact_type: str):
        """Уведомить о найденном контакте."""
        message = f"<b>Найден контакт</b>\n\nКомпания: {company}\nТип: {contact_type}"
        return await self.send_alert("contact_found", message)
    
    async def notify_outreach_sent(self, contact_info: str):
        """Уведомить об отправленном outreach."""
        message = f"<b>Outreach отправлен</b>\n\n{contact_info}"
        return await self.send_alert("outreach_sent", message)
    
    async def notify_vacancy_matched(self, title: str, company: str, score: int):
        """Уведомить о подходящей вакансии."""
        message = f"<b>Подходящая вакансия</b>\n\n{title}\n{company}\nScore: {score}"
        return await self.send_alert("vacancy_matched", message)
    
    async def notify_error(self, error_message: str, context: Optional[str] = None):
        """Уведомить об ошибке."""
        message = f"<b>Ошибка</b>\n\n{error_message}"
        if context:
            message += f"\n\nКонтекст: {context}"
        return await self.send_alert("error", message)
    
    def log_event(self, event_type: str, entity_id: Optional[str], data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="alert",
            entity_id=entity_id,
            message=f"Alert event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()
