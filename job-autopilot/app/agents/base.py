from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class AgentTaskResult:
    """Результат выполнения задачи агентом."""
    
    def __init__(
        self,
        status: str,  # success, partial, failed
        task_type: str,
        items: list,
        metrics: Dict[str, int],
        errors: list,
        raw_result: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.task_type = task_type
        self.items = items
        self.metrics = metrics
        self.errors = errors
        self.raw_result = raw_result
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "task_type": self.task_type,
            "items": self.items,
            "metrics": self.metrics,
            "errors": self.errors,
        }


class BrowserAgentProvider(ABC):
    """Абстрактный базовый класс для провайдеров браузерных агентов."""
    
    @abstractmethod
    async def dispatch(self, task: Any) -> AgentTaskResult:
        """Отправить задачу агенту и получить результат."""
        raise NotImplementedError
    
    @abstractmethod
    async def healthcheck(self) -> bool:
        """Проверить доступность агента."""
        raise NotImplementedError
