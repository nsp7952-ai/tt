from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import SQLModel
from app.templates import templates
from app.web.routes import (
    dashboard,
    sources,
    filters,
    profile,
    runbooks,
    vacancies,
    applications,
    contacts,
    outreach,
    stats,
    settings as settings_route,
    logs,
)

import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
os.makedirs("data/sessions", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/screenshots", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates are now in app.templates module
# templates = Jinja2Templates(directory="app/web/templates")

# Include routers
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(filters.router, prefix="/filters", tags=["filters"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(runbooks.router, prefix="/runbooks", tags=["runbooks"])
app.include_router(vacancies.router, prefix="/vacancies", tags=["vacancies"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(outreach.router, prefix="/outreach", tags=["outreach"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(settings_route.router, prefix="/settings", tags=["settings"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
