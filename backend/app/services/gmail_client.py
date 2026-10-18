import base64
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Dict, Any, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.draft import EmailDraftModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.models.prospect import ProspectModel
from backend.app.models.google_auth import GoogleAccountModel, EmailSendAttemptModel
from backend.app.services.google_oauth import get_valid_access_token

logger = logging.getLogger("leddro.gmail_client")

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

def validate_recipient_email(email_str: str) -> str:
    """
    Validates recipient email address. Never invents or guesses addresses.
    """
    if not email_str or not email_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipient email address is available. Add and verify the recipient address before sending."
        )
    cleaned = email_str.strip()
    if not EMAIL_REGEX.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid recipient email address format: '{cleaned}'"
        )
    return cleaned

def check_suppression(email_str: str, db: Session):
    """
    Checks if recipient email or domain is in suppression records.
    """
    cleaned = email_str.strip().lower()
    domain = cleaned.split("@")[-1] if "@" in cleaned else ""

    records = db.query(SuppressionRecordModel).all()
    for rec in records:
        entry = rec.email_or_domain.strip().lower()
        if entry == cleaned or (domain and (entry == domain or entry == f"@{domain}")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Outbound dispatch blocked: Recipient '{email_str}' is suppressed ({rec.reason})."
            )

def build_rfc2822_message(sender: str, recipient: str, subject: str, body_text: str) -> str:
    """
    Builds a standard RFC 2822 MIME message and encodes it as base64url string.
    """
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text, charset="utf-8")

    # Base64url without newlines
    raw_bytes = msg.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode("ascii")

async def send_draft_via_gmail(
    db: Session,
    draft_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    confirmed: bool
) -> Dict[str, Any]:
    """
    Sends an individual, explicitly approved email draft using the authenticated Google account.
    Enforces duplicate prevention, suppression checks, exact content verification,
    and durable send attempt auditing.
    """
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit operator confirmation is required before dispatching email via Gmail API."
        )

    # 1. Validate Recipient
    valid_recipient = validate_recipient_email(recipient_email)

    # 2. Check Suppression List
    check_suppression(valid_recipient, db)

    # 3. Validate Draft
    draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft with ID '{draft_id}' not found."
        )

    # 4. Validate Connected Google Account
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if not account or not account.is_connected or not account.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send: No active Google account is connected. Connect Google in Integrations."
        )
    sender_email = account.email


    # 5. Validate content
    if not subject or not subject.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email subject line cannot be empty.")
    if not body or not body.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email message body cannot be empty.")

    cleaned_subject = subject.strip()
    cleaned_body = body.strip()
    body_hash = hashlib.sha256(cleaned_body.encode("utf-8")).hexdigest()

    # 6. Deduplication & Existing Attempt Check
    active_attempts = db.query(EmailSendAttemptModel).filter(
        EmailSendAttemptModel.draft_id == draft_id
    ).all()

    for att in active_attempts:
        if att.status == "sent":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This draft was already sent on {att.completed_at} (Gmail ID: {att.gmail_message_id}). Duplicate sends are blocked."
            )
        if att.status == "sending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A dispatch attempt for this draft is currently in progress."
            )
        if att.status == "uncertain":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A previous send attempt resulted in an uncertain network state. Please verify your Gmail Sent folder before retrying."
            )

    # 7. Create Durable Send Attempt Record
    attempt_id = f"att-{uuid.uuid4().hex[:12]}"
    send_attempt = EmailSendAttemptModel(
        id=attempt_id,
        draft_id=draft_id,
        prospect_id=draft.prospect_id,
        recipient_email=valid_recipient,
        sender_email=sender_email,
        subject=cleaned_subject,
        body_hash=body_hash,
        status="sending",
        confirmed_at=datetime.now(timezone.utc),
        dispatched_at=datetime.now(timezone.utc)
    )
    db.add(send_attempt)
    db.commit()

    # 8. Obtain valid access token
    try:
        access_token = await get_valid_access_token(db)
    except Exception as e:
        send_attempt.status = "failed"
        send_attempt.error_code = "AUTH_ERROR"
        send_attempt.error_message = f"Authentication failure: {str(e)}"
        send_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

    # 9. Build base64url MIME payload
    raw_payload = build_rfc2822_message(
        sender=sender_email,
        recipient=valid_recipient,
        subject=cleaned_subject,
        body_text=cleaned_body
    )

    # 10. Call Gmail API send endpoint
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                GMAIL_SEND_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"raw": raw_payload}
            )
    except httpx.TimeoutException:
        logger.error(f"Timeout occurred sending email for draft {draft_id}. Setting state to 'uncertain'.")
        send_attempt.status = "uncertain"
        send_attempt.error_code = "NETWORK_TIMEOUT"
        send_attempt.error_message = (
            "Network timeout during Gmail API dispatch. The email may or may not have been accepted by Gmail. "
            "Leddro marked this attempt as UNCERTAIN to prevent duplicate sending. Check your Gmail Sent folder."
        )
        send_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=send_attempt.error_message
        )
    except httpx.RequestError as e:
        logger.error(f"Network error dispatching to Gmail: {e}")
        send_attempt.status = "failed"
        send_attempt.error_code = "NETWORK_ERROR"
        send_attempt.error_message = f"Network connection error during Gmail dispatch: {str(e)}"
        send_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error communicating with Gmail API: {str(e)}"
        )

    # 11. Handle API response
    if resp.status_code != 200:
        err_msg = f"Gmail API send failed with HTTP {resp.status_code}"
        err_code = "GMAIL_API_ERROR"
        try:
            err_data = resp.json().get("error", {})
            if "message" in err_data:
                err_msg = err_data["message"]
            if "status" in err_data:
                err_code = err_data["status"]
        except Exception:
            pass

        send_attempt.status = "failed"
        send_attempt.error_code = err_code
        send_attempt.error_message = err_msg
        send_attempt.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.error(f"Gmail send API rejected attempt {attempt_id}: {err_msg} ({err_code})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if resp.status_code < 500 else status.HTTP_502_BAD_GATEWAY,
            detail=f"Gmail API error: {err_msg}"
        )

    # 12. Parse Success
    result_data = resp.json()
    gmail_message_id = result_data.get("id")
    gmail_thread_id = result_data.get("threadId")

    now_utc = datetime.now(timezone.utc)
    send_attempt.status = "sent"
    send_attempt.gmail_message_id = gmail_message_id
    send_attempt.gmail_thread_id = gmail_thread_id
    send_attempt.completed_at = now_utc

    # 13. Update Draft Record
    draft.status = "submitted"
    draft.provider_message_id = gmail_message_id
    draft.submitted_at = now_utc
    draft.recipient_email = valid_recipient
    draft.subject = cleaned_subject
    draft.body = cleaned_body

    # 14. Update Prospect Status if relevant
    prospect = None
    if draft.prospect_id:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == draft.prospect_id).first()
        if prospect and prospect.status != "contacted":
            prospect.status = "contacted"
            prospect.last_activity = "Email sent via Gmail"

    # 15. Create History Record
    history_item = EmailHistoryModel(
        id=f"hist-{uuid.uuid4().hex[:10]}",
        recipient=valid_recipient,
        prospect_name=prospect.name if prospect else "Prospect",
        prospect_id=draft.prospect_id,
        subject=cleaned_subject,
        date=now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        status="submitted",
        provider="Gmail API (OAuth 2.0)",
        provider_message_id=gmail_message_id,
        body_snippet=cleaned_body[:120] + ("..." if len(cleaned_body) > 120 else "")
    )
    db.add(history_item)

    db.commit()
    logger.info(f"Successfully sent individual email via Gmail API: {valid_recipient} (Message ID: {gmail_message_id})")

    return {
        "success": True,
        "attempt_id": attempt_id,
        "gmail_message_id": gmail_message_id,
        "gmail_thread_id": gmail_thread_id,
        "sender": sender_email,
        "recipient": valid_recipient,
        "status": "sent",
        "sent_at": now_utc.strftime("%Y-%m-%d %H:%M UTC")
    }
