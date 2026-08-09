from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import ProfileContext
from datetime import datetime

router = APIRouter()


@router.get("/")
async def get_profile(session: Session = Depends(get_session)):
    """Get current profile context"""
    profile = session.exec(select(ProfileContext).limit(1)).first()
    if not profile:
        return {}
    return {
        "id": profile.id,
        "name": profile.name,
        "markdown_text": profile.markdown_text,
        "cv_file_path": profile.cv_file_path,
        "tone": profile.tone,
        "constraints_text": profile.constraints_text,
        "stop_words_text": profile.stop_words_text,
        "salary_expectation": profile.salary_expectation,
        "remote_only": profile.remote_only,
        "min_grade": profile.min_grade,
        "allow_full_stack": profile.allow_full_stack,
        "full_stack_backend_focus_min": profile.full_stack_backend_focus_min,
    }


@router.post("/")
async def save_profile(profile_data: dict, session: Session = Depends(get_session)):
    """Save or update profile context"""
    profile = session.exec(select(ProfileContext).limit(1)).first()
    
    if profile:
        # Update existing
        profile.name = profile_data.get("name", profile.name)
        profile.markdown_text = profile_data.get("markdown_text", profile.markdown_text)
        profile.tone = profile_data.get("tone", profile.tone)
        profile.constraints_text = profile_data.get("constraints_text", profile.constraints_text)
        profile.stop_words_text = profile_data.get("stop_words_text", profile.stop_words_text)
        profile.salary_expectation = profile_data.get("salary_expectation", profile.salary_expectation)
        profile.remote_only = profile_data.get("remote_only", profile.remote_only)
        profile.min_grade = profile_data.get("min_grade", profile.min_grade)
        profile.allow_full_stack = profile_data.get("allow_full_stack", profile.allow_full_stack)
        profile.full_stack_backend_focus_min = profile_data.get("full_stack_backend_focus_min", profile.full_stack_backend_focus_min)
        profile.updated_at = datetime.utcnow()
        session.add(profile)
    else:
        # Create new
        profile = ProfileContext(
            name=profile_data.get("name", "Default Profile"),
            markdown_text=profile_data.get("markdown_text", ""),
            tone=profile_data.get("tone", "professional"),
            constraints_text=profile_data.get("constraints_text", ""),
            stop_words_text=profile_data.get("stop_words_text", ""),
            salary_expectation=profile_data.get("salary_expectation"),
            remote_only=profile_data.get("remote_only", True),
            min_grade=profile_data.get("min_grade", "middle"),
            allow_full_stack=profile_data.get("allow_full_stack", True),
            full_stack_backend_focus_min=profile_data.get("full_stack_backend_focus_min", 0.6),
        )
        session.add(profile)
    
    session.commit()
    session.refresh(profile)
    
    return {
        "id": profile.id,
        "name": profile.name,
        "markdown_text": profile.markdown_text,
        "tone": profile.tone,
        "remote_only": profile.remote_only,
        "min_grade": profile.min_grade,
        "allow_full_stack": profile.allow_full_stack,
    }
