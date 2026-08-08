from fastapi import APIRouter, Request
from app.main import templates

router = APIRouter()


@router.get("/")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})
