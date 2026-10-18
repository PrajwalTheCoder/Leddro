import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.google_auth import EmailSendAttemptModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.services.gmail_client import send_draft_via_gmail

logger = logging.getLogger("leddro.api.email")
router = APIRouter(prefix="/email", tags=["Email Dispatch & Safeguards"])

class EmailSendRequest(BaseModel):
    draft_id: str = Field(..., description="Target EmailDraft ID")
    recipient_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Exact verified subject line")
    body: str = Field(..., description="Exact verified body text")
    confirmed: bool = Field(..., description="Operator explicit confirmation boolean")

class SuppressionCreateRequest(BaseModel):
    email_or_domain: str = Field(..., description="Email address or domain (e.g. business.com) to suppress")
    reason: Optional[str] = Field("Operator requested opt-out", description="Reason for suppression")

@router.post("/send")
async def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    """
    Sends an individual, explicitly approved email draft using the authenticated Gmail account.
    Validates recipient, checks suppression, verifies explicit confirmation,
    prevents duplicate sends, and records durable send attempts.
    """
    return await send_draft_via_gmail(
        db=db,
        draft_id=payload.draft_id,
        recipient_email=payload.recipient_email,
        subject=payload.subject,
        body=payload.body,
        confirmed=payload.confirmed
    )

@router.get("/send-attempts")
def list_send_attempts(
    draft_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Returns audit trail of durable email send attempts.
    """
    query = db.query(EmailSendAttemptModel)
    if draft_id:
        query = query.filter(EmailSendAttemptModel.draft_id == draft_id)
    if status_filter and status_filter != "all":
        query = query.filter(EmailSendAttemptModel.status == status_filter)

    attempts = query.order_by(EmailSendAttemptModel.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "draft_id": a.draft_id,
            "prospect_id": a.prospect_id,
            "recipient_email": a.recipient_email,
            "sender_email": a.sender_email,
            "subject": a.subject,
            "status": a.status,
            "gmail_message_id": a.gmail_message_id,
            "error_message": a.error_message,
            "error_code": a.error_code,
            "confirmed_at": a.confirmed_at.strftime("%Y-%m-%d %H:%M UTC") if a.confirmed_at else None,
            "completed_at": a.completed_at.strftime("%Y-%m-%d %H:%M UTC") if a.completed_at else None,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M UTC") if a.created_at else None,
        }
        for a in attempts
    ]

@router.get("/send-attempts/{attempt_id}")
def get_send_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.id == attempt_id).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Send attempt with ID '{attempt_id}' not found"
        )
    return {
        "id": attempt.id,
        "draft_id": attempt.draft_id,
        "prospect_id": attempt.prospect_id,
        "recipient_email": attempt.recipient_email,
        "sender_email": attempt.sender_email,
        "subject": attempt.subject,
        "status": attempt.status,
        "gmail_message_id": attempt.gmail_message_id,
        "error_message": attempt.error_message,
        "error_code": attempt.error_code,
        "confirmed_at": attempt.confirmed_at.strftime("%Y-%m-%d %H:%M UTC") if attempt.confirmed_at else None,
        "completed_at": attempt.completed_at.strftime("%Y-%m-%d %H:%M UTC") if attempt.completed_at else None,
        "created_at": attempt.created_at.strftime("%Y-%m-%d %H:%M UTC") if attempt.created_at else None,
    }

@router.get("/history")
def list_email_history(
    prospect_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Returns email dispatch history records from SQLite database.
    """
    query = db.query(EmailHistoryModel)
    if prospect_id:
        query = query.filter(EmailHistoryModel.prospect_id == prospect_id)
    if status_filter and status_filter != "all":
        query = query.filter(EmailHistoryModel.status == status_filter)

    items = query.order_by(EmailHistoryModel.created_at.desc()).all()
    return [
        {
            "id": h.id,
            "recipient": h.recipient,
            "prospectName": h.prospect_name,
            "prospectId": h.prospect_id,
            "subject": h.subject,
            "date": h.date,
            "status": h.status,
            "provider": h.provider,
            "providerMessageId": h.provider_message_id,
            "bodySnippet": h.body_snippet,
            "createdAt": h.created_at.strftime("%Y-%m-%d %H:%M UTC") if h.created_at else None
        }
        for h in items
    ]

@router.get("/suppression")
def list_suppressions(db: Session = Depends(get_db)):
    """
    Returns all active email and domain suppression records.
    """
    records = db.query(SuppressionRecordModel).order_by(SuppressionRecordModel.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "email_or_domain": r.email_or_domain,
            "reason": r.reason,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M UTC") if r.created_at else None
        }
        for r in records
    ]

@router.post("/suppress", status_code=status.HTTP_201_CREATED)
def add_suppression(payload: SuppressionCreateRequest, db: Session = Depends(get_db)):
    """
    Adds an email address or entire domain to the suppression records to prevent future dispatches.
    """
    cleaned = payload.email_or_domain.strip().lower()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or domain string cannot be empty")

    existing = db.query(SuppressionRecordModel).filter(
        SuppressionRecordModel.email_or_domain == cleaned
    ).first()
    if existing:
        return {
            "id": existing.id,
            "email_or_domain": existing.email_or_domain,
            "reason": existing.reason,
            "already_suppressed": True
        }

    rec = SuppressionRecordModel(
        id=f"sup-{uuid.uuid4().hex[:8]}",
        email_or_domain=cleaned,
        reason=payload.reason or "Operator requested opt-out"
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {
        "id": rec.id,
        "email_or_domain": rec.email_or_domain,
        "reason": rec.reason,
        "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M UTC")
    }

@router.delete("/suppress/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/suppression/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suppression(suppression_id: str, db: Session = Depends(get_db)):
    rec = db.query(SuppressionRecordModel).filter(SuppressionRecordModel.id == suppression_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suppression record not found")
    db.delete(rec)
    db.commit()
    return None

