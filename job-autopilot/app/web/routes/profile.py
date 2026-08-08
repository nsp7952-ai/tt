from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import ProfileContext

router = APIRouter()


@router.get("/")
async def profile_page(request: Request, session: Session = Depends(get_session)):
    profile = session.exec(select(ProfileContext).limit(1)).first()
    return templates.TemplateResponse("profile.html", {"request": request, "profile": profile})
