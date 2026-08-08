from sqlmodel import SQLModel, Field, Column
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import JSON


class Source(SQLModel, table=True):
    __tablename__ = "sources"
    
    id: str = Field(primary_key=True)
    name: str
    enabled: bool = True
    use_global_filter: bool = True
    local_filter_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    config_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProfileContext(SQLModel, table=True):
    __tablename__ = "profile_contexts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
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
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlobalFilter(SQLModel, table=True):
    __tablename__ = "global_filters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    enabled: bool = True
    filter_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Vacancy(SQLModel, table=True):
    __tablename__ = "vacancies"
    
    id: str = Field(primary_key=True)
    source: str
    source_id: Optional[str] = None
    url: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    remote: Optional[bool] = None
    grade_hint: Optional[str] = None
    salary_text: Optional[str] = None
    description_text: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = "new"
    match_score: Optional[int] = None
    match_reason: Optional[str] = None
    skip_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Application(SQLModel, table=True):
    __tablename__ = "applications"
    
    id: str = Field(primary_key=True)
    vacancy_id: str = Field(foreign_key="vacancies.id")
    source: str
    status: str = "pending"
    cover_letter: Optional[str] = None
    generated_answers_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    agent_task_id: Optional[str] = None
    external_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"
    
    id: str = Field(primary_key=True)
    source: str
    vacancy_id: Optional[str] = Field(default=None, foreign_key="vacancies.id")
    company: Optional[str] = None
    person_name: Optional[str] = None
    role_hint: Optional[str] = None
    contact_type: str
    value_normalized: str
    value_raw: str
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OutreachMessage(SQLModel, table=True):
    __tablename__ = "outreach_messages"
    
    id: str = Field(primary_key=True)
    contact_id: str = Field(foreign_key="contacts.id")
    channel: str
    subject: Optional[str] = None
    body: str
    cv_attached: bool = False
    status: str = "draft"
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TelegramChannel(SQLModel, table=True):
    __tablename__ = "telegram_channels"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username_or_id: str
    name: Optional[str] = None
    enabled: bool = True
    last_message_id: Optional[int] = None
    last_checked_at: Optional[datetime] = None


class TelegramAccount(SQLModel, table=True):
    __tablename__ = "telegram_accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    session_file: str
    api_id: str
    api_hash: str
    phone: Optional[str] = None
    enabled: bool = True


class AgentTask(SQLModel, table=True):
    __tablename__ = "agent_tasks"
    
    id: str = Field(primary_key=True)
    source: str
    task_type: str
    prompt_text: str
    provider: str
    status: str = "created"
    input_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    result_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EventLog(SQLModel, table=True):
    __tablename__ = "event_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
