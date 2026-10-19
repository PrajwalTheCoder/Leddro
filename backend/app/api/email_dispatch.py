import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.google_auth import EmailSendAttemptModel, GoogleAccountModel
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

class SMTPTestRequest(BaseModel):
    user: Optional[str] = None
    password: Optional[str] = None

@router.get("/status")
def get_email_dispatch_status(db: Session = Depends(get_db)):
    """
    Returns the active email dispatch configuration status (OAuth, SMTP, or none).
    Acts as the backend source of truth for safe provider selection.
    """
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    has_oauth = bool(account and account.is_connected and account.email)
    has_smtp = bool(settings.SMTP_USER.strip() and settings.SMTP_PASSWORD.strip())

    method = "oauth" if has_oauth else ("smtp" if has_smtp else "none")
    provider_name = "Gmail API (OAuth 2.0)" if has_oauth else ("Gmail SMTP" if has_smtp else "None")
    sender_email = account.email if has_oauth else (settings.SMTP_USER.strip() if has_smtp else None)

    return {
        "is_ready": has_oauth or has_smtp,
        "method": method,
        "provider_name": provider_name,
        "sender_email": sender_email,
        "smtp_configured": has_smtp,
        "oauth_configured": has_oauth,
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT
    }

@router.post("/test-smtp")
def test_smtp_connection(payload: SMTPTestRequest = SMTPTestRequest()):
    """
    Tests Gmail SMTP connection using configured or provided App Password.
    Never exposes credentials or raw auth errors in responses or logs.
    """
    import smtplib
    user = (payload.user if payload.user is not None else settings.SMTP_USER).strip()
    pwd = (payload.password if payload.password is not None else settings.SMTP_PASSWORD).strip().replace(" ", "")

    if not user or not pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both SMTP_USER and SMTP_PASSWORD are required to test connection."
        )

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(user, pwd)
        server.quit()
        return {
            "success": True,
            "message": f"Successfully authenticated with Gmail SMTP gateway as {user}!",
            "user": user
        }
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail SMTP Authentication failed. Ensure your 16-character Google App Password is correct."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SMTP Connection error: {type(e).__name__}"
        )

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
    try:
        db.commit()
        db.refresh(rec)
    except Exception:
        db.rollback()
        raise

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
    try:
        db.delete(rec)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return None

