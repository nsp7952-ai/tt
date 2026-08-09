from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import Source, Vacancy, Contact, AgentTask
from app.services.llm_service import LLMService
from app.services.filter_service import FilterService
from loguru import logger
import uuid


class HirifySource:
    """Источник вакансий и контактов Hirify."""
    
    source_name = "hirify"
    
    def __init__(self, session: Session):
        self.session = session
        self.llm_service = LLMService()
        self.filter_service = FilterService(session)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """
        Получить вакансии с Hirify.
        На MVP это делается через browser agent.
        """
        logger.info("Hirify source fetch called - requires browser agent")
        return []
    
    async def extract_contacts(self, vacancy_url: str) -> List[Dict[str, Any]]:
        """
        Извлечь контакты HR из вакансии на Hirify.
        На MVP это делается через browser agent.
        """
        logger.info(f"Hirify extract contacts for {vacancy_url}")
        return []
    
    async def collect_stats(self) -> Dict[str, Any]:
        """Собрать статистику по Hirify."""
        vacancies_count = self.session.exec(
            select(Vacancy).where(Vacancy.source == "hirify")
        ).all()
        
        contacts_count = self.session.exec(
            select(Contact).where(Contact.source == "hirify")
        ).all()
        
        return {
            "source": "hirify",
            "vacancies_found": len(vacancies_count),
            "contacts_found": len(contacts_count),
        }
    
    def create_agent_task(self, task_type: str, prompt: str, input_data: Dict[str, Any]) -> AgentTask:
        """Создать задачу для browser агента."""
        task_id = f"hirify_{task_type}_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            id=task_id,
            source="hirify",
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
