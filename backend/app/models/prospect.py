from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime, timezone
from backend.app.core.database import Base

class ProspectModel(Base):
    __tablename__ = "prospects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, default="Commercial Services")
    city = Column(String, default="Mumbai")
    state = Column(String, default="Maharashtra")
    country = Column(String, default="India")
    website_url = Column(String, nullable=True)
    website_status = Column(String, default="active")  # active, not_listed, unreachable, dns_error, ssl_expired, broken_pages
    opportunity_score = Column(Integer, default=70)
    score_urgency = Column(Integer, default=25)
    score_intent = Column(Integer, default=25)
    score_ease = Column(Integer, default=20)
    status = Column(String, default="new")  # new, needs_audit, needs_review, draft_ready, contacted, archived
    last_activity = Column(String, default="Just now")
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    audit_count = Column(Integer, default=0)
    latest_audit_id = Column(String, nullable=True)
    recommended_action = Column(Text, default="Execute website audit crawl.")
    notes = Column(Text, nullable=True)
    tags = Column(Text, default="[]")  # JSON encoded list of strings
    source_provider = Column(String, nullable=True, default=None)  # osm, google_places, csv_import, manual
    source_record_id = Column(String, nullable=True, default=None)  # provider record ID (e.g. node/123456)
    source_url = Column(String, nullable=True, default=None)  # direct web link to source entity
    identity_status = Column(String, default="not_checked")  # verified, likely_match, uncertain, conflicting, not_found, not_checked
    identity_evidence = Column(Text, default="{}")  # JSON encoded evidence dict
    contact_provenance = Column(Text, default="{}")  # JSON encoded provenance dict
    social_profiles = Column(Text, default="{}")  # JSON encoded social profile matches dict
    discovered_at = Column(DateTime, nullable=True, default=None)
    last_verified_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
