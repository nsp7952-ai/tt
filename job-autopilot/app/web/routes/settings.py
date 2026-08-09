from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.models import Setting, TelegramChannel
from sqlmodel import Session
from app.database import engine
from datetime import datetime
from app.templates import templates

router = APIRouter()


class SettingsRequest(BaseModel):
    # LLM Configuration
    llm_api_key: Optional[str] = None
    llm_api_key_keep_existing: bool = False  # Don't overwrite if True and value is empty
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    
    # Telegram Configuration
    telegram_api_id: Optional[str] = None
    telegram_api_id_keep_existing: bool = False
    telegram_api_hash: Optional[str] = None
    telegram_api_hash_keep_existing: bool = False
    telegram_reader_session: Optional[str] = None
    telegram_reader_session_keep_existing: bool = False
    telegram_outreach_session: Optional[str] = None
    telegram_outreach_session_keep_existing: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_bot_token_keep_existing: bool = False
    telegram_alerts_chat_id: Optional[str] = None
    telegram_alerts_chat_id_keep_existing: bool = False
    
    # Scheduler
    vacancy_fetch_interval_minutes: int = 30
    telegram_monitor_interval_minutes: int = 5
    summary_interval_hours: int = 4
    
    # Browser agent
    browser_agent_provider: str = "manual"


class SettingsResponse(BaseModel):
    # LLM Configuration
    llm_api_key: Optional[str] = None
    llm_api_key_set: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    
    # Telegram Configuration
    telegram_api_id: Optional[str] = None
    telegram_api_id_set: bool = False
    telegram_api_hash: Optional[str] = None
    telegram_api_hash_set: bool = False
    telegram_reader_session: Optional[str] = None
    telegram_reader_session_set: bool = False
    telegram_outreach_session: Optional[str] = None
    telegram_outreach_session_set: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_bot_token_set: bool = False
    telegram_alerts_chat_id: Optional[str] = None
    telegram_alerts_chat_id_set: bool = False
    
    # Scheduler
    vacancy_fetch_interval_minutes: int = 30
    telegram_monitor_interval_minutes: int = 5
    summary_interval_hours: int = 4
    
    # Browser agent
    browser_agent_provider: str = "manual"
    
    # Telegram Channels
    telegram_channels: List[Dict[str, Any]] = []


def get_setting(key: str, default: str = "") -> str:
    """Get setting value from database"""
    with Session(engine) as session:
        setting = session.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else default


def save_setting(key: str, value: str, is_secret: bool = False):
    """Save setting to database"""
    with Session(engine) as session:
        setting = session.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
            setting.is_secret = is_secret
            setting.updated_at = datetime.utcnow()
        else:
            setting = Setting(key=key, value=value, is_secret=is_secret)
            session.add(setting)
        session.commit()


@router.get("/")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


@router.get("/api/data")
async def get_settings():
    """Get all settings"""
    channels = []
    with Session(engine) as session:
        db_channels = session.query(TelegramChannel).all()
        channels = [{"id": ch.id, "username_or_id": ch.username_or_id, "name": ch.name or "", "enabled": ch.enabled} for ch in db_channels]
    
    return SettingsResponse(
        llm_api_key=None,
        llm_api_key_set=get_setting("LLM_API_KEY", "") != "",
        llm_base_url=get_setting("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_model=get_setting("LLM_MODEL", "gpt-4o"),
        
        telegram_api_id=None,
        telegram_api_id_set=get_setting("TELEGRAM_API_ID", "") != "",
        telegram_api_hash=None,
        telegram_api_hash_set=get_setting("TELEGRAM_API_HASH", "") != "",
        telegram_reader_session=None,
        telegram_reader_session_set=get_setting("TELEGRAM_READER_SESSION", "") != "",
        telegram_outreach_session=None,
        telegram_outreach_session_set=get_setting("TELEGRAM_OUTREACH_SESSION", "") != "",
        telegram_bot_token=None,
        telegram_bot_token_set=get_setting("TELEGRAM_BOT_TOKEN", "") != "",
        telegram_alerts_chat_id=None,
        telegram_alerts_chat_id_set=get_setting("TELEGRAM_ALERTS_CHAT_ID", "") != "",
        
        vacancy_fetch_interval_minutes=int(get_setting("VACANCY_FETCH_INTERVAL_MINUTES", "30")),
        telegram_monitor_interval_minutes=int(get_setting("TELEGRAM_MONITOR_INTERVAL_MINUTES", "5")),
        summary_interval_hours=int(get_setting("SUMMARY_INTERVAL_HOURS", "4")),
        
        browser_agent_provider=get_setting("BROWSER_AGENT_PROVIDER", "manual"),
        telegram_channels=channels
    )


@router.post("/api/save")
async def save_settings(data: SettingsRequest):
    """Save all settings"""
    try:
        # Save LLM settings
        if data.llm_api_key and not data.llm_api_key_keep_existing:
            save_setting("LLM_API_KEY", data.llm_api_key, is_secret=True)
        elif data.llm_api_key_keep_existing and get_setting("LLM_API_KEY", "") == "":
            # If keep_existing is True but no existing value, save anyway if new value provided
            if data.llm_api_key:
                save_setting("LLM_API_KEY", data.llm_api_key, is_secret=True)
        save_setting("LLM_BASE_URL", data.llm_base_url)
        save_setting("LLM_MODEL", data.llm_model)
        
        # Save Telegram settings - only update if new value provided or no existing value
        if data.telegram_api_id and not data.telegram_api_id_keep_existing:
            save_setting("TELEGRAM_API_ID", data.telegram_api_id, is_secret=True)
        if data.telegram_api_hash and not data.telegram_api_hash_keep_existing:
            save_setting("TELEGRAM_API_HASH", data.telegram_api_hash, is_secret=True)
        if data.telegram_reader_session and not data.telegram_reader_session_keep_existing:
            save_setting("TELEGRAM_READER_SESSION", data.telegram_reader_session, is_secret=True)
        if data.telegram_outreach_session and not data.telegram_outreach_session_keep_existing:
            save_setting("TELEGRAM_OUTREACH_SESSION", data.telegram_outreach_session, is_secret=True)
        if data.telegram_bot_token and not data.telegram_bot_token_keep_existing:
            save_setting("TELEGRAM_BOT_TOKEN", data.telegram_bot_token, is_secret=True)
        if data.telegram_alerts_chat_id and not data.telegram_alerts_chat_id_keep_existing:
            save_setting("TELEGRAM_ALERTS_CHAT_ID", data.telegram_alerts_chat_id, is_secret=True)
        
        # Save Scheduler settings
        save_setting("VACANCY_FETCH_INTERVAL_MINUTES", str(data.vacancy_fetch_interval_minutes))
        save_setting("TELEGRAM_MONITOR_INTERVAL_MINUTES", str(data.telegram_monitor_interval_minutes))
        save_setting("SUMMARY_INTERVAL_HOURS", str(data.summary_interval_hours))
        
        # Save Browser agent settings
        save_setting("BROWSER_AGENT_PROVIDER", data.browser_agent_provider)
        
        return {"success": True, "message": "Settings saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/channels/add")
async def add_channel(username_or_id: str, name: Optional[str] = None):
    """Add a new Telegram channel"""
    try:
        with Session(engine) as session:
            channel = TelegramChannel(username_or_id=username_or_id, name=name or username_or_id)
            session.add(channel)
            session.commit()
            return {"success": True, "message": "Channel added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/channels/{channel_id}/toggle")
async def toggle_channel(channel_id: int):
    """Toggle channel enabled status"""
    try:
        with Session(engine) as session:
            channel = session.query(TelegramChannel).filter(TelegramChannel.id == channel_id).first()
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")
            channel.enabled = not channel.enabled
            session.commit()
            return {"success": True, "enabled": channel.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: int):
    """Delete a Telegram channel"""
    try:
        with Session(engine) as session:
            channel = session.query(TelegramChannel).filter(TelegramChannel.id == channel_id).first()
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")
            session.delete(channel)
            session.commit()
            return {"success": True, "message": "Channel deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
