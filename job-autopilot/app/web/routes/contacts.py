from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Contact

router = APIRouter()


@router.get("/")
async def contacts_page(request: Request, session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("contacts.html", {"request": request, "contacts": contacts})
