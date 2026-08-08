from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Application

router = APIRouter()


@router.get("/")
async def applications_page(request: Request, session: Session = Depends(get_session)):
    applications = session.exec(select(Application).order_by(Application.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("applications.html", {"request": request, "applications": applications})
