from fastapi import APIRouter, Request
from app.main import templates

router = APIRouter()


@router.get("/")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
