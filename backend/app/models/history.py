from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
from backend.app.core.database import Base

class EmailHistoryModel(Base):
    __tablename__ = "email_history"

    id = Column(String, primary_key=True, index=True)
    recipient = Column(String, nullable=False)
    prospect_name = Column(String, nullable=False)
    prospect_id = Column(String, nullable=True, index=True)
    subject = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(String, default="submitted")  # submitted, failed, cancelled
    provider = Column(String, default="Gmail API (OAuth 2.0)")
    provider_message_id = Column(String, nullable=True)
    body_snippet = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SuppressionRecordModel(Base):
    __tablename__ = "suppression_records"

    id = Column(String, primary_key=True, index=True)
    email_or_domain = Column(String, unique=True, index=True, nullable=False)
    reason = Column(String, default="Unsubscribed or bounced")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
