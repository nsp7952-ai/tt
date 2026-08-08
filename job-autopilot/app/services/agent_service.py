from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.models import AgentTask, EventLog


class AgentService:
    """Сервис для управления браузерными агентами."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_task_id(self) -> str:
        """Сгенерировать ID для задачи агента."""
        return f"task_{uuid.uuid4().hex[:12]}"
    
    def create_task(
        self,
        source: str,
        task_type: str,
        prompt_text: str,
        provider: str = "manual",
        input_json: Optional[Dict[str, Any]] = None
    ) -> AgentTask:
        """Создать новую задачу для агента."""
        task = AgentTask(
            id=self.generate_task_id(),
            source=source,
            task_type=task_type,
            prompt_text=prompt_text,
            provider=provider,
            status="created",
            input_json=input_json or {}
        )
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        self.log_event("agent_task_created", task.id, {
            "source": source,
            "task_type": task_type,
            "provider": provider
        })
        
        return task
    
    def update_status(self, task_id: str, status: str, 
                      result_json: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None) -> AgentTask:
        """Обновить статус задачи."""
        task = self.session.get(AgentTask, task_id)
        if not task:
            raise ValueError(f"AgentTask {task_id} not found")
        
        task.status = status
        if result_json is not None:
            task.result_json = result_json
        if error:
            task.error = error
        task.updated_at = datetime.utcnow()
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        self.log_event("agent_task_status_updated", task.id, {"status": status})
        
        return task
    
    def get_by_id(self, task_id: str) -> Optional[AgentTask]:
        """Получить задачу по ID."""
        return self.session.get(AgentTask, task_id)
    
    def get_all(self, limit: int = 100, status_filter: Optional[str] = None,
                source_filter: Optional[str] = None) -> List[AgentTask]:
        """Получить список задач."""
        query = select(AgentTask).order_by(AgentTask.created_at.desc())
        
        if status_filter:
            query = query.where(AgentTask.status == status_filter)
        if source_filter:
            query = query.where(AgentTask.source == source_filter)
        
        query = query.limit(limit)
        return self.session.exec(query).all()
    
    def get_pending_tasks(self, provider: Optional[str] = None) -> List[AgentTask]:
        """Получить ожидающие задачи."""
        query = select(AgentTask).where(
            (AgentTask.status == "created") | (AgentTask.status == "queued")
        )
        
        if provider:
            query = query.where(AgentTask.provider == provider)
        
        return self.session.exec(query.order_by(AgentTask.created_at)).all()
    
    def log_event(self, event_type: str, entity_id: str, data: Optional[Dict[str, Any]] = None):
        """Записать событие в лог."""
        event = EventLog(
            event_type=event_type,
            entity_type="agent_task",
            entity_id=entity_id,
            message=f"Agent task event: {event_type}",
            data=data or {}
        )
        self.session.add(event)
        self.session.commit()


class ManualAgentProvider:
    """Ручной провайдер для браузного агента - пользователь копирует prompt и вставляет результат."""
    
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service
    
    async def dispatch(self, task: AgentTask) -> AgentTask:
        """Dispatch task - для manual просто меняем статус на dispatched."""
        return self.agent_service.update_status(task.id, "dispatched")
    
    async def healthcheck(self) -> bool:
        """Manual provider всегда доступен."""
        return True
    
    def get_ui_instructions(self, task: AgentTask) -> str:
        """Получить инструкции для UI."""
        return f"""
1. Скопируйте prompt ниже
2. Откройте Codex или другой browser agent
3. Вставьте prompt и выполните задачу
4. Скопируйте результат (JSON)
5. Вернитесь на эту страницу и вставьте результат в поле ниже
"""


class ClipboardBrowserAgentProvider:
    """Провайдер с clipboard интеграцией."""
    
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service
    
    async def dispatch(self, task: AgentTask) -> AgentTask:
        """Dispatch task - копируем prompt в clipboard."""
        import pyperclip
        try:
            pyperclip.copy(task.prompt_text)
            return self.agent_service.update_status(task.id, "dispatched")
        except Exception as e:
            return self.agent_service.update_status(task.id, "failed", error=str(e))
    
    async def healthcheck(self) -> bool:
        """Проверить доступность clipboard."""
        import pyperclip
        try:
            pyperclip.paste()
            return True
        except:
            return False


class BrowserBridgeAgentProvider:
    """Экспериментальный провайдер с Playwright управлением."""
    
    def __init__(self, agent_service: AgentService, browser_profile_path: Optional[str] = None):
        self.agent_service = agent_service
        self.browser_profile_path = browser_profile_path
    
    async def dispatch(self, task: AgentTask) -> AgentTask:
        """Dispatch task через Playwright."""
        # Это экспериментальная функция - требует дополнительной реализации
        return self.agent_service.update_status(task.id, "dispatched")
    
    async def healthcheck(self) -> bool:
        """Проверить доступность браузера."""
        # Требуется реализация проверки
        return False
