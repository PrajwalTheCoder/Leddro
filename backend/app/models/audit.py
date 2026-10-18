from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.core.database import Base

class AuditReportModel(Base):
    __tablename__ = "audit_reports"

    id = Column(String, primary_key=True, index=True)
    prospect_id = Column(String, ForeignKey("prospects.id", ondelete="SET NULL"), nullable=True, index=True)
    url = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    status = Column(String, default="completed")  # completed, running, failed
    overall_score = Column(Integer, default=70)
    raw_dns = Column(Text, default="{}")  # JSON encoded A, MX, NS, response_ms
    raw_ssl = Column(Text, default="{}")  # JSON encoded valid, issuer, expires_days, tls_version, cipher
    performance = Column(Text, default="{}")  # JSON encoded ttfb_ms, dom_ready_ms, page_size_kb, viewport_present
    headers = Column(Text, default="{}")  # JSON encoded HTTP response headers
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    findings = relationship("AuditFindingModel", back_populates="report", cascade="all, delete-orphan")

class AuditFindingModel(Base):
    __tablename__ = "audit_findings"

    id = Column(String, primary_key=True, index=True)
    audit_report_id = Column(String, ForeignKey("audit_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # high, medium, low, info
    check_status = Column(String, default="WARNING")  # PASS, WARNING, FAIL, ERROR, NOT_CHECKED
    observed = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    why_it_matters = Column(Text, default="")
    recommended_action = Column(Text, default="")
    confidence = Column(Float, default=1.0)
    category = Column(String, default="reachability")  # security, reachability, performance, seo_meta, conversion
    http_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    checked_url = Column(String, nullable=True)

    report = relationship("AuditReportModel", back_populates="findings")
