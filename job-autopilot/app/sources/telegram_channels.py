from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import TelegramChannel, Vacancy, Contact, TelegramAccount
from app.services.llm_service import LLMService
from app.services.filter_service import FilterService
from loguru import logger
import uuid


class TelegramChannelsSource:
    """Источник вакансий из Telegram каналов."""
    
    source_name = "telegram_channels"
    
    def __init__(self, session: Session):
        self.session = session
        self.llm_service = LLMService()
        self.filter_service = FilterService(session)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Получить новые сообщения из Telegram каналов.
        Использует Telethon для чтения каналов.
        """
        logger.info("Telegram channels source fetch called")
        
        # Получаем активные каналы
        channels = self.session.exec(
            select(TelegramChannel).where(TelegramChannel.enabled == True)
        ).all()
        
        if not channels:
            logger.warning("No enabled Telegram channels")
            return []
        
        # Здесь будет логика чтения через Telethon
        # На данный момент возвращаем пустой список
        logger.info(f"Found {len(channels)} enabled channels")
        return []
    
    async def parse_post(self, post_text: str) -> Optional[Dict[str, Any]]:
        """Распарсить пост Telegram и извлечь данные о вакансии."""
        if not self.llm_service.is_configured():
            logger.warning("LLM not configured for parsing")
            return None
        
        result = await self.llm_service.parse_telegram_post(post_text)
        return result
    
    async def collect_stats(self) -> Dict[str, Any]:
        """Собрать статистику по Telegram каналам."""
        channels_count = self.session.exec(
            select(TelegramChannel).where(TelegramChannel.enabled == True)
        ).all()
        
        vacancies_count = self.session.exec(
            select(Vacancy).where(Vacancy.source == "telegram_channels")
        ).all()
        
        contacts_count = self.session.exec(
            select(Contact).where(Contact.source == "telegram_channels")
        ).all()
        
        return {
            "source": "telegram_channels",
            "channels_monitored": len(channels_count),
            "vacancies_found": len(vacancies_count),
            "contacts_found": len(contacts_count),
        }
