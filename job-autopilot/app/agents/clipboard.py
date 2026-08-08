from typing import Any, Dict, Optional
import asyncio
from sqlmodel import Session
from app.agents.base import BrowserAgentProvider, AgentTaskResult
from app.models import AgentTask
from loguru import logger
import pyperclip


class ClipboardBrowserAgentProvider(BrowserAgentProvider):
    """
    Полуручной провайдер: система открывает Codex в браузере,
    копирует prompt в clipboard, пользователь вставляет и запускает.
    """
    
    def __init__(self, session: Session, codex_ui_url: str = ""):
        self.session = session
        self.codex_ui_url = codex_ui_url
    
    async def dispatch(self, task: AgentTask) -> AgentTaskResult:
        """
        Копирует prompt в clipboard и помечает задачу как dispatched.
        """
        # Копируем prompt в clipboard
        try:
            pyperclip.copy(task.prompt_text)
            logger.info(f"Prompt copied to clipboard for task {task.id}")
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")
        
        task.status = "dispatched"
        task.provider = "clipboard"
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        
        logger.info(f"Clipboard agent task {task.id} created")
        
        return AgentTaskResult(
            status="queued",
            task_type=task.task_type,
            items=[],
            metrics={"found": 0, "matched": 0, "applied": 0, "skipped": 0, "failed": 0},
            errors=[],
            raw_result=None
        )
    
    async def healthcheck(self) -> bool:
        """Clipboard provider доступен если есть доступ к clipboard."""
        try:
            pyperclip.paste()
            return True
        except Exception:
            return False
    
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
        
        logger.info(f"Clipboard agent task {task_id} result submitted")
        return task
