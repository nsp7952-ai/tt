from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import TelegramChannel, Vacancy, Contact, TelegramAccount, Setting
from app.services.llm_service import LLMService
from app.services.filter_service import FilterService
from loguru import logger
import uuid
import hashlib
from datetime import datetime, timezone, timedelta


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
        Учитывает parse_depth_hours для каждого канала.
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
            from datetime import timedelta
            
            api_id = int(api_id_setting.value)
            api_hash = api_hash_setting.value
            session_string = session_string_setting.value
            
            logger.info(f"Connecting to Telegram with API ID {api_id}...")
            
            # Создаем клиент
            string_session = StringSession(session_string)
            client = TelegramClient(string_session, api_id, api_hash)
            
            # Подключаемся
            await client.connect()
            
            me = await client.get_me()
            logger.info(f"Connected as @{me.username} ({me.first_name})")
            
            if not await client.is_user_authorized():
                logger.error("Telegram session is not authorized")
                await client.disconnect()
                return []
            
            messages_data = []
            
            for channel in channels:
                try:
                    logger.info(f"Fetching channel: {channel.username_or_id} (last_msg_id={channel.last_message_id}, parse_depth_hours={channel.parse_depth_hours})")
                    
                    # Получаем entity канала
                    try:
                        entity = await client.get_entity(channel.username_or_id)
                        logger.info(f"Successfully resolved entity: {entity.title}")
                    except Exception as e:
                        logger.error(f"Cannot get entity for {channel.username_or_id}: {e}")
                        # Пробуем по ID если username не работает
                        if channel.username_or_id.startswith('@'):
                            logger.info(f"Trying without @ prefix: {channel.username_or_id[1:]}")
                            try:
                                entity = await client.get_entity(channel.username_or_id[1:])
                                logger.info(f"Successfully resolved entity: {entity.title}")
                            except Exception as e2:
                                logger.error(f"Still cannot get entity: {e2}")
                                continue
                        continue
                    
                    # Получаем последнее проверенное сообщение
                    last_msg_id = channel.last_message_id or 0
                    
                    # Вычисляем дату cutoff на основе parse_depth_hours
                    parse_depth_hours = channel.parse_depth_hours or 168  # default 1 week
                    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=parse_depth_hours)
                    logger.info(f"Using parse depth: {parse_depth_hours} hours, cutoff date: {cutoff_date}")
                    
                    # Soft mode - игнорируем last_msg_id для всех сообщений при начальном парсинге (когда last_message_id was None/0)
                    # Это позволяет загрузить историю при первом запуске или после сброса
                    soft_mode = (channel.last_message_id is None or channel.last_message_id == 0)
                    logger.info(f"Soft mode: {soft_mode} (last_message_id was {channel.last_message_id})")
                    
                    # Получаем новые сообщения (последние 500, но с ограничением по дате)
                    # Итерируемся пока не достигнем cutoff_date
                    new_messages_count = 0
                    async for message in client.iter_messages(entity, limit=500):
                        # В soft mode пропускаем проверку last_msg_id полностью
                        if not soft_mode:
                            # Останавливаемся если достигли последнего проверенного ID
                            if message.id <= last_msg_id:
                                logger.debug(f"Stopping at message {message.id} <= last_msg_id {last_msg_id}")
                                break
                        
                        # Проверка даты
                        msg_date = message.date
                        if msg_date and msg_date.tzinfo is None:
                            msg_date = msg_date.replace(tzinfo=timezone.utc)
                        
                        # В soft mode первые 100 сообщений игнорируют дату (для загрузки недавней истории)
                        if soft_mode and new_messages_count < 100:
                            pass  # Игнорируем дату для первых 100 сообщений
                        elif msg_date and msg_date < cutoff_date:
                            logger.info(f"Message {message.id} dated {msg_date} is older than cutoff ({cutoff_date}), stopping")
                            break
                        
                        if not message.text:
                            continue
                        
                        new_messages_count += 1
                        
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
                        logger.info(f"Message {message.id}: {message.text[:100]}...")
                        
                        # Обновляем last_message_id
                        if last_msg_id == 0 or message.id > last_msg_id:
                            last_msg_id = message.id
                    
                    logger.info(f"Channel {channel.username_or_id}: fetched {new_messages_count} new messages")
                    
                    # Обновляем канал
                    if last_msg_id > 0:
                        channel.last_message_id = last_msg_id
                        channel.last_checked_at = datetime.now(timezone.utc)
                        self.session.add(channel)
                        self.session.commit()
                        logger.info(f"Updated channel {channel.username_or_id} last_message_id to {last_msg_id}")
                    
                except Exception as e:
                    logger.error(f"Error fetching channel {channel.username_or_id}: {e}", exc_info=True)
                    continue
            
            await client.disconnect()
            
            logger.info(f"Total fetched {len(messages_data)} messages from Telegram channels")
            return messages_data
            
        except Exception as e:
            logger.error(f"Error in Telegram fetch: {e}", exc_info=True)
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
