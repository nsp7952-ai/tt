from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Source
from datetime import datetime

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


@router.post("/{source_id}/fetch")
async def fetch_source(source_id: str, session: Session = Depends(get_session)):
    """Trigger fetch for a specific source"""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # TODO: Trigger actual fetch logic
    return {"status": "fetch_triggered", "source_id": source_id}


@router.post("/fetch-all")
async def fetch_all_sources(session: Session = Depends(get_session)):
    """Trigger fetch for all enabled sources"""
    sources = session.exec(select(Source).where(Source.enabled == True)).all()
    
    # TODO: Trigger actual fetch logic for each source
    return {
        "status": "fetch_triggered",
        "sources_count": len(sources),
        "sources": [s.id for s in sources]
    }
