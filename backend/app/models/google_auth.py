from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from datetime import datetime, timezone
from backend.app.core.database import Base

class GoogleAccountModel(Base):
    """
    Persists real connected Google Account credentials and OAuth metadata.
    Tokens are stored strictly in authenticated encrypted form (Fernet AES-128-CBC + HMAC).
    Never exposed to frontend or plaintext database queries.
    """
    __tablename__ = "google_accounts"

    id = Column(String, primary_key=True, index=True, default="default")
    email = Column(String, unique=True, index=True, nullable=False)
    google_sub = Column(String, nullable=True)  # Google account unique subject ID
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_uri = Column(String, default="https://oauth2.googleapis.com/token")
    scopes = Column(Text, nullable=False, default="[]")  # JSON-encoded array of granted scopes
    expires_at = Column(DateTime, nullable=True)
    is_connected = Column(Boolean, default=True)
    connected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class OAuthStateModel(Base):
    """
    Tracks cryptographically secure CSRF states and PKCE code verifiers for OAuth flows.
    States are one-time-use with a short TTL (10 minutes) to prevent replay and CSRF attacks.
    """
    __tablename__ = "oauth_states"

    state = Column(String, primary_key=True, index=True)
    code_verifier = Column(String, nullable=True)
    redirect_uri = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)

class EmailSendAttemptModel(Base):
    """
    Durable record of every outbound email attempt to prevent duplicate sends,
    record exact confirmation states, and handle uncertain network outcomes safely.
    """
    __tablename__ = "email_send_attempts"

    id = Column(String, primary_key=True, index=True)
    draft_id = Column(String, index=True, nullable=False)
    prospect_id = Column(String, index=True, nullable=True)
    recipient_email = Column(String, index=True, nullable=False)
    sender_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body_hash = Column(String, nullable=False)  # SHA-256 hash of confirmed content
    status = Column(String, default="awaiting_confirmation", index=True)
    # Statuses: 'awaiting_confirmation', 'sending', 'sent', 'failed', 'uncertain'
    gmail_message_id = Column(String, nullable=True, index=True)
    gmail_thread_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    attempt_number = Column(Integer, default=1)
    confirmed_at = Column(DateTime, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
