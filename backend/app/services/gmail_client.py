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

from backend.app.core.config import settings
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
    Strictly rejects header injection attempts containing CR, LF, or null characters.
    Does not silently transform malicious input into valid input.
    """
    if not email_str or not email_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipient email address is available. Add and verify the recipient address before sending."
        )
    if any(c in email_str for c in ("\r", "\n", "\0")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header injection detected: Recipient email must not contain carriage return, newline, or null characters."
        )
    cleaned = email_str.strip()
    if not EMAIL_REGEX.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid recipient email address format: '{cleaned}'"
        )
    return cleaned

def validate_sender_email(email_str: str) -> str:
    """
    Validates sender email address. Strictly rejects header injection containing CR, LF, or null characters.
    """
    if not email_str or not email_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sender email address is available. Configure an authenticated Google account or SMTP sender."
        )
    if any(c in email_str for c in ("\r", "\n", "\0")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header injection detected: Sender email must not contain carriage return, newline, or null characters."
        )
    cleaned = email_str.strip()
    if not EMAIL_REGEX.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sender email address format: '{cleaned}'"
        )
    return cleaned

def validate_subject(subject_str: str) -> str:
    """
    Validates email subject line. Strictly rejects CR, LF, or null characters to prevent header injection.
    Does not silently convert or strip newlines.
    """
    if not subject_str or not subject_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email subject line cannot be empty."
        )
    if any(c in subject_str for c in ("\r", "\n", "\0")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header injection detected: Subject line must not contain carriage return, newline, or null characters."
        )
    return subject_str.strip()

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
    Strictly verifies that header fields contain no CRLF or null characters.
    """
    for field_name, field_val in [("Sender", sender), ("Recipient", recipient), ("Subject", subject)]:
        if any(c in field_val for c in ("\r", "\n", "\0")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Header injection detected: {field_name} must not contain carriage return, newline, or null characters."
            )

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
    Sends an individual, explicitly approved email draft using the authenticated Google account
    or configured Gmail SMTP with Google App Password.
    Enforces duplicate prevention, suppression checks, header injection rejection,
    and durable send attempt auditing. Never claims SMTP acceptance guarantees inbox delivery.
    """
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit operator confirmation is required before dispatching email."
        )

    # 1. Validate Recipient, Subject & Content (Reject Header Injections)
    valid_recipient = validate_recipient_email(recipient_email)
    valid_subject = validate_subject(subject)
    if not body or not body.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email message body cannot be empty.")

    cleaned_body = body.strip()
    body_hash = hashlib.sha256(cleaned_body.encode("utf-8")).hexdigest()

    # 2. Check Suppression List
    check_suppression(valid_recipient, db)

    # 3. Validate Draft
    draft = db.query(EmailDraftModel).filter(EmailDraftModel.id == draft_id).first()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft with ID '{draft_id}' not found."
        )

    # Guard against duplicate sends based on existing attempts and draft status
    active_attempts = db.query(EmailSendAttemptModel).filter(
        EmailSendAttemptModel.draft_id == draft_id
    ).all()

    for att in active_attempts:
        if att.status == "sent":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This draft was already sent on {att.completed_at} (ID: {att.gmail_message_id}). Duplicate sends are blocked."
            )
        if att.status == "sending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A dispatch attempt for this draft is currently in progress."
            )
        if att.status == "uncertain":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A previous send attempt resulted in an uncertain delivery state. Blind retries are blocked to prevent duplicate outreach. Please inspect your email provider's Sent folder before retrying."
            )

    if draft.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This draft was already sent / submitted and cannot be resent. Duplicate sends are blocked."
        )
    if draft.status == "uncertain":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This draft is in an uncertain delivery state from a prior dispatch attempt. Blind retries are blocked to prevent duplicate outreach. Please inspect your email provider's Sent folder."
        )

    # 4. Validate Connected Google Account or SMTP Credentials
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    has_oauth = bool(account and account.is_connected and account.email)
    has_smtp = bool(settings.SMTP_USER.strip() and settings.SMTP_PASSWORD.strip())

    if not has_oauth and not has_smtp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send: No active email dispatcher is configured. Configure a Google App Password (instant) or Google OAuth in Integrations."
        )

    delivery_method = "oauth" if has_oauth else "smtp"
    provider_label = "Gmail API (OAuth 2.0)" if delivery_method == "oauth" else "Gmail SMTP"

    raw_sender = account.email if has_oauth else settings.SMTP_USER.strip()
    valid_sender = validate_sender_email(raw_sender)

    # Pre-fetch prospect info for audit logging
    prospect = None
    if draft.prospect_id:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == draft.prospect_id).first()
    prospect_name = prospect.name if prospect else "Prospect"

    # 7. Create Durable Send Attempt Record
    attempt_id = f"att-{uuid.uuid4().hex[:12]}"
    send_attempt = EmailSendAttemptModel(
        id=attempt_id,
        draft_id=draft_id,
        prospect_id=draft.prospect_id,
        recipient_email=valid_recipient,
        sender_email=valid_sender,
        subject=valid_subject,
        body_hash=body_hash,
        status="sending",
        confirmed_at=datetime.now(timezone.utc),
        dispatched_at=datetime.now(timezone.utc)
    )
    db.add(send_attempt)
    db.commit()

    if delivery_method == "smtp":
        import smtplib
        import socket
        server = None
        try:
            msg = EmailMessage()
            msg["From"] = valid_sender
            msg["To"] = valid_recipient
            msg["Subject"] = valid_subject
            msg.set_content(cleaned_body, charset="utf-8")

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            if settings.SMTP_USE_TLS:
                server.starttls()
            clean_pwd = settings.SMTP_PASSWORD.strip().replace(" ", "")
            server.login(valid_sender, clean_pwd)
            server.send_message(msg)
            try:
                server.quit()
            except Exception:
                pass

            gmail_message_id = f"smtp-{uuid.uuid4().hex[:12]}"
            gmail_thread_id = None
        except smtplib.SMTPAuthenticationError:
            send_attempt.status = "failed"
            send_attempt.error_code = "SMTP_AUTH_ERROR"
            send_attempt.error_message = "Gmail SMTP authentication failed. Please verify your App Password."
            send_attempt.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.warning("Gmail SMTP authentication failed for sender")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail SMTP Authentication failed. Please verify your App Password."
            )
        except smtplib.SMTPConnectError as e:
            send_attempt.status = "failed"
            send_attempt.error_code = "SMTP_CONNECT_ERROR"
            send_attempt.error_message = f"Failed to connect to SMTP server: {type(e).__name__}"
            send_attempt.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"SMTP connect error: {type(e).__name__}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to SMTP server: {type(e).__name__}"
            )
        except (socket.timeout, TimeoutError, smtplib.SMTPServerDisconnected) as e:
            now_utc = datetime.now(timezone.utc)
            logger.error(f"Timeout/disconnect during SMTP send for draft {draft_id}. Setting state to 'uncertain': {type(e).__name__}")
            send_attempt.status = "uncertain"
            send_attempt.error_code = "SMTP_TIMEOUT"
            send_attempt.error_message = (
                "Network timeout or unexpected disconnect during SMTP dispatch. The email may or may not have been accepted by the mail server. "
                "Leddro marked this attempt as UNCERTAIN to prevent duplicate sending. Check your email provider's Sent folder before retrying."
            )
            send_attempt.completed_at = now_utc
            draft.status = "uncertain"

            # Create history record capturing uncertain outcome
            history_item = EmailHistoryModel(
                id=f"hist-{uuid.uuid4().hex[:10]}",
                recipient=valid_recipient,
                prospect_name=prospect_name,
                prospect_id=draft.prospect_id,
                subject=valid_subject,
                date=now_utc.strftime("%Y-%m-%d %H:%M UTC"),
                status="uncertain",
                provider=provider_label,
                provider_message_id=None,
                body_snippet=cleaned_body[:120] + ("..." if len(cleaned_body) > 120 else "")
            )
            db.add(history_item)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=send_attempt.error_message
            )
        except Exception as e:
            send_attempt.status = "failed"
            send_attempt.error_code = "SMTP_ERROR"
            send_attempt.error_message = f"SMTP dispatch error: {type(e).__name__}"
            send_attempt.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"SMTP dispatch error: {type(e).__name__}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to dispatch email via SMTP: {type(e).__name__}"
            )
        finally:
            if server:
                try:
                    server.close()
                except Exception:
                    pass
    else:
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
            sender=valid_sender,
            recipient=valid_recipient,
            subject=valid_subject,
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
            now_utc = datetime.now(timezone.utc)
            logger.error(f"Timeout occurred sending email for draft {draft_id}. Setting state to 'uncertain'.")
            send_attempt.status = "uncertain"
            send_attempt.error_code = "NETWORK_TIMEOUT"
            send_attempt.error_message = (
                "Network timeout during Gmail API dispatch. The email may or may not have been accepted by Gmail. "
                "Leddro marked this attempt as UNCERTAIN to prevent duplicate sending. Check your Gmail Sent folder."
            )
            send_attempt.completed_at = now_utc
            draft.status = "uncertain"

            history_item = EmailHistoryModel(
                id=f"hist-{uuid.uuid4().hex[:10]}",
                recipient=valid_recipient,
                prospect_name=prospect_name,
                prospect_id=draft.prospect_id,
                subject=valid_subject,
                date=now_utc.strftime("%Y-%m-%d %H:%M UTC"),
                status="uncertain",
                provider=provider_label,
                provider_message_id=None,
                body_snippet=cleaned_body[:120] + ("..." if len(cleaned_body) > 120 else "")
            )
            db.add(history_item)
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
    draft.subject = valid_subject
    draft.body = cleaned_body

    # 14. Update Prospect Status if relevant
    if prospect and prospect.status != "contacted":
        prospect.status = "contacted"
        prospect.last_activity = f"Email sent via {provider_label}"

    # 15. Create History Record
    history_item = EmailHistoryModel(
        id=f"hist-{uuid.uuid4().hex[:10]}",
        recipient=valid_recipient,
        prospect_name=prospect_name,
        prospect_id=draft.prospect_id,
        subject=valid_subject,
        date=now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        status="submitted",
        provider=provider_label,
        provider_message_id=gmail_message_id,
        body_snippet=cleaned_body[:120] + ("..." if len(cleaned_body) > 120 else "")
    )
    db.add(history_item)

    db.commit()
    logger.info(f"Successfully submitted individual email via {provider_label}: {valid_recipient} (Message ID: {gmail_message_id})")

    return {
        "success": True,
        "attempt_id": attempt_id,
        "delivery_method": delivery_method,
        "provider": provider_label,
        "gmail_message_id": gmail_message_id,
        "gmail_thread_id": gmail_thread_id,
        "sender": valid_sender,
        "recipient": valid_recipient,
        "status": "submitted",
        "sent_at": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "delivery_note": "Outreach proposal accepted by mail server gateway for transmission."
    }
