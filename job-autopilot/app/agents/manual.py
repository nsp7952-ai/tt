from typing import Any, Dict, Optional
from sqlmodel import Session, select
from app.agents.base import BrowserAgentProvider, AgentTaskResult
from app.models import AgentTask
from loguru import logger


class ManualAgentProvider(BrowserAgentProvider):
    """
    Ручной провайдер: пользователь копирует prompt в Codex вручную,
    затем вставляет результат обратно в UI.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    async def dispatch(self, task: AgentTask) -> AgentTaskResult:
        """
        Для manual provider задача просто помечается как dispatched
        и ждет результата от пользователя.
        """
        task.status = "dispatched"
        task.provider = "manual"
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        logger.info(f"Manual agent task {task.id} created, waiting for user input")
        
        # Возвращаем пустой результат, так как задача еще не выполнена
        return AgentTaskResult(
            status="queued",
            task_type=task.task_type,
            items=[],
            metrics={"found": 0, "matched": 0, "applied": 0, "skipped": 0, "failed": 0},
            errors=[],
            raw_result=None
        )
    
    async def healthcheck(self) -> bool:
        """Manual provider всегда доступен."""
        return True
    
    def submit_result(self, task_id: str, result_json: Dict[str, Any]) -> AgentTask:
        """Пользователь вставил результат через UI."""
        task = self.session.get(AgentTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.result_json = result_json
        task.status = result_json.get("status", "completed")
        if result_json.get("errors"):
            task.error = "; ".join(result_json.get("errors", []))
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        logger.info(f"Manual agent task {task_id} result submitted")
        return task
