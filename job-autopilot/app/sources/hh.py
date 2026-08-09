from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import Source, Vacancy, Application, Contact, AgentTask, EventLog
from app.services.llm_service import LLMService
from app.services.filter_service import FilterService
from loguru import logger
import uuid
from datetime import datetime


class HHSource:
    """Источник вакансий HH.ru."""
    
    source_name = "hh"
    
    def __init__(self, session: Session):
        self.session = session
        self.llm_service = LLMService()
        self.filter_service = FilterService(session)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Получить вакансии с HH.ru.
        На MVP это делается через browser agent.
        """
        logger.info("HH source fetch called - requires browser agent")
        return []
    
    async def apply(self, vacancy: Vacancy, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Откликнуться на вакансию через HH.ru.
        На MVP это делается через browser agent.
        """
        logger.info(f"HH source apply called for vacancy {vacancy.id}")
        return {"status": "pending", "message": "Requires browser agent"}
    
    async def collect_stats(self) -> Dict[str, Any]:
        """Собрать статистику по HH.ru."""
        vacancies_count = self.session.exec(
            select(Vacancy).where(Vacancy.source == "hh")
        ).all()
        
        applications_count = self.session.exec(
            select(Application).where(Application.source == "hh")
        ).all()
        
        return {
            "source": "hh",
            "vacancies_found": len(vacancies_count),
            "applications_submitted": len(applications_count),
        }
    
    def create_agent_task(self, task_type: str, prompt: str, input_data: Dict[str, Any]) -> AgentTask:
        """Создать задачу для browser агента."""
        task_id = f"hh_{task_type}_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            id=task_id,
            source="hh",
            task_type=task_type,
            prompt_text=prompt,
            provider="manual",
            status="created",
            input_json=input_data,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
