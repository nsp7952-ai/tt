from fastapi import APIRouter, Request, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import GlobalFilter

router = APIRouter()


@router.get("/")
async def filters_page(request: Request, session: Session = Depends(get_session)):
    global_filter = session.exec(select(GlobalFilter).limit(1)).first()
    return templates.TemplateResponse("filters.html", {"request": request, "global_filter": global_filter})
