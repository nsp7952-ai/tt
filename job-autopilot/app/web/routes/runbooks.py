from fastapi import APIRouter, Request
from app.main import templates

router = APIRouter()


@router.get("/")
async def runbooks_page(request: Request):
    return templates.TemplateResponse("runbooks.html", {"request": request})
