from fastapi import APIRouter, Request
from app.main import templates

router = APIRouter()


@router.get("/")
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})
