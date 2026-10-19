import os
import json
import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.draft import EmailDraftModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.discovery.providers.csv_import import (
    preview_csv_import,
    commit_csv_import
)
from backend.app.services.audit_comparison import compare_audits
from backend.app.services.prospect_scoring import calculate_prospect_score

client = TestClient(app)

@pytest.fixture
def temp_db():
    """Creates a temporary, fully isolated SQLite database for integration testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name

    test_db_url = f"sqlite:///{temp_path}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()

    try:
        yield session, temp_path, test_engine
    finally:
        session.close()
        test_engine.dispose()
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ==============================================================================
# 1. PROSPECT DELETION & AUDIT HISTORY RETENTION (Section 4A)
# ==============================================================================

def test_prospect_deletion_retains_audit_history_and_findings(temp_db):
    """
    Verifies that deleting a prospect:
    - Retains AuditReportModel with prospect_id set to None
    - Retains all child AuditFindingModel records
    - Deletes associated EmailDraftModel
    - Retains EmailHistoryModel with prospect_id set to None
    """
    session, _, _ = temp_db

    # 1. Create prospect
    prospect = ProspectModel(
        id="pros_lifecycle_1",
        name="Lifecycle Technologies",
        website_url="https://lifecycle-tech.com",
        opportunity_score=85
    )
    session.add(prospect)
    session.commit()

    # 2. Add audit report with findings
    report = AuditReportModel(
        id="aud_lifecycle_1",
        prospect_id="pros_lifecycle_1",
        url="https://lifecycle-tech.com",
        timestamp="2026-10-19 14:00 UTC",
        status="completed",
        overall_score=85
    )
    session.add(report)

    f1 = AuditFindingModel(
        id="find_lifecycle_1",
        audit_report_id="aud_lifecycle_1",
        title="Expired SSL Certificate",
        severity="high",
        check_status="FAIL",
        observed="TLS expired 10 days ago",
        evidence="SSL Handshake: EXPIRED"
    )
    f2 = AuditFindingModel(
        id="find_lifecycle_2",
        audit_report_id="aud_lifecycle_1",
        title="Missing DMARC Policy",
        severity="medium",
        check_status="WARNING",
        observed="No DMARC record in DNS",
        evidence="DNS TXT: NXDOMAIN"
    )
    session.add(f1)
    session.add(f2)

    # 3. Add email draft and history
    draft = EmailDraftModel(
        id="draft_lifecycle_1",
        prospect_id="pros_lifecycle_1",
        recipient_email="admin@lifecycle-tech.com",
        recipient_name="Admin",
        subject="Audit Notice",
        body="SSL is expired"
    )
    history = EmailHistoryModel(
        id="hist_lifecycle_1",
        recipient="admin@lifecycle-tech.com",
        prospect_name="Lifecycle Technologies",
        prospect_id="pros_lifecycle_1",
        subject="Audit Notice",
        date="2026-10-19 14:05 UTC",
        body_snippet="SSL is expired"
    )
    session.add(draft)
    session.add(history)
    session.commit()

    # 4. Execute deletion logic as in delete_prospect endpoint
    session.query(AuditReportModel).filter(AuditReportModel.prospect_id == "pros_lifecycle_1").update(
        {AuditReportModel.prospect_id: None}, synchronize_session=False
    )
    session.query(EmailDraftModel).filter(EmailDraftModel.prospect_id == "pros_lifecycle_1").delete(
        synchronize_session=False
    )
    session.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == "pros_lifecycle_1").update(
        {EmailHistoryModel.prospect_id: None}, synchronize_session=False
    )
    session.delete(prospect)
    session.commit()

    # Assertions
    # Prospect is deleted
    assert session.query(ProspectModel).filter(ProspectModel.id == "pros_lifecycle_1").first() is None

    # Audit report is preserved with prospect_id=None
    retained_report = session.query(AuditReportModel).filter(AuditReportModel.id == "aud_lifecycle_1").first()
    assert retained_report is not None
    assert retained_report.prospect_id is None
    assert retained_report.url == "https://lifecycle-tech.com"

    # Findings are fully preserved
    retained_findings = session.query(AuditFindingModel).filter(AuditFindingModel.audit_report_id == "aud_lifecycle_1").all()
    assert len(retained_findings) == 2

    # Draft was deleted
    assert session.query(EmailDraftModel).filter(EmailDraftModel.id == "draft_lifecycle_1").first() is None

    # History was preserved with prospect_id=None
    retained_hist = session.query(EmailHistoryModel).filter(EmailHistoryModel.id == "hist_lifecycle_1").first()
    assert retained_hist is not None
    assert retained_hist.prospect_id is None
    assert retained_hist.prospect_name == "Lifecycle Technologies"


# ==============================================================================
# 2. SQLITE FOREIGN-KEY ENFORCEMENT & ORPHAN DIAGNOSTICS (Section 4B)
# ==============================================================================

def test_sqlite_foreign_key_orphan_prevention(temp_db):
    """
    Verifies that foreign key constraints actively prevent orphan insertion.
    """
    session, _, _ = temp_db

    # Attempting to insert an audit finding without an existing parent AuditReportModel
    orphan_finding = AuditFindingModel(
        id="find_orphan_1",
        audit_report_id="non_existent_audit_id",
        title="Orphaned finding",
        severity="low",
        observed="Test",
        evidence="Test"
    )
    session.add(orphan_finding)
    with pytest.raises(Exception) as exc_info:
        session.commit()
    session.rollback()
    assert "foreign key" in str(exc_info.value).lower()


# ==============================================================================
# 3. CSV BATCH DEDUPLICATION MATRIX (Section 4C)
# ==============================================================================

def test_csv_deduplication_two_identical_urls(temp_db):
    """Test 1: Two identical URLs in one batch (with protocol differences) are detected."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
First Firm,Consulting,Mumbai,Maharashtra,http://firm.com,,
Second Firm,Consulting,Mumbai,Maharashtra,https://www.firm.com/,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 1
    assert preview.preview_records[1].is_duplicate is True


def test_csv_deduplication_same_name_different_urls(temp_db):
    """Test 2: Two records with the same name and city but different URLs."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Acme Services,Consulting,Mumbai,Maharashtra,https://acme-one.com,,
Acme Services,Consulting,Mumbai,Maharashtra,https://acme-two.com,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 1
    assert preview.preview_records[1].is_duplicate is True
    assert "business name & city" in preview.preview_records[1].duplicate_reason.lower()


def test_csv_deduplication_different_names_same_url(temp_db):
    """Test 3: Two records with different names but identical website domain."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Brand A,Retail,Pune,Maharashtra,https://shared-shop.com,,
Brand B,Retail,Pune,Maharashtra,https://shared-shop.com,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 1
    assert preview.preview_records[1].is_duplicate is True
    assert "website domain" in preview.preview_records[1].duplicate_reason.lower()


def test_csv_deduplication_no_url_identical_name_same_city(temp_db):
    """Test 4: Two records without URLs but identical names in the same city."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Apex Workshop,Auto,Delhi,Delhi,,,
Apex Workshop,Auto,Delhi,Delhi,,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 1
    assert preview.preview_records[1].is_duplicate is True


def test_csv_deduplication_no_url_same_name_different_cities(temp_db):
    """Test 5: Two records without URLs with identical names in DIFFERENT cities (not duplicates)."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Apex Workshop,Auto,Delhi,Delhi,,,
Apex Workshop,Auto,Bengaluru,Karnataka,,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 0  # Separate regional entities
    assert preview.preview_records[0].is_duplicate is False
    assert preview.preview_records[1].is_duplicate is False


def test_csv_deduplication_generic_host_not_merged(temp_db):
    """Test 6: Social media or generic hosts (e.g. facebook.com) are not treated as duplicate domains."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Bakery One,Food,Mumbai,Maharashtra,https://facebook.com/bakeryone,,
Plumbing Two,Services,Pune,Maharashtra,https://facebook.com/plumbingtwo,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    assert preview.duplicate_count == 0


def test_csv_commit_skip_duplicates_toggle(temp_db):
    """Test 7: Verify skip_duplicates=True skips vs skip_duplicates=False imports all."""
    session, _, _ = temp_db
    records = [
        {"name": "Dupe Corp", "city": "Mumbai", "website_url": "https://dupe.com"},
        {"name": "Dupe Corp", "city": "Mumbai", "website_url": "https://dupe.com"},
    ]

    # With skip_duplicates=True
    summary_skip = commit_csv_import(session, records, skip_duplicates=True)
    assert summary_skip.imported_count == 1
    assert summary_skip.skipped_duplicates_count == 1

    # Now with a fresh batch and skip_duplicates=False
    records2 = [
        {"name": "Explicit Corp A", "city": "Mumbai", "website_url": "https://explicit.com"},
        {"name": "Explicit Corp B", "city": "Mumbai", "website_url": "https://explicit.com"},
    ]
    summary_noskip = commit_csv_import(session, records2, skip_duplicates=False)
    assert summary_noskip.imported_count == 2
    assert summary_noskip.skipped_duplicates_count == 0


def test_csv_sanitizes_formula_injection(temp_db):
    """Test 8: CSV parser escapes dangerous formula prefixes (=, +, -, @)."""
    session, _, _ = temp_db
    csv_data = """Business Name,Category,City,State,Website,Phone,Email
=cmd|' /C calc'!A0,Services,Mumbai,Maharashtra,https://safe.com,,
+SUM(1+1),Services,Mumbai,Maharashtra,https://safe-two.com,,
"""
    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 2
    # Ensure formula prefixes were sanitized with leading quote
    assert preview.preview_records[0].name.startswith("'")
    assert preview.preview_records[1].name.startswith("'")


# ==============================================================================
# 4. AUDIT COMPARISON REGRESSION SAFEGUARDS (Section 3 Workflow D)
# ==============================================================================

def test_audit_comparison_cross_domain_and_inconclusive_checks():
    """
    Verifies that compare_audits enforces:
    - Cross-domain rejection
    - Missing checks classified as INCONCLUSIVE (not resolved)
    - Persistent findings preserved
    """
    class MockAudit:
        def __init__(self, aid, pid, url, timestamp, score, findings, status="completed"):
            self.id = aid
            self.prospect_id = pid
            self.url = url
            self.timestamp = timestamp
            self.overall_score = score
            self.findings = findings
            self.status = status
            self.raw_dns = "{}"
            self.raw_ssl = "{}"
            self.performance = "{}"

    class MockFinding:
        def __init__(self, fid, title, cat, sev, status, obs, ev):
            self.id = fid
            self.title = title
            self.category = cat
            self.severity = sev
            self.check_status = status
            self.observed = obs
            self.evidence = ev

    # 1. Cross-domain mismatch check
    a1 = MockAudit("aud_1", "p1", "https://site-a.com", "2026-10-01 10:00 UTC", 70, [])
    a2 = MockAudit("aud_2", "p1", "https://site-b.com", "2026-10-15 10:00 UTC", 70, [])

    with pytest.raises(Exception) as exc_info:
        compare_audits(a1, a2)
    assert "different websites" in str(exc_info.value).lower()

    # 2. Inconclusive check when older had finding but newer audit failed
    f_ssl = MockFinding("f1", "SSL Expired", "security", "high", "FAIL", "Expired", "TLS Expired")
    a_old = MockAudit("aud_old", "p1", "https://site-a.com", "2026-10-01 10:00 UTC", 60, [f_ssl], status="completed")
    a_new_failed = MockAudit("aud_new", "p1", "https://site-a.com", "2026-10-15 10:00 UTC", 0, [], status="failed")

    comp_res = compare_audits(a_old, a_new_failed)
    # The missing finding in a failed audit must NOT be classified as resolved!
    assert len(comp_res["resolvedFindings"]) == 0
    assert len(comp_res["inconclusiveFindings"]) == 1
    assert comp_res["inconclusiveFindings"][0]["state"] == "inconclusive"
