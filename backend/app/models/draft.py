from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from datetime import datetime, timezone
from backend.app.core.database import Base

class EmailDraftModel(Base):
    __tablename__ = "email_drafts"

    id = Column(String, primary_key=True, index=True)
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    audit_id = Column(String, nullable=True, index=True)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    subject_alternatives = Column(Text, default="[]")  # JSON encoded list of strings
    body = Column(Text, nullable=False)
    findings_referenced = Column(Text, default="[]")  # JSON encoded list of finding IDs
    ai_claims_rationale = Column(Text, default="[]")  # JSON encoded list of claim rationale objects
    outreach_purpose = Column(String, nullable=True, default="website_improvement")
    writing_tone = Column(String, nullable=True, default="professional")
    ai_provider = Column(String, nullable=True)
    ai_model = Column(String, nullable=True)
    generation_metadata = Column(Text, default="{}")  # JSON encoded metadata
    status = Column(String, default="draft")  # draft, edited, approved, submitted, failed, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

