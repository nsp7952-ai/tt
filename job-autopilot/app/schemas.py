from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class SourceBase(BaseModel):
    id: str
    name: str
    enabled: bool = True
    use_global_filter: bool = True
    local_filter_json: Dict = {}
    config_json: Dict = {}


class SourceUpdate(BaseModel):
    enabled: Optional[bool] = None
    use_global_filter: Optional[bool] = None
    local_filter_json: Optional[Dict] = None
    config_json: Optional[Dict] = None


class ProfileContextBase(BaseModel):
    name: str
    markdown_text: str
    cv_file_path: Optional[str] = None
    tone: str = "professional"
    constraints_text: str = ""
    stop_words_text: str = ""
    salary_expectation: Optional[str] = None
    remote_only: bool = True
    min_grade: str = "middle"
    allow_full_stack: bool = True
    full_stack_backend_focus_min: float = 0.6


class GlobalFilterBase(BaseModel):
    enabled: bool = True
    filter_json: Dict = {}


class VacancyBase(BaseModel):
    source: str
    url: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    grade_hint: Optional[str] = None
    salary_text: Optional[str] = None
    description_text: Optional[str] = None


class ApplicationBase(BaseModel):
    vacancy_id: str
    source: str
    cover_letter: Optional[str] = None


class ContactBase(BaseModel):
    source: str
    vacancy_id: Optional[str] = None
    company: Optional[str] = None
    person_name: Optional[str] = None
    role_hint: Optional[str] = None
    contact_type: str
    value_normalized: str
    value_raw: str


class OutreachMessageBase(BaseModel):
    contact_id: str
    channel: str
    subject: Optional[str] = None
    body: str
    cv_attached: bool = False


class TelegramChannelBase(BaseModel):
    username_or_id: str
    name: Optional[str] = None
    enabled: bool = True


class TelegramAccountBase(BaseModel):
    name: str
    session_file: str
    api_id: str
    api_hash: str
    phone: Optional[str] = None
    enabled: bool = True


class AgentTaskBase(BaseModel):
    source: str
    task_type: str
    prompt_text: str
    provider: str
    input_json: Dict = {}


class EventLogBase(BaseModel):
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    message: str
    data: Optional[Dict] = None
