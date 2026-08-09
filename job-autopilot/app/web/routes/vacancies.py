from fastapi import APIRouter, Request, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Vacancy, Contact
from typing import Optional

router = APIRouter()


@router.get("/")
async def vacancies_page(request: Request, session: Session = Depends(get_session)):
    vacancies = session.exec(select(Vacancy).order_by(Vacancy.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("vacancies.html", {"request": request, "vacancies": vacancies})


@router.delete("/api/{vacancy_id}")
async def delete_vacancy(vacancy_id: str, session: Session = Depends(get_session)):
    """Delete a vacancy and its associated contacts"""
    try:
        vacancy = session.get(Vacancy, vacancy_id)
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        
        # Delete associated contacts first
        contacts = session.exec(select(Contact).where(Contact.vacancy_id == vacancy_id)).all()
        for contact in contacts:
            session.delete(contact)
        
        # Delete the vacancy
        session.delete(vacancy)
        session.commit()
        return {"success": True, "message": "Vacancy deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
