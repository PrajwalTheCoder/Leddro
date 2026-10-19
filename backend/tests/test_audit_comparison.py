"""
Comprehensive test suite for Phase 8.3:
Website Audit Comparison & Change Detection (Audit Comparison Service & API)
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch

from backend.app.services.audit_comparison import (
    derive_check_key,
    normalize_check_status,
    is_finding_defect,
    is_finding_pass,
    compare_audits,
    AuditComparisonService
)
from backend.app.models.audit import AuditReportModel, AuditFindingModel
from backend.app.models.prospect import ProspectModel


class MockAuditReport:
    """Mock audit report model for pure service tests."""
    def __init__(
        self,
        id: str,
        url: str = "https://example.com",
        timestamp: str = "2026-10-18 10:00:00 UTC",
        status: str = "completed",
        overall_score: int = 70,
        findings: list = None,
        raw_dns: dict = None,
        raw_ssl: dict = None,
        performance: dict = None,
        headers: dict = None,
        prospect_id: str = "p-1"
    ):
        self.id = id
        self.url = url
        self.timestamp = timestamp
        self.status = status
        self.overall_score = overall_score
        self.findings = findings or []
        self.raw_dns = json.dumps(raw_dns) if isinstance(raw_dns, dict) else (raw_dns or "{}")
        self.raw_ssl = json.dumps(raw_ssl) if isinstance(raw_ssl, dict) else (raw_ssl or "{}")
        self.performance = json.dumps(performance) if isinstance(performance, dict) else (performance or "{}")
        self.headers = json.dumps(headers) if isinstance(headers, dict) else (headers or "{}")
        self.prospect_id = prospect_id


class MockFinding:
    """Mock audit finding model for pure service tests."""
    def __init__(
        self,
        id: str,
        title: str,
        severity: str = "medium",
        check_status: str = "WARNING",
        observed: str = "Issue observed",
        evidence: str = "Diagnostic trace",
        category: str = "reachability",
        http_status: int = None,
        response_time_ms: int = None
    ):
        self.id = id
        self.title = title
        self.severity = severity
        self.check_status = check_status
        self.observed = observed
        self.evidence = evidence
        self.category = category
        self.http_status = http_status
        self.response_time_ms = response_time_ms


# ==============================================================================
# A. RESOLVED FINDING
# ==============================================================================
def test_resolved_finding():
    """
    Older audit confirms a finding.
    Newer audit completes the same check and confirms it is fixed.
    Expected: resolved.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-ssl",
                title="SSL/TLS certificate has expired",
                severity="high",
                check_status="FAIL",
                evidence="Expired on Oct 9 2026",
                category="security"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-new-ssl",
                title="Valid SSL/TLS certificate verified",
                severity="info",
                check_status="PASS",
                evidence="Valid TLS certificate issued by Let's Encrypt with 89 days remaining.",
                category="security"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 1
    assert res["resolvedFindings"][0]["checkKey"] == "security.tls_certificate"
    assert res["resolvedFindings"][0]["olderFindingId"] == "f-old-ssl"
    assert res["resolvedFindings"][0]["newerFindingId"] == "f-new-ssl"
    assert "positive verification" in res["resolvedFindings"][0]["reason"].lower()
    assert len(res["persistentFindings"]) == 0
    assert len(res["newFindings"]) == 0
    assert len(res["inconclusiveFindings"]) == 0


# ==============================================================================
# B. NEW FINDING
# ==============================================================================
def test_new_finding():
    """
    Older audit completed the relevant check successfully.
    Newer audit detects a new issue with evidence.
    Expected: new.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-vp",
                title="Mobile viewport meta declaration verified",
                severity="info",
                check_status="PASS",
                category="performance"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-new-vp",
                title="Missing mobile viewport meta declaration",
                severity="medium",
                check_status="FAIL",
                evidence="Missing: <meta name='viewport'>",
                category="performance"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["newFindings"]) == 1
    assert res["newFindings"][0]["checkKey"] == "performance.mobile_viewport"
    assert res["newFindings"][0]["newerFindingId"] == "f-new-vp"
    assert len(res["resolvedFindings"]) == 0
    assert len(res["persistentFindings"]) == 0


# ==============================================================================
# C. PERSISTENT FINDING
# ==============================================================================
def test_persistent_finding():
    """
    The same issue is confirmed in both audits.
    Expected: persistent.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-spf",
                title="Missing Sender Policy Framework (SPF) DNS record",
                severity="medium",
                check_status="WARNING",
                evidence="TXT record: SPF tag not found",
                category="seo_meta"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-new-spf",
                title="Missing Sender Policy Framework (SPF) DNS record",
                severity="medium",
                check_status="WARNING",
                evidence="TXT record: SPF tag still not found",
                category="seo_meta"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["persistentFindings"]) == 1
    assert res["persistentFindings"][0]["checkKey"] == "seo_meta.dns_spf_record"
    assert res["persistentFindings"][0]["olderFindingId"] == "f-old-spf"
    assert res["persistentFindings"][0]["newerFindingId"] == "f-new-spf"
    assert len(res["resolvedFindings"]) == 0
    assert len(res["newFindings"]) == 0


# ==============================================================================
# D. NEWER AUDIT FAILURE
# ==============================================================================
def test_newer_audit_failure():
    """
    Older audit confirms an issue.
    Newer audit fails.
    Expected: inconclusive, NEVER resolved.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-dmarc",
                title="Missing DMARC email authentication policy",
                severity="low",
                check_status="WARNING",
                category="security"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="failed",  # Audit failed!
        findings=[]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 0  # CRITICAL: Must NOT be resolved!
    assert len(res["inconclusiveFindings"]) == 1
    assert res["inconclusiveFindings"][0]["checkKey"] == "security.dns_dmarc_record"
    assert "newer audit failed" in res["inconclusiveFindings"][0]["reason"].lower()
    assert res["isReliable"] is False
    assert res["executionStatus"] == "newer_failed"


# ==============================================================================
# E. SKIPPED CHECK
# ==============================================================================
def test_skipped_check_not_resolved():
    """
    Older audit confirms an issue.
    Newer audit skips the relevant check.
    Expected: inconclusive, never resolved.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-contact",
                title="No contact or inquiry link detected in navigation",
                severity="low",
                check_status="WARNING",
                category="conversion"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-new-contact-skipped",
                title="Internal Contact & Inquiry Pathways",
                severity="info",
                check_status="NOT_CHECKED",  # Explicitly skipped
                category="conversion"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 0
    assert len(res["inconclusiveFindings"]) == 1
    assert "skipped" in res["inconclusiveFindings"][0]["reason"].lower()


# ==============================================================================
# F. MISSING FINDING WITHOUT PASS EVIDENCE
# ==============================================================================
def test_missing_finding_without_pass_evidence():
    """
    Older audit contains an issue.
    Newer findings simply omit it, but no pass evidence is recorded.
    Expected: inconclusive (Never infer resolution from absence alone).
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-title",
                title="Missing or empty HTML page title tag",
                severity="medium",
                check_status="FAIL",
                category="seo_meta"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[]  # Finding simply missing, no PASS finding!
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 0
    assert len(res["inconclusiveFindings"]) == 1
    assert "omitted" in res["inconclusiveFindings"][0]["reason"].lower()


# ==============================================================================
# G. NEWER PARTIAL AUDIT
# ==============================================================================
def test_newer_partial_audit():
    """
    The newer audit contains some valid results but failed other checks.
    Expected: valid comparisons only for checks with sufficient evidence.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-old-dns",
                title="No DNS A/IPv4 records discovered",
                severity="high",
                check_status="FAIL",
                category="reachability"
            ),
            MockFinding(
                id="f-old-ssl",
                title="SSL/TLS certificate has expired",
                severity="high",
                check_status="FAIL",
                category="security"
            )
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            # DNS check succeeded and confirmed resolution
            MockFinding(
                id="f-new-dns-pass",
                title="DNS A/IPv4 resolution verified",
                severity="info",
                check_status="PASS",
                category="reachability"
            ),
            # SSL check experienced socket handshake error
            MockFinding(
                id="f-new-ssl-err",
                title="TLS connection handshake failed",
                severity="high",
                check_status="ERROR",
                category="security"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    # DNS check is confirmed resolved
    assert len(res["resolvedFindings"]) == 1
    assert res["resolvedFindings"][0]["checkKey"] == "reachability.dns_a_record"

    # SSL check is inconclusive because newer check failed with error
    assert len(res["inconclusiveFindings"]) == 1
    assert res["inconclusiveFindings"][0]["checkKey"] in ("security.tls_certificate", "security.tls_handshake")


# ==============================================================================
# H. OLD AUDIT INCOMPLETE
# ==============================================================================
def test_old_audit_incomplete():
    """
    The older audit never established whether a problem existed (failed older audit).
    Expected: do not confidently classify as new or resolved without sufficient evidence.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="failed",  # Older audit failed
        findings=[]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-new-desc",
                title="Missing meta description for search snippets",
                severity="low",
                check_status="WARNING",
                category="seo_meta"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    # Cannot be classified as confidently "new" because older baseline is incomplete
    assert len(res["newFindings"]) == 0
    assert len(res["inconclusiveFindings"]) == 1
    assert "older audit was incomplete" in res["inconclusiveFindings"][0]["reason"].lower()


# ==============================================================================
# I. DUPLICATE FINDINGS
# ==============================================================================
def test_duplicate_findings_do_not_inflate_counts():
    """
    Duplicate representations of the same check in an audit do not inflate counts.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        findings=[
            MockFinding(id="f-1", title="Missing meta description for search snippets", severity="low", check_status="WARNING", category="seo_meta"),
            MockFinding(id="f-2", title="Missing meta description for search snippets", severity="low", check_status="WARNING", category="seo_meta")
        ]
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        findings=[
            MockFinding(id="f-3", title="Meta description tag verified", severity="info", check_status="PASS", category="seo_meta")
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 1
    assert res["summary"]["resolvedCount"] == 1


# ==============================================================================
# J. FINDING MATCHING & NORMALIZATION
# ==============================================================================
def test_finding_matching_normalizes_case_and_whitespace():
    """
    Case differences and whitespace changes are normalized, but distinct issues remain distinct.
    """
    key1 = derive_check_key("Reachability", "  DNS A/IPv4 Record Resolution  ")
    key2 = derive_check_key("reachability", "dns a/ipv4 record resolution")
    key3 = derive_check_key("security", "ssl/tls certificate validity")

    assert key1 == key2
    assert key1 != key3


# ==============================================================================
# K. HTTP RESPONSE TIME & MEASUREMENT COMPARISONS
# ==============================================================================
def test_http_response_time_comparison():
    """
    Valid comparable values produce correct absolute change and percentage.
    850ms -> 420ms: -430ms (-50.6%), improved.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        performance={"ttfbMs": 850, "domReadyMs": 1200, "pageSizeKb": 50, "mobileViewportPresent": False}
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        performance={"ttfbMs": 420, "domReadyMs": 600, "pageSizeKb": 45, "mobileViewportPresent": True}
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    ttfb_m = next(m for m in res["measurements"] if m["key"] == "http_ttfb")
    assert ttfb_m["before"] == 850
    assert ttfb_m["after"] == 420
    assert ttfb_m["change"] == -430
    assert ttfb_m["changePercent"] == -50.6
    assert ttfb_m["direction"] == "improved"
    assert ttfb_m["status"] == "comparable"

    vp_m = next(m for m in res["measurements"] if m["key"] == "mobile_viewport")
    assert vp_m["before"] == "No"
    assert vp_m["after"] == "Yes"
    assert vp_m["direction"] == "improved"


# ==============================================================================
# L. ZERO PREVIOUS VALUE
# ==============================================================================
def test_zero_previous_value_no_division_by_zero():
    """
    When the before value is zero, no division-by-zero or NaN occurs.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        performance={"ttfbMs": 0}
    )

    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        performance={"ttfbMs": 300}
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    ttfb_m = next(m for m in res["measurements"] if m["key"] == "http_ttfb")
    assert ttfb_m["before"] == 0
    assert ttfb_m["after"] == 300
    assert ttfb_m["change"] == 300
    assert ttfb_m["changePercent"] is None  # Safely omitted
    assert ttfb_m["direction"] == "degraded"


# ==============================================================================
# M. DIFFERENT UNITS / INCOMPARABLE MEASUREMENTS
# ==============================================================================
def test_inconclusive_measurements_when_missing():
    older = MockAuditReport(id="aud-1", timestamp="2026-10-10 10:00:00 UTC", raw_ssl={})
    newer = MockAuditReport(id="aud-2", timestamp="2026-10-18 10:00:00 UTC", raw_ssl={"expiresDays": 30})

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    ssl_exp = next(m for m in res["measurements"] if m["key"] == "cert_expiry")
    assert ssl_exp["status"] == "inconclusive"


# ==============================================================================
# N. HTTP STATUS SEMANTICS
# ==============================================================================
def test_http_status_semantics():
    """
    500 -> 200 is an improvement; 200 -> 404 is a degradation.
    Arithmetic subtraction is NOT used as primary signal.
    """
    service = AuditComparisonService()

    comp_improved = service._compare_http_status_metric(500, 200, "completed", "completed")
    assert comp_improved["direction"] == "improved"
    assert comp_improved["change"] is None  # No raw arithmetic like -300

    comp_degraded = service._compare_http_status_metric(200, 404, "completed", "completed")
    assert comp_degraded["direction"] == "degraded"

    comp_unchanged = service._compare_http_status_metric(200, 200, "completed", "completed")
    assert comp_unchanged["direction"] == "unchanged"


# ==============================================================================
# O. TLS COMPARISON
# ==============================================================================
def test_tls_version_semantic_comparison():
    service = AuditComparisonService()

    # TLSv1.2 -> TLSv1.3 = improved
    res_up = service._compare_tls_version_metric("TLSv1.2", "TLSv1.3")
    assert res_up["direction"] == "improved"

    # TLSv1.3 -> TLSv1.0 = degraded
    res_down = service._compare_tls_version_metric("TLSv1.3", "TLSv1.0")
    assert res_down["direction"] == "degraded"

    # None -> None = inconclusive
    res_none = service._compare_tls_version_metric("None", "None")
    assert res_none["status"] == "inconclusive"


# ==============================================================================
# P. SAME AUDIT SELECTED TWICE
# ==============================================================================
def test_same_audit_selected_twice_rejected():
    older = MockAuditReport(id="aud-same", timestamp="2026-10-10 10:00:00 UTC")
    newer = MockAuditReport(id="aud-same", timestamp="2026-10-10 10:00:00 UTC")

    service = AuditComparisonService()
    with pytest.raises(ValueError) as excinfo:
        service.compare_audits(older, newer)
    assert "Cannot compare an audit with itself" in str(excinfo.value)


# ==============================================================================
# Q. DIFFERENT WEBSITES REJECTED
# ==============================================================================
def test_different_websites_rejected():
    older = MockAuditReport(id="aud-1", url="https://site-alpha.com", timestamp="2026-10-10 10:00:00 UTC")
    newer = MockAuditReport(id="aud-2", url="https://site-beta.com", timestamp="2026-10-18 10:00:00 UTC")

    service = AuditComparisonService()
    with pytest.raises(ValueError) as excinfo:
        service.compare_audits(older, newer)
    assert "different websites" in str(excinfo.value).lower()


# ==============================================================================
# S. TIMESTAMP ORDER
# ==============================================================================
def test_timestamp_order_validated():
    older = MockAuditReport(id="aud-1", timestamp="2026-10-20 10:00:00 UTC")
    newer = MockAuditReport(id="aud-2", timestamp="2026-10-10 10:00:00 UTC")  # Earlier than older!

    service = AuditComparisonService()
    with pytest.raises(ValueError) as excinfo:
        service.compare_audits(older, newer)
    assert "older audit" in str(excinfo.value).lower() and "more recent" in str(excinfo.value).lower()


# ==============================================================================
# API INTEGRATION TESTS (FastAPI Client)
# ==============================================================================
def test_api_compare_endpoint_flow(client):
    # 1. Create a prospect
    p_res = client.post("/api/prospects", json={
        "name": "Audit Compare Target",
        "websiteUrl": "https://comparetarget.org",
        "opportunityScore": 75
    })
    prospect_id = p_res.json()["id"]

    # 2. Run Audit 1 (with an issue)
    audit_1_data = {
        "url": "https://comparetarget.org",
        "timestamp": "2026-10-10 12:00:00 UTC",
        "status": "completed",
        "overallScore": 85,
        "rawDns": {"aRecord": "93.184.216.34", "mxRecord": "mail.comparetarget.org", "responseMs": 25, "nameservers": []},
        "rawSsl": {"valid": False, "issuer": "None", "expiresDays": -2, "tlsVersion": "None", "cipher": "None"},
        "performance": {"ttfbMs": 950, "domReadyMs": 1400, "pageSizeKb": 200, "mobileViewportPresent": False},
        "headers": {"server": "apache"},
        "findings": [
            {
                "id": "f-1-ssl",
                "title": "SSL/TLS certificate has expired",
                "severity": "high",
                "checkStatus": "FAIL",
                "observed": "Certificate expired 2 days ago.",
                "evidence": "Expired Oct 8 2026",
                "category": "security"
            }
        ]
    }

    with patch("backend.app.api.audits.execute_audit", return_value=audit_1_data), \
         patch("backend.app.services.ssrf_validator.validate_host_and_resolve", return_value=(True, ["93.184.216.34"], None)):
        res1 = client.post("/api/audits/run", json={"url": "https://comparetarget.org", "prospectId": prospect_id})
        assert res1.status_code == 201
        audit_1_id = res1.json()["id"]

    # 3. Run Audit 2 (SSL renewed & viewport added)
    audit_2_data = {
        "url": "https://comparetarget.org",
        "timestamp": "2026-10-18 12:00:00 UTC",
        "status": "completed",
        "overallScore": 55,
        "rawDns": {"aRecord": "93.184.216.34", "mxRecord": "mail.comparetarget.org", "responseMs": 18, "nameservers": []},
        "rawSsl": {"valid": True, "issuer": "DigiCert", "expiresDays": 90, "tlsVersion": "TLSv1.3", "cipher": "TLS_AES_256_GCM_SHA384"},
        "performance": {"ttfbMs": 350, "domReadyMs": 500, "pageSizeKb": 180, "mobileViewportPresent": True},
        "headers": {"server": "apache"},
        "findings": [
            {
                "id": "f-2-ssl",
                "title": "Valid SSL/TLS certificate verified",
                "severity": "info",
                "checkStatus": "PASS",
                "observed": "Valid TLS certificate issued by DigiCert with 90 days remaining.",
                "evidence": "DigiCert TLSv1.3",
                "category": "security"
            }
        ]
    }

    with patch("backend.app.api.audits.execute_audit", return_value=audit_2_data), \
         patch("backend.app.services.ssrf_validator.validate_host_and_resolve", return_value=(True, ["93.184.216.34"], None)):
        res2 = client.post("/api/audits/run", json={"url": "https://comparetarget.org", "prospectId": prospect_id})
        assert res2.status_code == 201
        audit_2_id = res2.json()["id"]

    # 4. Compare audits via API
    compare_res = client.post("/api/audits/compare", json={
        "older_audit_id": audit_1_id,
        "newer_audit_id": audit_2_id
    })

    assert compare_res.status_code == 200
    comp = compare_res.json()

    assert comp["olderAuditId"] == audit_1_id
    assert comp["newerAuditId"] == audit_2_id
    assert comp["isReliable"] is True
    assert comp["executionStatus"] == "both_completed"
    assert comp["summary"]["resolvedCount"] == 1
    assert comp["summary"]["newCount"] == 0
    assert len(comp["resolvedFindings"]) == 1
    assert comp["resolvedFindings"][0]["olderFindingId"] == "f-1-ssl"
    assert comp["resolvedFindings"][0]["newerFindingId"] == "f-2-ssl"

    # Verify measurement change
    ttfb = next(m for m in comp["measurements"] if m["key"] == "http_ttfb")
    assert ttfb["before"] == 950
    assert ttfb["after"] == 350
    assert ttfb["change"] == -600
    assert ttfb["direction"] == "improved"


def test_api_compare_missing_audit_returns_404(client):
    res = client.post("/api/audits/compare", json={
        "older_audit_id": "aud-nonexistent-1",
        "newer_audit_id": "aud-nonexistent-2"
    })
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_api_compare_same_audit_returns_400(client):
    res = client.post("/api/audits/compare", json={
        "older_audit_id": "aud-same",
        "newer_audit_id": "aud-same"
    })
    assert res.status_code == 400
    assert "cannot compare an audit with itself" in res.json()["detail"].lower()


# ==============================================================================
# PHASE 8.3.1 REGRESSION TESTS (Sections 2 - 6)
# ==============================================================================

def test_similar_titles_different_categories_do_not_collide():
    """
    Section 2.G: Similar titles in different categories must not be matched.
    A security issue mentioning 'contact' must not be matched with a conversion
    contact pathway check.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-sec-csrf-1",
                title="Contact form missing CSRF protection",
                severity="high",
                check_status="FAIL",
                category="security"
            )
        ]
    )
    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        findings=[
            MockFinding(
                id="f-html-contact-pass-2",
                title="Internal contact pathway detected",
                severity="info",
                check_status="PASS",
                category="conversion"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    # Security finding was omitted from newer audit without pass evidence -> inconclusive
    # It must NOT be marked resolved because of the conversion pass!
    assert len(res["resolvedFindings"]) == 0
    assert any(f["category"] == "security" and f["state"] == "inconclusive" for f in res["inconclusiveFindings"])


def test_empty_audit_reports_do_not_invent_findings():
    """
    Section 2.L: Empty audit reports must not invent findings or resolutions.
    """
    older = MockAuditReport(id="aud-1", timestamp="2026-10-10 10:00:00 UTC", findings=[])
    newer = MockAuditReport(id="aud-2", timestamp="2026-10-18 10:00:00 UTC", findings=[])

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 0
    assert len(res["newFindings"]) == 0
    assert len(res["persistentFindings"]) == 0
    assert len(res["inconclusiveFindings"]) == 0
    assert res["summary"]["totalFindingsEvaluated"] == 0


def test_cross_prospect_comparison_rejected_same_domain():
    """
    Section 2.J & Section 6: Audits belonging to different prospects must be rejected
    even if the recorded domain happens to match.
    """
    older = MockAuditReport(id="aud-1", url="https://example.com", prospect_id="p-alpha", timestamp="2026-10-10 10:00:00 UTC")
    newer = MockAuditReport(id="aud-2", url="https://example.com", prospect_id="p-beta", timestamp="2026-10-18 10:00:00 UTC")

    service = AuditComparisonService()
    with pytest.raises(ValueError) as excinfo:
        service.compare_audits(older, newer)
    assert "different prospects" in str(excinfo.value).lower()


def test_info_severity_without_pass_evidence_does_not_falsely_resolve():
    """
    Section 3: A finding with severity 'info' but without explicit PASS check_status
    must not be treated as a confirmed pass.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        findings=[
            MockFinding(
                id="f-timeout-1",
                title="Connection to target web server timed out",
                severity="high",
                check_status="FAIL",
                category="reachability"
            )
        ]
    )
    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        findings=[
            MockFinding(
                id="f-note-2",
                title="Connection diagnostic notice",
                severity="info",
                check_status="UNKNOWN",  # Not PASS!
                category="reachability"
            )
        ]
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    assert len(res["resolvedFindings"]) == 0
    assert len(res["inconclusiveFindings"]) >= 1


def test_cert_expiry_scenarios_comprehensive():
    """
    Section 4.A - 4.H: Comprehensive certificate expiry comparison scenarios.
    """
    service = AuditComparisonService()

    # Scenario A: Older valid, newer valid, natural passage of time (90 -> 80 days)
    comp_a = service._compare_cert_expiry_metric(before=90, after=80, older_valid=True, newer_valid=True)
    assert comp_a["direction"] == "neutral"
    assert comp_a["status"] == "comparable"

    # Scenario B: Older valid, newer invalid (30 -> -1 days)
    comp_b = service._compare_cert_expiry_metric(before=30, after=-1, older_valid=True, newer_valid=False)
    assert comp_b["direction"] == "degraded"

    # Scenario C: Older invalid, newer valid (-5 -> 90 days)
    comp_c = service._compare_cert_expiry_metric(before=-5, after=90, older_valid=False, newer_valid=True)
    assert comp_c["direction"] == "improved"

    # Scenario D: Both invalid/expired (-20 -> -5 days) -> MUST NOT BE IMPROVED
    comp_d = service._compare_cert_expiry_metric(before=-20, after=-5, older_valid=False, newer_valid=False)
    assert comp_d["direction"] == "unchanged"

    # Scenario E: Missing / malformed expiry
    comp_e = service._compare_cert_expiry_metric(before=None, after=90, older_valid=True, newer_valid=True)
    assert comp_e["status"] == "inconclusive"

    comp_e2 = service._compare_cert_expiry_metric(before="bad-int", after=90, older_valid=True, newer_valid=True)
    assert comp_e2["status"] == "not_comparable"

    # Scenario F: TLS diagnostic failed (can_compare=False)
    comp_f = service._compare_cert_expiry_metric(before=90, after=0, older_valid=True, newer_valid=False, can_compare=False)
    assert comp_f["status"] == "inconclusive"

    # Scenario G: Expired between audits (5 -> -2 days)
    comp_g = service._compare_cert_expiry_metric(before=5, after=-2, older_valid=True, newer_valid=False)
    assert comp_g["direction"] == "degraded"

    # Scenario H: Valid renewal (10 -> 90 days)
    comp_h = service._compare_cert_expiry_metric(before=10, after=90, older_valid=True, newer_valid=True)
    assert comp_h["direction"] == "improved"


def test_tls_version_unknown_string_not_comparable():
    """
    Section 4.I: Unknown TLS versions must not be ranked or compared arbitrarily.
    """
    service = AuditComparisonService()
    res = service._compare_tls_version_metric("TLSv1.3", "CustomCryptoV2")
    assert res["status"] == "not_comparable"
    assert "unrecognized" in res["reason"].lower()


def test_numeric_metric_negative_value_rejected():
    """
    Section 5: Negative latency or payload size must be rejected.
    """
    service = AuditComparisonService()
    res = service._compare_numeric_metric("http_ttfb", "TTFB", -50, 200, "ms", allow_negative=False)
    assert res["status"] == "not_comparable"
    assert "negative" in res["reason"].lower()


def test_dns_latency_inconclusive_when_resolution_failed():
    """
    Section 5: DNS latency must be inconclusive if DNS resolution failed in either audit.
    """
    older = MockAuditReport(
        id="aud-1",
        timestamp="2026-10-10 10:00:00 UTC",
        status="completed",
        raw_dns={"aRecord": "N/A", "responseMs": 0}  # Failed resolution
    )
    newer = MockAuditReport(
        id="aud-2",
        timestamp="2026-10-18 10:00:00 UTC",
        status="completed",
        raw_dns={"aRecord": "93.184.216.34", "responseMs": 25}
    )

    service = AuditComparisonService()
    res = service.compare_audits(older, newer)

    dns_metric = next(m for m in res["measurements"] if m["key"] == "dns_latency")
    assert dns_metric["status"] == "inconclusive"

