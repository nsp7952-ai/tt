from fastapi import APIRouter, Request
from app.main import templates

router = APIRouter()


@router.get("/")
async def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})
