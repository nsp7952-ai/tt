from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import GlobalFilter
from datetime import datetime
from typing import Optional, Dict, Any

router = APIRouter()


@router.get("/global")
async def get_global_filter(session: Session = Depends(get_session)):
    """Get global filter configuration"""
    gf = session.exec(select(GlobalFilter).limit(1)).first()
    if not gf:
        return {"enabled": True, "filter_json": {}}
    return {
        "id": gf.id,
        "enabled": gf.enabled,
        "filter_json": gf.filter_json or {},
    }


@router.post("/global")
async def save_global_filter(filter_data: dict, session: Session = Depends(get_session)):
    """Save or update global filter"""
    gf = session.exec(select(GlobalFilter).limit(1)).first()
    
    if gf:
        # Update existing
        gf.enabled = filter_data.get("enabled", gf.enabled)
        gf.filter_json = filter_data.get("filter_json", gf.filter_json)
        gf.updated_at = datetime.utcnow()
        session.add(gf)
    else:
        # Create new
        gf = GlobalFilter(
            enabled=filter_data.get("enabled", True),
            filter_json=filter_data.get("filter_json", {}),
        )
        session.add(gf)
    
    session.commit()
    session.refresh(gf)
    
    return {
        "id": gf.id,
        "enabled": gf.enabled,
        "filter_json": gf.filter_json,
    }
