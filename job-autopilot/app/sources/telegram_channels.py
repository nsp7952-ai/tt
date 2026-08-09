from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import TelegramChannel, Vacancy, Contact, TelegramAccount, Setting
from app.services.llm_service import LLMService
from app.services.filter_service import FilterService
from loguru import logger
import uuid
import hashlib
from datetime import datetime


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
        
        logger.info(f"Found {len(channels)} enabled channels")
        
        # Проверяем наличие настроек Telegram
        api_id_setting = self.session.get(Setting, "TELEGRAM_API_ID")
        api_hash_setting = self.session.get(Setting, "TELEGRAM_API_HASH")
        session_string_setting = self.session.get(Setting, "TELEGRAM_READER_SESSION")
        
        if not all([api_id_setting, api_hash_setting, session_string_setting]):
            logger.error("Telegram API credentials not configured")
            return []
        
        if not api_id_setting.value or not api_hash_setting.value or not session_string_setting.value:
            logger.error(f"Telegram API credentials are empty - API_ID: {bool(api_id_setting.value)}, API_HASH: {bool(api_hash_setting.value)}, SESSION: {bool(session_string_setting.value)}")
            return []
        
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            
            api_id = int(api_id_setting.value)
            api_hash = api_hash_setting.value
            session_string = session_string_setting.value
            
            # Создаем клиент
            string_session = StringSession(session_string)
            client = TelegramClient(string_session, api_id, api_hash)
            
            # Подключаемся
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error("Telegram session is not authorized")
                await client.disconnect()
                return []
            
            messages_data = []
            
            for channel in channels:
                try:
                    # Получаем последние сообщения
                    entity = await client.get_entity(channel.username_or_id)
                    
                    # Получаем последнее проверенное сообщение
                    last_msg_id = channel.last_message_id or 0
                    
                    # Получаем новые сообщения (последние 50)
                    async for message in client.iter_messages(entity, limit=50):
                        if message.id <= last_msg_id:
                            break
                        
                        if not message.text:
                            continue
                        
                        # Извлекаем данные
                        msg_data = {
                            "channel_id": channel.username_or_id,
                            "channel_name": channel.name,
                            "message_id": message.id,
                            "text": message.text,
                            "date": message.date.isoformat() if message.date else None,
                            "media": bool(message.media),
                        }
                        
                        messages_data.append(msg_data)
                        
                        # Обновляем last_message_id
                        if last_msg_id == 0 or message.id > last_msg_id:
                            last_msg_id = message.id
                    
                    # Обновляем канал
                    if last_msg_id > 0:
                        channel.last_message_id = last_msg_id
                        channel.last_checked_at = datetime.utcnow()
                        self.session.add(channel)
                        self.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error fetching channel {channel.username_or_id}: {e}")
                    continue
            
            await client.disconnect()
            
            logger.info(f"Fetched {len(messages_data)} messages from Telegram channels")
            return messages_data
            
        except Exception as e:
            logger.error(f"Error in Telegram fetch: {e}")
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
