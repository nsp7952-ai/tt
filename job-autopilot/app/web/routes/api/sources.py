from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Source, EventLog
from datetime import datetime
from loguru import logger

router = APIRouter()


@router.get("/")
async def get_sources(session: Session = Depends(get_session)):
    """Get all sources"""
    sources = session.exec(select(Source)).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "enabled": s.enabled,
            "use_global_filter": s.use_global_filter,
            "local_filter_json": s.local_filter_json,
            "config_json": s.config_json,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in sources
    ]


@router.post("/{source_id}/toggle")
async def toggle_source(source_id: str, session: Session = Depends(get_session)):
    """Toggle source enabled status"""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    source.enabled = not source.enabled
    source.updated_at = datetime.utcnow()
    session.add(source)
    session.commit()
    
    return {"enabled": source.enabled}


@router.post("/fetch")
async def fetch_source(source_id: str = None, session: Session = Depends(get_session)):
    """Trigger fetch for a specific source or all enabled sources"""
    from app.services.vacancy_service import VacancyService
    from app.sources.telegram_channels import TelegramChannelsSource
    from app.sources.hh import HHSource
    from app.sources.hirify import HirifySource
    
    try:
        if source_id:
            # Fetch specific source
            source = session.get(Source, source_id)
            if not source:
                raise HTTPException(status_code=404, detail="Source not found")
            
            if not source.enabled:
                return {"status": "error", "message": f"Source {source_id} is disabled"}
            
            await _fetch_source_by_id(source_id, session)
            return {"status": "success", "message": f"Fetch triggered for {source_id}"}
        else:
            # Fetch all enabled sources
            sources = session.exec(select(Source).where(Source.enabled == True)).all()
            results = []
            for source in sources:
                try:
                    await _fetch_source_by_id(source.id, session)
                    results.append({"source_id": source.id, "status": "success"})
                except Exception as e:
                    logger.error(f"Error fetching {source.id}: {e}")
                    results.append({"source_id": source.id, "status": "error", "message": str(e)})
            
            return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error in fetch_source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_source_by_id(source_id: str, session: Session):
    """Helper to fetch a specific source by ID"""
    from app.services.vacancy_service import VacancyService
    from app.sources.telegram_channels import TelegramChannelsSource
    from app.sources.hh import HHSource
    from app.sources.hirify import HirifySource
    from app.services.llm_service import LLMService
    
    vacancy_service = VacancyService(session)
    llm_service = LLMService()
    
    if source_id == "telegram_channels":
        # Fetch Telegram channels
        tg_source = TelegramChannelsSource(session)
        messages = await tg_source.fetch()
        
        if messages:
            stats = await vacancy_service.process_telegram_vacancies(messages, llm_service)
            logger.info(f"Telegram fetch stats: {stats}")
            
            # Log event
            event = EventLog(
                event_type="vacancy_fetch",
                entity_type="source",
                entity_id=source_id,
                message=f"Fetched {stats.get('vacancies_created', 0)} vacancies from Telegram",
                data=stats
            )
            session.add(event)
            session.commit()
    
    elif source_id == "hh":
        # Fetch HeadHunter
        hh_source = HHSource(session)
        vacancies = await hh_source.fetch()
        
        if vacancies:
            for vac_data in vacancies:
                vacancy_service.create_or_update(
                    source="hh",
                    url=vac_data.get("url", ""),
                    title=vac_data.get("title", "Unknown"),
                    company=vac_data.get("company"),
                    location=vac_data.get("location"),
                    salary_text=vac_data.get("salary"),
                    description_text=vac_data.get("description"),
                    raw_json=vac_data,
                    status="new"
                )
            
            # Log event
            event = EventLog(
                event_type="vacancy_fetch",
                entity_type="source",
                entity_id=source_id,
                message=f"Fetched {len(vacancies)} vacancies from HH",
                data={"count": len(vacancies)}
            )
            session.add(event)
            session.commit()
    
    elif source_id == "hirify":
        # Fetch Hirify
        hirify_source = HirifySource(session)
        vacancies = await hirify_source.fetch()
        
        if vacancies:
            for vac_data in vacancies:
                vacancy_service.create_or_update(
                    source="hirify",
                    url=vac_data.get("url", ""),
                    title=vac_data.get("title", "Unknown"),
                    company=vac_data.get("company"),
                    location=vac_data.get("location"),
                    salary_text=vac_data.get("salary"),
                    description_text=vac_data.get("description"),
                    raw_json=vac_data,
                    status="new"
                )
            
            # Log event
            event = EventLog(
                event_type="vacancy_fetch",
                entity_type="source",
                entity_id=source_id,
                message=f"Fetched {len(vacancies)} vacancies from Hirify",
                data={"count": len(vacancies)}
            )
            session.add(event)
            session.commit()


@router.post("/fetch-all")
async def fetch_all_sources(session: Session = Depends(get_session)):
    """Trigger fetch for all enabled sources"""
    return await fetch_source(source_id=None, session=session)
