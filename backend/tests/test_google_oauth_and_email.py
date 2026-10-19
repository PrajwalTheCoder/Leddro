import json
import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest
import httpx
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import encrypt_credential, decrypt_credential, redact_sensitive
from backend.app.models.draft import EmailDraftModel
from backend.app.models.google_auth import GoogleAccountModel, OAuthStateModel, EmailSendAttemptModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.models.prospect import ProspectModel

# ----------------- Security and Encryption Tests -----------------

def test_credential_encryption_and_decryption():
    secret_token = "ya29.a0AfH6SMD_test_access_token_12345"
    encrypted = encrypt_credential(secret_token)
    assert encrypted is not None
    assert encrypted != secret_token
    assert "ya29" not in encrypted

    decrypted = decrypt_credential(encrypted)
    assert decrypted == secret_token

def test_credential_redaction():
    token = "ya29.a0AfH6SMD_test_token"
    redacted = redact_sensitive(token)
    assert redacted.startswith("ya29")
    assert redacted.endswith("oken")
    assert "H6SMD" not in redacted
    assert redact_sensitive("") == "[REDACTED]"
    assert redact_sensitive("short") == "[REDACTED]"

# ----------------- Google Status & Missing Config Tests -----------------

def test_google_status_when_not_configured(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")

    resp = client.get("/api/google/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_configured"] is False
    assert "GOOGLE_CLIENT_ID" in data["missing_config"]
    assert "GOOGLE_CLIENT_SECRET" in data["missing_config"]
    assert data["is_connected"] is False
    assert data["email"] is None

def test_google_connect_fails_when_unconfigured(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    resp = client.get("/api/google/connect")
    assert resp.status_code == 400
    assert "Google OAuth credentials missing" in resp.json()["detail"]

# ----------------- OAuth State & Authorization Flow Tests -----------------

def test_google_connect_generates_valid_oauth_url(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/google/callback")

    resp = client.get("/api/google/connect")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "state" in data

    auth_url = data["authorization_url"]
    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "test-client-id.apps.googleusercontent.com" in auth_url
    assert "access_type=offline" in auth_url
    assert "code_challenge=" in auth_url
    assert "code_challenge_method=S256" in auth_url

    # Check state was stored in DB
    state_rec = db_session.query(OAuthStateModel).filter(OAuthStateModel.state == data["state"]).first()
    assert state_rec is not None
    assert state_rec.code_verifier is not None
    exp_utc = state_rec.expires_at if state_rec.expires_at.tzinfo else state_rec.expires_at.replace(tzinfo=timezone.utc)
    assert exp_utc > datetime.now(timezone.utc)

def test_oauth_callback_invalid_state_rejected(client: TestClient, db_session):
    resp = client.get("/api/google/callback?code=mock_code&state=non_existent_state", follow_redirects=False)
    assert resp.status_code == 302
    assert "google_error=" in resp.headers["location"]
    assert "Invalid%20or%20expired%20OAuth%20state" in resp.headers["location"]

def test_oauth_callback_expired_state_rejected(client: TestClient, db_session):
    expired_state = OAuthStateModel(
        state="expired_state_123",
        code_verifier="test_verifier",
        redirect_uri="http://localhost:8000/api/google/callback",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db_session.add(expired_state)
    db_session.commit()

    resp = client.get("/api/google/callback?code=mock_code&state=expired_state_123", follow_redirects=False)
    assert resp.status_code == 302
    assert "google_error=" in resp.headers["location"]

def test_oauth_callback_error_query_param(client: TestClient):
    resp = client.get("/api/google/callback?error=access_denied&error_description=User%20denied%20consent", follow_redirects=False)
    assert resp.status_code == 302
    assert "google_error=" in resp.headers["location"]
    assert "User%20denied%20consent" in resp.headers["location"]

# ----------------- Mocked Successful OAuth Callback -----------------

@pytest.mark.asyncio
async def test_successful_oauth_callback_stores_real_email_and_encrypted_tokens(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/google/callback")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:5173")

    # Prepare active OAuth state
    state_rec = OAuthStateModel(
        state="valid_mock_state_456",
        code_verifier="mock_code_verifier_abc",
        redirect_uri="http://localhost:8000/api/google/callback",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db_session.add(state_rec)
    db_session.commit()

    # Mock Google Token and Userinfo responses
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "ya29.test_real_access_token",
        "refresh_token": "1//test_real_refresh_token",
        "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/userinfo.email openid"
    }

    mock_userinfo_resp = MagicMock()
    mock_userinfo_resp.status_code = 200
    mock_userinfo_resp.json.return_value = {
        "id": "google_sub_987654321",
        "email": "verified.operator@example.com",
        "verified_email": True
    }

    async def mock_post(url, *args, **kwargs):
        if "oauth2.googleapis.com/token" in str(url):
            return mock_token_resp
        return MagicMock(status_code=404)

    async def mock_get(url, *args, **kwargs):
        if "oauth2/v2/userinfo" in str(url):
            return mock_userinfo_resp
        return MagicMock(status_code=404)

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("httpx.AsyncClient.get", side_effect=mock_get):
        resp = client.get("/api/google/callback?code=google_auth_code_xyz&state=valid_mock_state_456", follow_redirects=False)

    assert resp.status_code == 302
    assert "google_connected=true" in resp.headers["location"]
    assert "verified.operator%40example.com" in resp.headers["location"]

    # Verify Account in DB
    account = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    assert account is not None
    assert account.email == "verified.operator@example.com"
    assert account.is_connected is True
    # Tokens must not be in plaintext
    assert account.encrypted_access_token != "ya29.test_real_access_token"
    assert decrypt_credential(account.encrypted_access_token) == "ya29.test_real_access_token"
    assert decrypt_credential(account.encrypted_refresh_token) == "1//test_real_refresh_token"

    # Status endpoint must display email and NEVER leak tokens
    status_resp = client.get("/api/google/status")
    status_data = status_resp.json()
    assert status_data["is_connected"] is True
    assert status_data["email"] == "verified.operator@example.com"
    assert "access_token" not in status_data
    assert "refresh_token" not in status_data
    assert "client_secret" not in status_data

# ----------------- Connection Test & Disconnect Tests -----------------

def test_google_test_connection(client: TestClient, db_session):
    acc = GoogleAccountModel(
        id="default",
        email="test.operator@example.com",
        encrypted_access_token=encrypt_credential("valid_token"),
        encrypted_refresh_token=encrypt_credential("valid_refresh"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True
    )
    db_session.add(acc)
    db_session.commit()

    mock_profile_resp = MagicMock()
    mock_profile_resp.status_code = 200
    mock_profile_resp.json.return_value = {
        "emailAddress": "test.operator@example.com",
        "messagesTotal": 1420,
        "threadsTotal": 890,
        "historyId": "998877"
    }

    async def mock_profile_get(url, *args, **kwargs):
        if "users/me/profile" in str(url):
            return mock_profile_resp
        return MagicMock(status_code=404)

    with patch("httpx.AsyncClient.get", side_effect=mock_profile_get):
        resp = client.post("/api/google/test-connection")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["email"] == "test.operator@example.com"
    assert data["messages_total"] == 1420

def test_google_disconnect_removes_account(client: TestClient, db_session):
    acc = GoogleAccountModel(
        id="default",
        email="disconnect.test@example.com",
        encrypted_access_token=encrypt_credential("tok"),
        encrypted_refresh_token=encrypt_credential("ref"),
        is_connected=True
    )
    db_session.add(acc)
    db_session.commit()

    mock_revoke_resp = MagicMock()
    mock_revoke_resp.status_code = 200

    async def mock_revoke(url, *args, **kwargs):
        return mock_revoke_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_revoke):
        resp = client.post("/api/google/disconnect")

    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify account deleted
    remaining = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    assert remaining is None

    # Check status endpoint confirms disconnected
    status_resp = client.get("/api/google/status")
    assert status_resp.json()["is_connected"] is False

# ----------------- Email Dispatch & Anti-Spam Tests -----------------

def _create_seed_prospect(db_session, prospect_id="pr-test-base"):
    existing = db_session.query(ProspectModel).filter(ProspectModel.id == prospect_id).first()
    if not existing:
        p = ProspectModel(
            id=prospect_id,
            name="Apex Precision Tools",
            category="Manufacturing",
            city="Pune",
            state="Maharashtra",
            country="India",
            status="approved",
            opportunity_score=85
        )
        db_session.add(p)
        db_session.commit()
    return prospect_id

def test_send_email_requires_explicit_confirmation(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-conf-1")
    draft = EmailDraftModel(
        id="draft-test-1",
        prospect_id=p_id,
        recipient_name="Jane Doe",
        recipient_email="client@example.com",
        subject="Audit review",
        body="Hello test",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    payload = {
        "draft_id": "draft-test-1",
        "recipient_email": "client@example.com",
        "subject": "Audit review",
        "body": "Hello test",
        "confirmed": False  # Not confirmed
    }

    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Explicit operator confirmation is required" in resp.json()["detail"]

def test_send_email_missing_recipient_rejected(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-recip-1")
    draft = EmailDraftModel(
        id="draft-test-2",
        prospect_id=p_id,
        recipient_name="Jane Doe",
        recipient_email="",
        subject="Audit review",
        body="Hello test",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    payload = {
        "draft_id": "draft-test-2",
        "recipient_email": "",
        "subject": "Audit review",
        "body": "Hello test",
        "confirmed": True
    }

    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "No recipient email address is available" in resp.json()["detail"]

def test_send_email_suppressed_recipient_blocked(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-sup-1")
    draft = EmailDraftModel(
        id="draft-test-3",
        prospect_id=p_id,
        recipient_name="Jane Doe",
        recipient_email="unsubscribed@competitor.com",
        subject="Audit review",
        body="Hello test",
        status="approved"
    )
    suppression = SuppressionRecordModel(
        id="sup-1",
        email_or_domain="unsubscribed@competitor.com",
        reason="Unsubscribed from outreach"
    )
    db_session.add_all([draft, suppression])
    db_session.commit()

    payload = {
        "draft_id": "draft-test-3",
        "recipient_email": "unsubscribed@competitor.com",
        "subject": "Audit review",
        "body": "Hello test",
        "confirmed": True
    }

    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "suppressed" in resp.json()["detail"].lower()

def test_send_email_suppressed_domain_blocked(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-sup-2")
    draft = EmailDraftModel(
        id="draft-test-3b",
        prospect_id=p_id,
        recipient_name="Jane Doe",
        recipient_email="contact@blockeddomain.org",
        subject="Audit review",
        body="Hello test",
        status="approved"
    )
    suppression = SuppressionRecordModel(
        id="sup-2",
        email_or_domain="blockeddomain.org",
        reason="Domain-level opt-out"
    )
    db_session.add_all([draft, suppression])
    db_session.commit()

    payload = {
        "draft_id": "draft-test-3b",
        "recipient_email": "contact@blockeddomain.org",
        "subject": "Audit review",
        "body": "Hello test",
        "confirmed": True
    }

    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "suppressed" in resp.json()["detail"].lower()

def test_send_email_successful_flow(client: TestClient, db_session):
    acc = GoogleAccountModel(
        id="default",
        email="sender.verified@gmail.com",
        encrypted_access_token=encrypt_credential("valid_access_tok"),
        encrypted_refresh_token=encrypt_credential("valid_refresh_tok"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True
    )
    p_id = _create_seed_prospect(db_session, "pr-send-1")
    draft = EmailDraftModel(
        id="draft-send-1",
        prospect_id=p_id,
        recipient_name="Director",
        recipient_email="director@apexprecision.in",
        subject="Technical Audit: Broken contact form on apexprecision.in",
        body="Dear Apex Team,\nWe observed an issue on your website.",
        status="approved"
    )
    db_session.add_all([acc, draft])
    db_session.commit()

    mock_send_resp = MagicMock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {
        "id": "18ec9992f801aa44",
        "threadId": "18ec9992f801aa44",
        "labelIds": ["SENT"]
    }

    async def mock_gmail_send(url, *args, **kwargs):
        if "messages/send" in str(url):
            return mock_send_resp
        return MagicMock(status_code=404)

    with patch("httpx.AsyncClient.post", side_effect=mock_gmail_send):
        payload = {
            "draft_id": "draft-send-1",
            "recipient_email": "director@apexprecision.in",
            "subject": "Technical Audit: Broken contact form on apexprecision.in",
            "body": "Dear Apex Team,\nWe observed an issue on your website.",
            "confirmed": True
        }
        resp = client.post("/api/email/send", json=payload)

    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["gmail_message_id"] == "18ec9992f801aa44"
    assert res_data["sender"] == "sender.verified@gmail.com"
    assert res_data["recipient"] == "director@apexprecision.in"

    # Verify Draft Status Updated
    refreshed_draft = db_session.query(EmailDraftModel).filter(EmailDraftModel.id == "draft-send-1").first()
    assert refreshed_draft.status == "submitted"
    assert refreshed_draft.provider_message_id == "18ec9992f801aa44"

    # Verify Send Attempt Record in DB
    attempt = db_session.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.draft_id == "draft-send-1").first()
    assert attempt is not None
    assert attempt.status == "sent"
    assert attempt.gmail_message_id == "18ec9992f801aa44"

    # Verify Email History Record in DB
    history = db_session.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == "pr-send-1").first()
    assert history is not None
    assert history.status == "submitted"
    assert history.provider_message_id == "18ec9992f801aa44"

    # Verify Duplicate Send Attempt is Blocked
    dup_resp = client.post("/api/email/send", json=payload)
    assert dup_resp.status_code == 409
    assert "already sent" in dup_resp.json()["detail"].lower()

def test_send_email_network_timeout_marks_uncertain_and_blocks_duplicate(client: TestClient, db_session):
    acc = GoogleAccountModel(
        id="default",
        email="sender.verified@gmail.com",
        encrypted_access_token=encrypt_credential("valid_access_tok"),
        encrypted_refresh_token=encrypt_credential("valid_refresh_tok"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True
    )
    p_id = _create_seed_prospect(db_session, "pr-timeout-1")
    draft = EmailDraftModel(
        id="draft-timeout-1",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="lead@timeoutprospect.com",
        subject="Important review",
        body="Timeout test content",
        status="approved"
    )
    db_session.add_all([acc, draft])
    db_session.commit()

    async def mock_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Read timed out after 25 seconds")

    with patch("httpx.AsyncClient.post", side_effect=mock_timeout):
        payload = {
            "draft_id": "draft-timeout-1",
            "recipient_email": "lead@timeoutprospect.com",
            "subject": "Important review",
            "body": "Timeout test content",
            "confirmed": True
        }
        resp = client.post("/api/email/send", json=payload)

    assert resp.status_code == 504
    assert "UNCERTAIN" in resp.json()["detail"]

    # Verify Attempt marked as 'uncertain'
    attempt = db_session.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.draft_id == "draft-timeout-1").first()
    assert attempt is not None
    assert attempt.status == "uncertain"
    assert "Network timeout" in attempt.error_message

    # Verify blind retry is blocked
    retry_resp = client.post("/api/email/send", json=payload)
    assert retry_resp.status_code == 409
    assert "uncertain" in retry_resp.json()["detail"].lower()

def test_suppression_api_crud(client: TestClient, db_session):
    resp = client.post("/api/email/suppress", json={
        "email_or_domain": "optout@target.com",
        "reason": "Requested via unsubscribe footer"
    })
    assert resp.status_code == 201
    sup_id = resp.json()["id"]

    list_resp = client.get("/api/email/suppression")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(i["email_or_domain"] == "optout@target.com" for i in items)

    del_resp = client.delete(f"/api/email/suppress/{sup_id}")
    assert del_resp.status_code == 204

    remaining = client.get("/api/email/suppression").json()
    assert not any(i["id"] == sup_id for i in remaining)

# ----------------- Priority 0: Hardened Delivery & SMTP Tests -----------------

def test_header_injection_rejected_in_recipient(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-inj-1")
    draft = EmailDraftModel(
        id="draft-inj-1",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="valid@target.com",
        subject="Valid Subject",
        body="Valid body content",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    # Recipient with CRLF injection
    payload = {
        "draft_id": "draft-inj-1",
        "recipient_email": "victim@target.com\r\nBcc: evil@attacker.com",
        "subject": "Valid Subject",
        "body": "Body content",
        "confirmed": True
    }
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Header injection detected" in resp.json()["detail"]

    # Recipient with null byte
    payload["recipient_email"] = "victim\0@target.com"
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Header injection detected" in resp.json()["detail"]

def test_header_injection_rejected_in_subject(client: TestClient, db_session):
    p_id = _create_seed_prospect(db_session, "pr-inj-2")
    draft = EmailDraftModel(
        id="draft-inj-2",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="lead@target.com",
        subject="Valid Subject",
        body="Valid body content",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    # Subject with CRLF injection
    payload = {
        "draft_id": "draft-inj-2",
        "recipient_email": "lead@target.com",
        "subject": "Injected Subject\r\nBcc: hacker@spy.org",
        "body": "Body content",
        "confirmed": True
    }
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Header injection detected" in resp.json()["detail"]

    # Subject with newline
    payload["subject"] = "Injected Subject\nCc: spy@org.com"
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Header injection detected" in resp.json()["detail"]

    # Subject with null byte
    payload["subject"] = "Injected\0Subject"
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "Header injection detected" in resp.json()["detail"]

def test_unconfigured_dispatcher_returns_400(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    acc = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if acc:
        acc.is_connected = False
        db_session.commit()

    p_id = _create_seed_prospect(db_session, "pr-unconf-1")
    draft = EmailDraftModel(
        id="draft-unconf-1",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="lead@target.com",
        subject="Valid Subject",
        body="Body content",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    payload = {
        "draft_id": "draft-unconf-1",
        "recipient_email": "lead@target.com",
        "subject": "Valid Subject",
        "body": "Body content",
        "confirmed": True
    }
    resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 400
    assert "No active email dispatcher is configured" in resp.json()["detail"]

def test_smtp_successful_submission(client: TestClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_USER", "consultant.auditor@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "mock-16char-passw")

    acc = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if acc:
        acc.is_connected = False
        db_session.commit()

    p_id = _create_seed_prospect(db_session, "pr-smtp-1")
    draft = EmailDraftModel(
        id="draft-smtp-1",
        prospect_id=p_id,
        recipient_name="Operations Lead",
        recipient_email="ops@techclient.in",
        subject="Security & Accessibility Audit Review",
        body="Dear Operations Lead,\nWe inspected your website.",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        payload = {
            "draft_id": "draft-smtp-1",
            "recipient_email": "ops@techclient.in",
            "subject": "Security & Accessibility Audit Review",
            "body": "Dear Operations Lead,\nWe inspected your website.",
            "confirmed": True
        }
        resp = client.post("/api/email/send", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["delivery_method"] == "smtp"
    assert data["provider"] == "Gmail SMTP"
    assert data["sender"] == "consultant.auditor@gmail.com"
    assert data["recipient"] == "ops@techclient.in"
    assert data["status"] == "submitted"
    assert "gateway" in data["delivery_note"].lower()

    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("consultant.auditor@gmail.com", "mock-16char-passw")
    mock_smtp_instance.send_message.assert_called_once()

    # Verify Draft Status in DB
    refreshed_draft = db_session.query(EmailDraftModel).filter(EmailDraftModel.id == "draft-smtp-1").first()
    assert refreshed_draft.status == "submitted"
    assert refreshed_draft.provider_message_id.startswith("smtp-")

    # Verify Send Attempt in DB
    attempt = db_session.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.draft_id == "draft-smtp-1").first()
    assert attempt is not None
    assert attempt.status == "sent"

    # Verify Email History Record in DB
    history = db_session.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == "pr-smtp-1").first()
    assert history is not None
    assert history.provider == "Gmail SMTP"
    assert history.status == "submitted"

    # Duplicate send is blocked
    dup_resp = client.post("/api/email/send", json=payload)
    assert dup_resp.status_code == 409
    assert "already been submitted" in dup_resp.json()["detail"].lower() or "already sent" in dup_resp.json()["detail"].lower()

def test_smtp_authentication_failure_handled_safely(client: TestClient, db_session, monkeypatch):
    import smtplib
    monkeypatch.setattr(settings, "SMTP_USER", "sender@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "bad_password_secret")

    acc = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if acc:
        acc.is_connected = False
        db_session.commit()

    p_id = _create_seed_prospect(db_session, "pr-smtp-auth")
    draft = EmailDraftModel(
        id="draft-smtp-auth",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="lead@example.com",
        subject="Website Audit",
        body="Audit body content",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")

    with patch("smtplib.SMTP", return_value=mock_smtp_instance):
        payload = {
            "draft_id": "draft-smtp-auth",
            "recipient_email": "lead@example.com",
            "subject": "Website Audit",
            "body": "Audit body content",
            "confirmed": True
        }
        resp = client.post("/api/email/send", json=payload)

    assert resp.status_code == 400
    err_detail = resp.json()["detail"]
    assert "Gmail SMTP Authentication failed" in err_detail
    # Credentials must NOT be leaked
    assert "bad_password_secret" not in err_detail

    # Verify attempt in DB is marked failed
    attempt = db_session.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.draft_id == "draft-smtp-auth").first()
    assert attempt is not None
    assert attempt.status == "failed"
    assert attempt.error_code == "SMTP_AUTH_ERROR"
    assert "bad_password_secret" not in (attempt.error_message or "")

def test_smtp_connection_timeout_persists_uncertain_state(client: TestClient, db_session, monkeypatch):
    import socket
    monkeypatch.setattr(settings, "SMTP_USER", "sender@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "mock_pass")

    acc = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if acc:
        acc.is_connected = False
        db_session.commit()

    p_id = _create_seed_prospect(db_session, "pr-smtp-timeout")
    draft = EmailDraftModel(
        id="draft-smtp-timeout",
        prospect_id=p_id,
        recipient_name="Lead",
        recipient_email="lead@timeout.com",
        subject="Important Audit Findings",
        body="Findings body content",
        status="approved"
    )
    db_session.add(draft)
    db_session.commit()

    with patch("smtplib.SMTP", side_effect=socket.timeout("Socket connection timed out")):
        payload = {
            "draft_id": "draft-smtp-timeout",
            "recipient_email": "lead@timeout.com",
            "subject": "Important Audit Findings",
            "body": "Findings body content",
            "confirmed": True
        }
        resp = client.post("/api/email/send", json=payload)

    assert resp.status_code == 504
    assert "UNCERTAIN" in resp.json()["detail"]

    # Verify Send Attempt is marked 'uncertain'
    attempt = db_session.query(EmailSendAttemptModel).filter(EmailSendAttemptModel.draft_id == "draft-smtp-timeout").first()
    assert attempt is not None
    assert attempt.status == "uncertain"
    assert attempt.error_code == "SMTP_TIMEOUT"

    # Verify Draft Model status updated to 'uncertain'
    refreshed_draft = db_session.query(EmailDraftModel).filter(EmailDraftModel.id == "draft-smtp-timeout").first()
    assert refreshed_draft.status == "uncertain"

    # Verify Email History Model records uncertain state
    history = db_session.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == "pr-smtp-timeout").first()
    assert history is not None
    assert history.status == "uncertain"
    assert history.provider == "Gmail SMTP"

    # Verify blind retry is blocked with 409
    retry_resp = client.post("/api/email/send", json=payload)
    assert retry_resp.status_code == 409
    assert "uncertain" in retry_resp.json()["detail"].lower()

def test_email_dispatch_status_and_frontend_availability(client: TestClient, db_session, monkeypatch):
    # Scenario A: OAuth connected
    acc = GoogleAccountModel(
        id="default",
        email="oauth.verified@gmail.com",
        encrypted_access_token=encrypt_credential("valid_tok"),
        is_connected=True
    )
    db_session.merge(acc)
    db_session.commit()

    resp = client.get("/api/email/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_ready"] is True
    assert data["method"] == "oauth"
    assert data["provider_name"] == "Gmail API (OAuth 2.0)"
    assert data["sender_email"] == "oauth.verified@gmail.com"

    # Scenario B: OAuth disconnected, SMTP configured
    acc_in_db = db_session.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    acc_in_db.is_connected = False
    db_session.commit()
    monkeypatch.setattr(settings, "SMTP_USER", "smtp.ready@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "app_pwd_16chars")

    resp2 = client.get("/api/email/status")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["is_ready"] is True
    assert data2["method"] == "smtp"
    assert data2["provider_name"] == "Gmail SMTP"
    assert data2["sender_email"] == "smtp.ready@gmail.com"
    assert data2["smtp_configured"] is True

    # Scenario C: Neither configured
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    resp3 = client.get("/api/email/status")
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["is_ready"] is False
    assert data3["method"] == "none"
    assert data3["sender_email"] is None

def test_smtp_test_connection_endpoint(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    mock_server = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_server):
        resp = client.post("/api/email/test-smtp", json={"user": "test@gmail.com", "password": "mockpassword1234"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_server.login.assert_called_once_with("test@gmail.com", "mockpassword1234")

    # Missing credentials rejected
    resp_empty = client.post("/api/email/test-smtp", json={"user": "", "password": ""})
    assert resp_empty.status_code == 400
