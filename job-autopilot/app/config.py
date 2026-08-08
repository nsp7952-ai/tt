from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Core
    APP_NAME: str = "Job Autopilot"
    DEBUG: bool = True
    DRY_RUN: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/db.sqlite"

    # LLM
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"

    # Telegram
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_CHANNELS_READER_SESSION: Optional[str] = None
    TELEGRAM_OUTREACH_SESSION: Optional[str] = None
    TELEGRAM_ALERTS_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ALERTS_CHAT_ID: Optional[str] = None

    # Scheduler
    VACANCY_FETCH_INTERVAL_MINUTES: int = 30
    TELEGRAM_MONITOR_INTERVAL_MINUTES: int = 5
    SUMMARY_INTERVAL_HOURS: int = 4

    # Browser agent
    BROWSER_AGENT_PROVIDER: str = "manual"  # manual, clipboard, browser_bridge, api

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
