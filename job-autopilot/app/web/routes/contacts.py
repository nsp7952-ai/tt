from fastapi import APIRouter, Request, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.main import templates
from app.models import Contact

router = APIRouter()


@router.get("/")
async def contacts_page(request: Request, session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc()).limit(50)).all()
    return templates.TemplateResponse("contacts.html", {"request": request, "contacts": contacts})


@router.delete("/api/{contact_id}")
async def delete_contact(contact_id: str, session: Session = Depends(get_session)):
    """Delete a contact"""
    try:
        contact = session.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        session.delete(contact)
        session.commit()
        return {"success": True, "message": "Contact deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
