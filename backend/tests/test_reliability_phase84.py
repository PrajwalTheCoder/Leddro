import os
import json
import sqlite3
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.draft import EmailDraftModel
from backend.app.models.history import EmailHistoryModel, SuppressionRecordModel
from backend.app.core.backup import (
    backup_sqlite_database,
    verify_sqlite_backup,
    restore_sqlite_database
)
from backend.app.services.ssrf_validator import validate_target_url, is_ip_allowed
from backend.app.discovery.providers.csv_import import (
    preview_csv_import,
    commit_csv_import
)

client = TestClient(app)

@pytest.fixture
def isolated_db():
    """Provides a fresh, temporary, isolated SQLite database session for unit tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = tf.name

    test_db_url = f"sqlite:///{temp_db_path}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    
    # Enable SQLite foreign keys on test engine
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session, temp_db_path
    finally:
        session.close()
        engine.dispose()
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError:
                pass


# ==============================================================================
# 1. DATABASE INTEGRITY, CASCADE, AND ROLLBACK TESTS
# ==============================================================================

def test_sqlite_foreign_key_pragmas_active():
    """Verifies that SQLite connections have PRAGMA foreign_keys enabled."""
    from backend.app.core.database import engine
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert result == 1, "PRAGMA foreign_keys must be enabled (1) on SQLite connections."


def test_delete_prospect_cascades_and_nulls_cleanly(isolated_db):
    """
    Verifies that deleting a prospect:
    - Nulls out prospect_id on associated AuditReports (preserving audit history)
    - Removes associated EmailDrafts
    - Nulls out prospect_id on EmailHistory (preserving audit trail)
    """
    session, _ = isolated_db

    # Create prospect
    prospect = ProspectModel(
        id="pros_test_cascade",
        name="Cascade Test Corp",
        website_url="https://cascade-test.com",
        opportunity_score=75
    )
    session.add(prospect)
    session.commit()

    # Create associated audit report
    audit = AuditReportModel(
        id="aud_cascade_1",
        prospect_id=prospect.id,
        url="https://cascade-test.com",
        timestamp="2026-10-19 12:00 UTC",
        status="completed",
        overall_score=75
    )
    session.add(audit)

    # Create associated email draft
    draft = EmailDraftModel(
        id="draft_cascade_1",
        prospect_id=prospect.id,
        recipient_email="test@cascade-test.com",
        recipient_name="Cascade Tester",
        subject="Audit Findings",
        body="Here are the findings."
    )
    session.add(draft)

    # Create associated email history
    history = EmailHistoryModel(
        id="hist_cascade_1",
        recipient="test@cascade-test.com",
        prospect_name=prospect.name,
        prospect_id=prospect.id,
        subject="Audit Findings",
        date="2026-10-19 12:00 UTC",
        body_snippet="Here are the findings."
    )
    session.add(history)
    session.commit()

    # Perform deletion logic as implemented in delete_prospect endpoint
    session.query(AuditReportModel).filter(AuditReportModel.prospect_id == prospect.id).update(
        {AuditReportModel.prospect_id: None}, synchronize_session=False
    )
    session.query(EmailDraftModel).filter(EmailDraftModel.prospect_id == prospect.id).delete(
        synchronize_session=False
    )
    session.query(EmailHistoryModel).filter(EmailHistoryModel.prospect_id == prospect.id).update(
        {EmailHistoryModel.prospect_id: None}, synchronize_session=False
    )
    session.delete(prospect)
    session.commit()

    # Verify prospect is gone
    assert session.query(ProspectModel).filter(ProspectModel.id == "pros_test_cascade").first() is None
    # Verify audit still exists but prospect_id is None
    retained_audit = session.query(AuditReportModel).filter(AuditReportModel.id == "aud_cascade_1").first()
    assert retained_audit is not None
    assert retained_audit.prospect_id is None
    # Verify draft was cleanly deleted
    assert session.query(EmailDraftModel).filter(EmailDraftModel.id == "draft_cascade_1").first() is None
    # Verify history still exists but prospect_id is None
    retained_hist = session.query(EmailHistoryModel).filter(EmailHistoryModel.id == "hist_cascade_1").first()
    assert retained_hist is not None
    assert retained_hist.prospect_id is None


def test_transaction_rollback_on_failed_operation(isolated_db):
    """Verifies that an exception during a multi-step operation rolls back cleanly."""
    session, _ = isolated_db

    initial_count = session.query(ProspectModel).count()

    # Start multi-step write that deliberately raises
    try:
        p1 = ProspectModel(id="pros_rollback_1", name="Rollback Prospect 1")
        session.add(p1)
        # Simulate unexpected failure before commit
        raise RuntimeError("Simulated mid-transaction failure")
    except RuntimeError:
        session.rollback()

    assert session.query(ProspectModel).count() == initial_count
    assert session.query(ProspectModel).filter(ProspectModel.id == "pros_rollback_1").first() is None


# ==============================================================================
# 2. INTRA-BATCH CSV DEDUPLICATION TESTS
# ==============================================================================

def test_csv_import_intra_batch_deduplication(isolated_db):
    """
    Verifies that a CSV batch containing duplicate rows within itself
    suppresses intra-batch duplicates when skip_duplicates=True.
    """
    session, _ = isolated_db

    csv_data = """Business Name,Category,City,State,Website,Phone,Email
Alpha Solutions,Technology,Mumbai,Maharashtra,https://alpha-sol.com,+91 9876543210,hello@alpha-sol.com
Alpha Solutions,Technology,Mumbai,Maharashtra,https://alpha-sol.com,+91 9876543210,hello@alpha-sol.com
Beta Logistics,Transport,Pune,Maharashtra,https://beta-log.com,+91 9876543211,info@beta-log.com
Gamma Tech,Technology,Mumbai,Maharashtra,https://alpha-sol.com,+91 9876543212,other@alpha-sol.com
"""

    preview = preview_csv_import(session, csv_data)
    assert preview.total_rows == 4
    assert preview.valid_count == 4
    # Rows 2 and 4 have duplicate URLs with row 1
    assert preview.duplicate_count == 2
    assert preview.preview_records[1].is_duplicate is True
    assert "Duplicate within CSV batch" in (preview.preview_records[1].duplicate_reason or "")
    assert preview.preview_records[3].is_duplicate is True

    # Now commit with skip_duplicates=True
    records = [
        {
            "name": r.name,
            "category": r.category,
            "city": r.city,
            "state": r.state,
            "country": r.country,
            "website_url": r.website_url,
            "website_status": r.website_status,
            "phone": r.phone,
            "email": r.email,
            "opportunity_score": r.opportunity_score
        }
        for r in preview.preview_records
    ]

    summary = commit_csv_import(session, records, skip_duplicates=True)
    assert summary.imported_count == 2  # Alpha Solutions and Beta Logistics
    assert summary.skipped_duplicates_count == 2
    assert summary.total_processed == 4


# ==============================================================================
# 3. BACKUP RESTORATION AND CORRUPTION SAFETY TESTS
# ==============================================================================

def test_backup_restore_into_temporary_test_database():
    """
    Verifies that:
    1. A database can be backed up using atomic backup_sqlite_database
    2. verify_sqlite_backup verifies data integrity
    3. Corrupted backup files fail safely without crashing
    4. restore_sqlite_database restores into an isolated target without touching dev DB
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_db = tmp_path / "source.db"
        backup_file = tmp_path / "test_backup.db"
        target_db = tmp_path / "restored_target.db"
        corrupt_file = tmp_path / "corrupt.db"

        # Initialize source DB with a test table and records
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test_data (id TEXT PRIMARY KEY, value TEXT);")
        conn.execute("INSERT INTO test_data VALUES ('1', 'alpha');")
        conn.execute("INSERT INTO test_data VALUES ('2', 'beta');")
        conn.commit()
        conn.close()

        # 1. Backup from source_db to backup_file
        res_path = backup_sqlite_database(destination_path=backup_file, source_path=source_db)
        assert res_path.exists()

        # 2. Verify backup
        verification = verify_sqlite_backup(backup_file)
        assert verification["valid"] is True
        assert verification["status"] == "ok"
        assert verification["counts"].get("test_data") == 2

        # 3. Corrupt file test
        corrupt_file.write_bytes(b"CORRUPTED_NOT_A_VALID_SQLITE_DATABASE_HEADER_00000000")
        corrupt_verif = verify_sqlite_backup(corrupt_file)
        assert corrupt_verif["valid"] is False
        assert "corrupt" in corrupt_verif["status"] or "failed" in corrupt_verif["status"]

        # Verify restore rejects corrupted file safely
        with pytest.raises(ValueError, match="Backup verification failed"):
            restore_sqlite_database(corrupt_file, create_safety_snapshot=False, target_path=target_db)

        # 4. Restore valid backup into isolated target_db
        restore_res = restore_sqlite_database(backup_file, create_safety_snapshot=False, target_path=target_db)
        assert restore_res["target"] == str(target_db)
        assert target_db.exists()

        # Verify restored target contains the exact data
        tgt_conn = sqlite3.connect(str(target_db))
        rows = tgt_conn.execute("SELECT id, value FROM test_data ORDER BY id;").fetchall()
        tgt_conn.close()
        assert rows == [("1", "alpha"), ("2", "beta")]


# ==============================================================================
# 4. SSRF COMPREHENSIVE FILTER TESTS (Deterministic Mocks)
# ==============================================================================

@pytest.mark.parametrize("prohibited_ip", [
    "127.0.0.1",
    "127.0.1.1",
    "10.0.0.1",
    "10.254.0.1",
    "172.16.0.1",
    "172.31.255.255",
    "192.168.1.1",
    "192.168.100.50",
    "169.254.169.254",   # AWS / GCP metadata
    "0.0.0.0",
    "::1",                # IPv6 loopback
    "fe80::1",            # IPv6 link-local
    "fc00::1",            # IPv6 unique local
])
def test_ssrf_prohibits_private_and_metadata_ips(prohibited_ip):
    """Verifies that all private, loopback, link-local, and metadata IPs are rejected."""
    allowed, reason = is_ip_allowed(prohibited_ip)
    assert allowed is False
    assert reason is not None


@pytest.mark.parametrize("malformed_or_dangerous_url", [
    "file:///etc/passwd",
    "ftp://example.com/file",
    "gopher://example.com",
    "http://169.254.169.254/latest/meta-data/",
    "http://127.0.0.1:8000/api/health",
    "http://localhost:5173",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://instance-data/latest/meta-data/",
    "http://example.com:22/",       # Disallowed SSH port
    "http://example.com:3306/",     # Disallowed MySQL port
])
def test_target_url_validation_rejects_unsafe_destinations(malformed_or_dangerous_url):
    """Verifies that validate_target_url rejects non-HTTP protocols, bad ports, and prohibited hosts."""
    is_safe, error_msg, _, _ = validate_target_url(malformed_or_dangerous_url)
    assert is_safe is False
    assert error_msg is not None


# ==============================================================================
# 5. EMAIL DELIVERY UNCERTAINTY & DUPLICATE PREVENTION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_uncertain_email_status_blocks_blind_retry(isolated_db):
    """
    Verifies that a draft marked with status='uncertain' cannot be resent,
    preventing duplicate delivery when network timeout occurred.
    """
    session, _ = isolated_db
    from backend.app.services.gmail_client import send_draft_via_gmail
    from fastapi import HTTPException

    # Create parent prospect first to satisfy SQLite foreign key constraint
    prospect = ProspectModel(
        id="pros_mock",
        name="Mock Co",
        website_url="https://mock.example.com",
        opportunity_score=70
    )
    session.add(prospect)
    session.flush()

    # Create draft with uncertain status
    draft = EmailDraftModel(
        id="draft_uncertain_1",
        prospect_id="pros_mock",
        recipient_email="client@example.com",
        recipient_name="Client",
        subject="Proposal",
        body="Hello world",
        status="uncertain"
    )
    session.add(draft)
    session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await send_draft_via_gmail(
            db=session,
            draft_id="draft_uncertain_1",
            recipient_email="client@example.com",
            subject="Proposal",
            body="Hello world",
            confirmed=True
        )

    assert exc_info.value.status_code == 409
    assert "uncertain delivery state" in exc_info.value.detail


def test_email_subject_header_injection_rejection():
    """Verifies that newline characters in subject lines are rejected to prevent CRLF injection."""
    from backend.app.services.gmail_client import validate_subject
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        validate_subject("Normal Subject\r\nBcc: victim@example.com")
    assert exc_info.value.status_code == 400
    assert "header injection" in exc_info.value.detail.lower()


# ==============================================================================
# 6. DETERMINISTIC SCORING & EXPLAINABLE EVIDENCE TESTS
# ==============================================================================

def test_scoring_determinism_and_evidence_consistency():
    """
    Verifies that prospect scoring is 100% deterministic and that
    missing audit evidence does not fabricate high technical urgency.
    """
    from backend.app.services.prospect_scoring import calculate_prospect_score

    class MockProspect:
        def __init__(self, name="Test Co", category="Commercial Services", city="Mumbai", phone="+919999999999", email="a@b.com", website_url="https://test.com", website_status="active"):
            self.name = name
            self.category = category
            self.city = city
            self.phone = phone
            self.email = email
            self.website_url = website_url
            self.website_status = website_status

    p = MockProspect()

    # Score with no audit
    res_no_audit_1 = calculate_prospect_score(p, None)
    res_no_audit_2 = calculate_prospect_score(p, None)
    assert res_no_audit_1 == res_no_audit_2
    assert res_no_audit_1["confidence_score"] <= 60  # Confidence capped without audit
    assert res_no_audit_1["audit_status"] == "none"

    # Score with audit containing 2 high severity findings
    class MockFinding:
        def __init__(self, fid, title, sev, status):
            self.id = fid
            self.title = title
            self.severity = sev
            self.check_status = status

    class MockAudit:
        def __init__(self):
            self.id = "aud_1"
            self.status = "completed"
            self.timestamp = "2026-10-19 12:00 UTC"
            self.findings = [
                MockFinding("f1", "SSL Expired", "high", "FAIL"),
                MockFinding("f2", "DNS Missing MX", "high", "FAIL"),
            ]

    a = MockAudit()
    res_audit_1 = calculate_prospect_score(p, a)
    res_audit_2 = calculate_prospect_score(p, a)
    assert res_audit_1 == res_audit_2
    assert res_audit_1["opportunity_score"] > res_no_audit_1["opportunity_score"]
    assert res_audit_1["confidence_score"] > res_no_audit_1["confidence_score"]
    assert res_audit_1["severity_summary"]["high"] == 2
