from fastapi import APIRouter, Request, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Source

router = APIRouter()


@router.get("/")
async def sources_page(request: Request, session: Session = Depends(get_session)):
    sources = session.exec(select(Source)).all()
    return templates.TemplateResponse("sources.html", {"request": request, "sources": sources})


@router.post("/{source_id}/toggle")
async def toggle_source(source_id: str, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.enabled = not source.enabled
    session.add(source)
    session.commit()
    return {"enabled": source.enabled}
