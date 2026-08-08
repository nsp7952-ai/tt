from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from app.database import get_session
from app.models import Vacancy, Application, EventLog, Source
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/summary")
async def get_stats_summary(session: Session = Depends(get_session)):
    """Get summary statistics"""
    # Count vacancies by status
    total_vacancies = session.exec(select(func.count(Vacancy.id))).one()
    new_vacancies = session.exec(select(func.count(Vacancy.id)).where(Vacancy.status == "new")).one()
    viewed_vacancies = session.exec(select(func.count(Vacancy.id)).where(Vacancy.status == "viewed")).one()
    applied_vacancies = session.exec(select(func.count(Vacancy.id)).where(Vacancy.status == "applied")).one()
    
    # Count applications
    total_applications = session.exec(select(func.count(Application.id))).one()
    pending_applications = session.exec(select(func.count(Application.id)).where(Application.status == "pending")).one()
    
    # Count sources
    enabled_sources = session.exec(select(func.count(Source.id)).where(Source.enabled == True)).one()
    
    return {
        "total_vacancies": total_vacancies or 0,
        "new_vacancies": new_vacancies or 0,
        "viewed_vacancies": viewed_vacancies or 0,
        "applied_vacancies": applied_vacancies or 0,
        "total_applications": total_applications or 0,
        "pending_applications": pending_applications or 0,
        "enabled_sources": enabled_sources or 0,
    }


@router.get("/events")
async def get_recent_events(limit: int = 10, session: Session = Depends(get_session)):
    """Get recent event logs"""
    events = session.exec(
        select(EventLog)
        .order_by(EventLog.created_at.desc())
        .limit(limit)
    ).all()
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "message": e.message,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
