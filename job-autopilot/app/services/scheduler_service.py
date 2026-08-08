from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models import EventLog


class SchedulerService:
    """Сервис для управления планировщиком задач."""
    
    def __init__(self, session: Session):
        self.session = session
        self.scheduler = None
        self.jobs_registered = False
    
    def init_scheduler(self):
        """Инициализировать APScheduler."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        self.scheduler = AsyncIOScheduler()
        return self.scheduler
    
    def register_jobs(self):
        """Зарегистрировать все jobs."""
        if self.jobs_registered or not self.scheduler:
            return
        
        from app.config import settings
        
        # Register jobs with intervals from settings
        # Note: Actual job implementations will be added later
        
        self.jobs_registered = True
    
    def start_scheduler(self):
        """Запустить планировщик."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
    
    def stop_scheduler(self):
        """Остановить планировщик."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
    
    def add_job(self, func, trigger: str, **kwargs):
        """Добавить job в планировщик."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        self.scheduler.add_job(func, trigger=trigger, **kwargs)
    
    def log_event(self, event_type: str, entity_id: Optional[str], data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="scheduler",
            entity_id=entity_id,
            message=f"Scheduler event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()
