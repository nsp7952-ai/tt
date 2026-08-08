from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from app.models import TelegramAccount, TelegramChannel, Contact, Vacancy, EventLog
from app.services.llm_service import LLMService
from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import Message
import asyncio


class TelegramClientService:
    """Сервис для работы с Telegram через Telethon."""
    
    def __init__(self, session: Session):
        self.session = session
        self.llm_service = LLMService()
        self._clients: Dict[str, TelegramClient] = {}
    
    def get_account(self, name: str) -> Optional[TelegramAccount]:
        """Получить аккаунт по имени."""
        return self.session.get(TelegramAccount, name)
    
    async def get_client(self, account_name: str) -> Optional[TelegramClient]:
        """Получить или создать Telegram клиент для аккаунта."""
        if account_name in self._clients:
            return self._clients[account_name]
        
        account = self.get_account(account_name)
        if not account or not account.enabled:
            logger.warning(f"Telegram account {account_name} not found or disabled")
            return None
        
        # Создаем клиент
        client = TelegramClient(
            account.session_file,
            int(account.api_id),
            account.api_hash
        )
        
        try:
            await client.connect()
            if await client.is_user_authorized():
                self._clients[account_name] = client
                logger.info(f"Telegram client for {account_name} connected")
                return client
            else:
                logger.warning(f"Telegram account {account_name} not authorized")
                await client.disconnect()
                return None
        except Exception as e:
            logger.error(f"Failed to connect Telegram client: {e}")
            return None
    
    async def read_channels(
        self,
        account_name: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Прочитать последние сообщения из включенных каналов."""
        client = await self.get_client(account_name)
        if not client:
            return []
        
        channels = self.session.exec(
            select(TelegramChannel).where(TelegramChannel.enabled == True)
        ).all()
        
        messages = []
        for channel in channels:
            try:
                entity = await client.get_entity(channel.username_or_id)
                
                # Получаем сообщения после last_message_id
                offset_id = channel.last_message_id or 0
                
                async for message in client.iter_messages(
                    entity,
                    limit=limit,
                    offset_id=offset_id,
                    reverse=True
                ):
                    if message.id > (channel.last_message_id or 0):
                        messages.append({
                            "channel": channel.username_or_id,
                            "message_id": message.id,
                            "text": message.text or "",
                            "date": message.date.isoformat() if message.date else None,
                        })
                        
                        # Обновляем last_message_id
                        channel.last_message_id = message.id
                
                self.session.add(channel)
                self.session.commit()
                
            except Exception as e:
                logger.error(f"Error reading channel {channel.username_or_id}: {e}")
        
        return messages
    
    async def send_message(
        self,
        account_name: str,
        recipient: str,
        text: str,
        file_path: Optional[str] = None
    ) -> bool:
        """Отправить сообщение контакту."""
        client = await self.get_client(account_name)
        if not client:
            return False
        
        try:
            entity = await client.get_entity(recipient)
            
            if file_path:
                await client.send_file(entity, file_path, caption=text)
            else:
                await client.send_message(entity, text)
            
            logger.info(f"Message sent to {recipient} via {account_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {recipient}: {e}")
            return False
    
    async def login(self, account_name: str, api_id: str, api_hash: str, phone: str) -> bool:
        """Выполнить вход в Telegram аккаунт."""
        session_file = f"data/sessions/{account_name}.session"
        
        client = TelegramClient(session_file, int(api_id), api_hash)
        await client.connect()
        
        if await client.is_user_authorized():
            logger.info(f"Account {account_name} already authorized")
            await client.disconnect()
            return True
        
        try:
            # Отправляем код подтверждения
            await client.send_code_request(phone)
            logger.info(f"Code sent to {phone}")
            
            # В MVP режиме просим пользователя ввести код вручную
            # В реальном приложении это делается через CLI
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            await client.disconnect()
            return False
    
    def save_account(
        self,
        name: str,
        session_file: str,
        api_id: str,
        api_hash: str,
        phone: Optional[str] = None,
        enabled: bool = True
    ) -> TelegramAccount:
        """Сохранить Telegram аккаунт в базу."""
        existing = self.get_account(name)
        if existing:
            existing.session_file = session_file
            existing.api_id = api_id
            existing.api_hash = api_hash
            existing.phone = phone
            existing.enabled = enabled
            self.session.add(existing)
        else:
            account = TelegramAccount(
                name=name,
                session_file=session_file,
                api_id=api_id,
                api_hash=api_hash,
                phone=phone,
                enabled=enabled
            )
            self.session.add(account)
        
        self.session.commit()
        return self.get_account(name)
