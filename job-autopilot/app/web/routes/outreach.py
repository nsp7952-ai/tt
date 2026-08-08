from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import OutreachMessage

router = APIRouter()


@router.get("/")
async def outreach_page(request: Request, session: Session = Depends(get_session)):
    messages = session.exec(select(OutreachMessage).order_by(OutreachMessage.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("outreach.html", {"request": request, "messages": messages})
