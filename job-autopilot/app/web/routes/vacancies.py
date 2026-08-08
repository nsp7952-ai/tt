from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Vacancy

router = APIRouter()


@router.get("/")
async def vacancies_page(request: Request, session: Session = Depends(get_session)):
    vacancies = session.exec(select(Vacancy).order_by(Vacancy.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("vacancies.html", {"request": request, "vacancies": vacancies})
