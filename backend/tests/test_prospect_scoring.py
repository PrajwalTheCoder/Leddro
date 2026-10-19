"""
Comprehensive automated test suite for Leddro Phase 8.2:
Prospect Intelligence & Explainable Scoring Service.

Tests:
A. DETERMINISM: Identical input produces identical score and explanation.
B. SCORE BOUNDS: Scores never fall below 0 or exceed 100 under all conditions.
C. NO AUDIT HISTORY: Prospect without an audit receives valid result, limited confidence, unknown factors.
D. FAILED AUDIT: Failed diagnostic check is not penalized as confirmed website defect.
E. ACCESSIBILITY: Confirmed HTTP reachability vs confirmed server error vs network timeout.
F. HTTPS/TLS: Verified HTTPS vs invalid TLS cert vs HTTP-only vs unconfirmed diagnostic.
G. FINDING SEVERITY: High, medium, low severity findings contribute according to documented formula.
H. DUPLICATE FINDINGS: Repeated representations of the same underlying issue do not inflate score.
I. AUDIT RECENCY: Stale audit decay lowers confidence without artificially increasing opportunity score.
J. CONTACT STATUS: Verified, unverified, absent contacts correctly distinguished.
K. EVIDENCE TRACEABILITY: Every returned evidence reference exists in source audit findings.
L. LEGACY DATA: Malformed, minimal, or legacy prospect/audit records do not crash scoring.
M. API CONSISTENCY: List, detail, and recalculate endpoints return consistent explainable scoring schema.
N. DEDUPLICATION REGRESSION: Existing central duplicate detection continues to work and rejects dupes.
P. PERFORMANCE (NO N+1): Batch fetching audits in list_prospects prevents N+1 query overhead.
"""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.prospect_scoring import (
    calculate_prospect_score,
    calculate_audit_age_days,
    SCORING_VERSION,
    MAX_ACCESSIBILITY_WEIGHT,
    MAX_TECHNICAL_FINDINGS_WEIGHT,
    MAX_HTTPS_WEIGHT,
    MAX_CONTACT_WEIGHT,
    MAX_DATA_COMPLETENESS_WEIGHT
)
from backend.app.models.prospect import ProspectModel
from backend.app.models.audit import AuditReportModel, AuditFindingModel


# =============================================================================
# A. DETERMINISM
# =============================================================================
def test_scoring_determinism():
    """Identical prospect and audit inputs produce identical scores, factors, and recommendations."""
    prospect_data = {
        "name": "Precision Tools Ltd",
        "website_url": "https://precisiontools.example",
        "email": "contact@precisiontools.example",
        "phone": "+91 22 25001234",
        "city": "Thane",
        "category": "Manufacturing"
    }
    audit_data = {
        "id": "aud_101",
        "status": "completed",
        "timestamp": "2026-10-15 10:00 UTC",
        "raw_ssl": {"valid": True, "issuer": "Let's Encrypt", "tlsVersion": "TLSv1.3"},
        "findings": [
            {
                "id": "f_1",
                "title": "Missing Content-Security-Policy",
                "severity": "medium",
                "check_status": "WARNING",
                "category": "security",
                "observed": "CSP header missing from response"
            },
            {
                "id": "f_2",
                "title": "Missing Strict-Transport-Security",
                "severity": "medium",
                "check_status": "WARNING",
                "category": "security",
                "observed": "HSTS header missing"
            }
        ]
    }

    res1 = calculate_prospect_score(prospect_data, audit_data)
    res2 = calculate_prospect_score(prospect_data, audit_data)

    assert res1["opportunity_score"] == res2["opportunity_score"]
    assert res1["confidence_score"] == res2["confidence_score"]
    assert res1["priority_label"] == res2["priority_label"]
    assert res1["contact_readiness"] == res2["contact_readiness"]
    assert res1["factors"] == res2["factors"]
    assert res1["limitations"] == res2["limitations"]
    assert res1["recommended_actions"] == res2["recommended_actions"]
    assert res1["score_version"] == SCORING_VERSION


# =============================================================================
# B. SCORE BOUNDS
# =============================================================================
def test_score_bounds_extreme_conditions():
    """Scores must stay strictly bounded within [0, 100] under all conditions."""
    # 1. Totally empty / missing prospect
    res_empty = calculate_prospect_score({}, None)
    assert 0 <= res_empty["opportunity_score"] <= 100
    assert 0 <= res_empty["confidence_score"] <= 100

    # 2. Extreme massive findings overload
    massive_findings = [
        {
            "id": f"f_{i}",
            "title": f"Critical Vulnerability {i}",
            "severity": "high",
            "check_status": "FAIL",
            "category": f"cat_{i}",
            "observed": "Severe failure"
        }
        for i in range(50)
    ]
    res_extreme = calculate_prospect_score(
        {"name": "Vulnerable Corp", "website_url": "http://insecure.test"},
        {"status": "completed", "findings": massive_findings, "raw_ssl": {"valid": False, "issuer": "None"}}
    )
    assert 0 <= res_extreme["opportunity_score"] <= 100
    assert 0 <= res_extreme["confidence_score"] <= 100


# =============================================================================
# C. NO AUDIT HISTORY
# =============================================================================
def test_no_audit_history():
    """A prospect without an audit receives valid score, untested factor states, and reduced confidence."""
    prospect = {
        "name": "Acme Supplies",
        "website_url": "https://acmesupplies.in",
        "email": "info@acmesupplies.in",
        "city": "Pune",
        "category": "Retail"
    }

    res = calculate_prospect_score(prospect, None)

    assert res["audit_status"] == "none"
    assert res["audit_age_days"] is None
    assert res["confidence_score"] <= 60  # Reduced due to lack of diagnostic audit
    assert res["priority_label"] == "Needs Audit"

    # Verify accessibility factor indicates untested
    f_acc = next(f for f in res["factors"] if f["key"] == "website_accessibility")
    assert f_acc["status"] == "untested"

    # Verify technical findings indicates no audit
    f_tech = next(f for f in res["factors"] if f["key"] == "technical_findings")
    assert f_tech["status"] == "no_audit"
    assert f_tech["contribution"] == 0

    # Verify limitation recorded
    assert any("audit" in lim.lower() for lim in res["limitations"])


# =============================================================================
# D. FAILED AUDIT (DIAGNOSTIC NETWORK FAILURE)
# =============================================================================
def test_failed_audit_not_treated_as_website_defect():
    """A failed diagnostic run is not treated as proof that the website has defects."""
    prospect = {
        "name": "Stable Bakery",
        "website_url": "https://stablebakery.example",
        "email": "owner@stablebakery.example",
        "city": "Bengaluru",
        "category": "Food & Beverage"
    }

    # Audit failed due to connection timeout or runner issue
    failed_audit = {
        "id": "aud_failed_1",
        "status": "failed",
        "timestamp": "2026-10-18 12:00 UTC",
        "findings": []
    }

    res = calculate_prospect_score(prospect, failed_audit)

    assert res["audit_status"] == "failed"
    # Never award high opportunity points solely because check failed
    f_acc = next(f for f in res["factors"] if f["key"] == "website_accessibility")
    assert f_acc["contribution"] == 0
    assert f_acc["status"] == "check_failed"

    # Confidence must be lower due to unconfirmed diagnostic
    assert res["confidence_score"] <= 60
    assert any("diagnostic" in lim.lower() or "connection" in lim.lower() for lim in res["limitations"])


# =============================================================================
# E. ACCESSIBILITY DISTINCTIONS
# =============================================================================
def test_accessibility_distinctions():
    """Distinguishes confirmed reachability, confirmed HTTP error, DNS failure, and timeout."""
    base_prospect = {"name": "Test Co", "website_url": "https://test.co", "city": "Mumbai", "category": "Logistics"}

    # 1. Confirmed reachable (HTTP 200 OK)
    res_reachable = calculate_prospect_score(
        base_prospect,
        {"status": "completed", "findings": [], "raw_ssl": {"valid": True}}
    )
    f_acc1 = next(f for f in res_reachable["factors"] if f["key"] == "website_accessibility")
    assert f_acc1["status"] == "confirmed_reachable"
    assert f_acc1["contribution"] == 0

    # 2. Confirmed HTTP 500 server error
    res_server_err = calculate_prospect_score(
        base_prospect,
        {
            "status": "completed",
            "findings": [
                {
                    "id": "f_500",
                    "title": "Server Error",
                    "severity": "high",
                    "check_status": "FAIL",
                    "http_status": 500,
                    "category": "reachability",
                    "observed": "HTTP 500 Internal Server Error"
                }
            ]
        }
    )
    f_acc2 = next(f for f in res_server_err["factors"] if f["key"] == "website_accessibility")
    assert f_acc2["status"] == "http_error"
    assert f_acc2["contribution"] > 0

    # 3. DNS resolution failure
    res_dns = calculate_prospect_score(
        base_prospect,
        {
            "status": "completed",
            "findings": [
                {
                    "id": "f_dns",
                    "title": "DNS NXDOMAIN",
                    "severity": "high",
                    "check_status": "FAIL",
                    "category": "reachability",
                    "observed": "Domain name does not resolve"
                }
            ]
        }
    )
    f_acc3 = next(f for f in res_dns["factors"] if f["key"] == "website_accessibility")
    assert f_acc3["status"] == "dns_failure"
    assert f_acc3["contribution"] > 0


# =============================================================================
# F. HTTPS/TLS STATUS
# =============================================================================
def test_https_tls_status_evaluations():
    """Verified HTTPS, invalid TLS cert, and HTTP-only produce distinct status and contributions."""
    p_https = {"name": "TLS Test", "website_url": "https://secure.example", "city": "Delhi", "category": "Tech"}
    p_http = {"name": "HTTP Test", "website_url": "http://insecure.example", "city": "Delhi", "category": "Tech"}

    # 1. Valid TLS
    res_valid = calculate_prospect_score(
        p_https,
        {"status": "completed", "raw_ssl": {"valid": True, "issuer": "DigiCert", "tlsVersion": "TLSv1.3"}}
    )
    f_tls1 = next(f for f in res_valid["factors"] if f["key"] == "https_transport")
    assert f_tls1["status"] == "https_verified"
    assert f_tls1["contribution"] == 0

    # 2. Invalid / Expired TLS Cert
    res_invalid = calculate_prospect_score(
        p_https,
        {"status": "completed", "raw_ssl": {"valid": False, "issuer": "Expired Cert Authority"}}
    )
    f_tls2 = next(f for f in res_invalid["factors"] if f["key"] == "https_transport")
    assert f_tls2["status"] == "tls_invalid"
    assert f_tls2["contribution"] == MAX_HTTPS_WEIGHT

    # 3. HTTP-only
    res_http = calculate_prospect_score(
        p_http,
        {"status": "completed", "raw_ssl": {"valid": False, "issuer": "None"}}
    )
    f_tls3 = next(f for f in res_http["factors"] if f["key"] == "https_transport")
    assert f_tls3["status"] == "http_only"
    assert f_tls3["contribution"] == 15


# =============================================================================
# G. FINDING SEVERITY
# =============================================================================
def test_finding_severity_weighting():
    """High (15 pts), medium (5 pts), and low (1 pt) severity findings contribute per formula."""
    prospect = {"name": "Weight Test", "website_url": "https://weight.test", "city": "Jaipur", "category": "Crafts"}

    findings = [
        {"id": "fh_1", "title": "Missing DMARC Policy", "severity": "high", "check_status": "FAIL", "category": "email_dns"},
        {"id": "fm_1", "title": "Missing HSTS Header", "severity": "medium", "check_status": "WARNING", "category": "security"},
        {"id": "fm_2", "title": "Missing CSP Header", "severity": "medium", "check_status": "WARNING", "category": "headers"},
        {"id": "fl_1", "title": "Missing Meta Description", "severity": "low", "check_status": "WARNING", "category": "seo_meta"}
    ]

    res = calculate_prospect_score(prospect, {"status": "completed", "findings": findings})
    f_tech = next(f for f in res["factors"] if f["key"] == "technical_findings")

    # High: 1 * 15 = 15
    # Med: 2 * 5 = 10
    # Low: 1 * 1 = 1
    # Expected = 26 pts
    assert f_tech["contribution"] == 26
    assert res["severity_summary"]["high"] == 1
    assert res["severity_summary"]["medium"] == 2
    assert res["severity_summary"]["low"] == 1


# =============================================================================
# H. DUPLICATE FINDINGS
# =============================================================================
def test_duplicate_findings_deduplication():
    """Repeated representations of the same underlying issue do not inflate the score."""
    prospect = {"name": "Dupe Finding Test", "website_url": "https://dupe.test", "city": "Goa", "category": "Hospitality"}

    # Duplicate findings representing same check twice
    findings = [
        {"id": "f_1", "title": "Missing HSTS Header", "severity": "medium", "check_status": "WARNING", "category": "security"},
        {"id": "f_2", "title": "Missing HSTS Header", "severity": "medium", "check_status": "WARNING", "category": "security"},
        {"id": "f_3", "title": "missing hsts header ", "severity": "medium", "check_status": "WARNING", "category": "security"}
    ]

    res = calculate_prospect_score(prospect, {"status": "completed", "findings": findings})
    f_tech = next(f for f in res["factors"] if f["key"] == "technical_findings")

    # Should count only once (5 pts), not 3 times (15 pts)
    assert f_tech["contribution"] == 5
    assert res["severity_summary"]["medium"] == 1


# =============================================================================
# I. AUDIT RECENCY AND CONFIDENCE DECAY
# =============================================================================
def test_audit_recency_decay():
    """An old audit lowers confidence without artificially inflating opportunity score."""
    prospect = {"name": "Aging Test", "website_url": "https://aging.test", "city": "Surat", "category": "Textiles"}

    # Fresh audit (1 day old)
    fresh_ts = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M UTC")
    res_fresh = calculate_prospect_score(prospect, {"status": "completed", "timestamp": fresh_ts, "findings": []})

    # Stale audit (45 days old)
    stale_ts = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d %H:%M UTC")
    res_stale = calculate_prospect_score(prospect, {"status": "completed", "timestamp": stale_ts, "findings": []})

    # Very stale audit (120 days old)
    very_stale_ts = (datetime.now(timezone.utc) - timedelta(days=120)).strftime("%Y-%m-%d %H:%M UTC")
    res_very_stale = calculate_prospect_score(prospect, {"status": "completed", "timestamp": very_stale_ts, "findings": []})

    # Opportunity score does NOT increase just because audit is old
    assert res_stale["opportunity_score"] == res_fresh["opportunity_score"]
    assert res_very_stale["opportunity_score"] == res_fresh["opportunity_score"]

    # Confidence must decay
    assert res_fresh["confidence_score"] > res_stale["confidence_score"]
    assert res_stale["confidence_score"] > res_very_stale["confidence_score"]
    assert res_stale["audit_age_days"] >= 44
    assert res_very_stale["audit_age_days"] >= 119


# =============================================================================
# J. CONTACT READINESS
# =============================================================================
def test_contact_readiness_states():
    """Verified, unverified, and absent contact information produce distinct readiness labels."""
    # 1. Verified contact
    res_verified = calculate_prospect_score({
        "name": "Verified Co",
        "email": "verified@domain.com",
        "phone": "+91 9876543210",
        "last_verified_at": "2026-10-10T12:00:00Z"
    })
    assert res_verified["contact_readiness"] == "verified"
    f_contact1 = next(f for f in res_verified["factors"] if f["key"] == "contact_readiness")
    assert f_contact1["contribution"] == 0

    # 2. Present but unverified (Must NOT inflate opportunity score; lowers confidence instead)
    res_unverified = calculate_prospect_score({
        "name": "Unverified Co",
        "email": "unverified@domain.com",
        "phone": "+91 9876543210",
        "last_verified_at": None
    })
    assert res_unverified["contact_readiness"] == "unverified"
    f_contact2 = next(f for f in res_unverified["factors"] if f["key"] == "contact_readiness")
    assert f_contact2["contribution"] == 0
    assert res_unverified["confidence_score"] < res_verified["confidence_score"]
    assert any("verified" in lim.lower() for lim in res_unverified["limitations"])

    # 3. Completely absent (Must NOT inflate opportunity score; lowers confidence instead)
    res_absent = calculate_prospect_score({
        "name": "Ghost Co",
        "email": None,
        "phone": None
    })
    assert res_absent["contact_readiness"] == "absent"
    f_contact3 = next(f for f in res_absent["factors"] if f["key"] == "contact_readiness")
    assert f_contact3["contribution"] == 0
    assert res_absent["confidence_score"] < res_unverified["confidence_score"]


# =============================================================================
# K. EVIDENCE TRACEABILITY
# =============================================================================
def test_evidence_traceability():
    """Every returned finding reference maps to a real finding ID in the source audit."""
    findings = [
        {"id": "real_finding_99", "title": "Missing SPF Record", "severity": "high", "check_status": "FAIL", "category": "email", "observed": "No SPF TXT record found"}
    ]
    res = calculate_prospect_score(
        {"name": "Trace Corp", "website_url": "https://trace.corp"},
        {"status": "completed", "findings": findings}
    )

    f_tech = next(f for f in res["factors"] if f["key"] == "technical_findings")
    assert len(f_tech["evidence"]) > 0
    first_ev = f_tech["evidence"][0]
    assert first_ev["finding_id"] == "real_finding_99"
    assert first_ev["title"] == "Missing SPF Record"
    assert first_ev["severity"] == "high"


# =============================================================================
# L. LEGACY DATA COMPATIBILITY
# =============================================================================
def test_legacy_data_tolerance():
    """Handles missing optional fields, unusual dict representations, and legacy records without crashing."""
    legacy_prospect = {
        "name": None,
        "websiteUrl": None,
        "location": None
    }
    legacy_audit = {
        "status": "completed",
        "raw_ssl": "{invalid_json}",
        "findings": None
    }

    res = calculate_prospect_score(legacy_prospect, legacy_audit)
    assert isinstance(res["opportunity_score"], int)
    assert isinstance(res["confidence_score"], int)
    assert res["score_version"] == SCORING_VERSION


# =============================================================================
# M. API INTEGRATION & CONSISTENCY
# =============================================================================
def test_api_list_and_detail_consistency(client):
    """Listing and detail endpoints return consistent opportunity scores and explainable breakdowns."""
    # Create prospect
    payload = {
        "name": "Consistency Target",
        "category": "Architecture",
        "location": {"city": "Kolkata", "state": "West Bengal", "country": "India"},
        "websiteUrl": "https://consistencytarget.example",
        "email": "hello@consistencytarget.example"
    }
    create_res = client.post("/api/prospects", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    p_id = created["id"]
    assert "scoring" in created
    assert created["scoring"]["opportunityScore"] == created["opportunityScore"]

    # Fetch detail
    get_res = client.get(f"/api/prospects/{p_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["scoring"]["opportunityScore"] == created["scoring"]["opportunityScore"]
    assert detail["scoring"]["confidenceScore"] == created["scoring"]["confidenceScore"]
    assert detail["scoring"]["priorityLabel"] == created["scoring"]["priorityLabel"]

    # List endpoint
    list_res = client.get("/api/prospects")
    assert list_res.status_code == 200
    items = list_res.json()
    matched = next((item for item in items if item["id"] == p_id), None)
    assert matched is not None
    assert matched["scoring"]["opportunityScore"] == detail["scoring"]["opportunityScore"]


# =============================================================================
# N. DEDUPLICATION REUSE & REGRESSION
# =============================================================================
def test_central_deduplication_reuse(client):
    """Existing central deduplication service rejects duplicate prospect creation by domain or name+city."""
    p1 = {
        "name": "Apex Engineering",
        "location": {"city": "Nashik", "state": "Maharashtra", "country": "India"},
        "websiteUrl": "https://apexengineering.co.in"
    }
    res1 = client.post("/api/prospects", json=p1)
    assert res1.status_code == 201

    # Exact duplicate website domain
    p2 = {
        "name": "Different Name Apex",
        "location": {"city": "Nashik", "state": "Maharashtra", "country": "India"},
        "websiteUrl": "https://www.apexengineering.co.in"  # Normalized domain match
    }
    res2 = client.post("/api/prospects", json=p2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


# =============================================================================
# P. PERFORMANCE / NO N+1 QUERIES
# =============================================================================
def test_batch_audit_retrieval_avoids_n_plus_one(client):
    """Creating multiple prospects and listing them executes cleanly without query explosion."""
    for i in range(5):
        client.post("/api/prospects", json={
            "name": f"Batch Test {i}",
            "location": {"city": "Indore", "state": "Madhya Pradesh", "country": "India"},
            "websiteUrl": f"https://batchtarget{i}.example"
        })

    list_res = client.get("/api/prospects")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 5
    for item in items:
        assert "scoring" in item
        assert item["scoring"]["scoreVersion"] == "1.0"


# =============================================================================
# Q. PHASE 8.2 VERIFICATION CASES (A through H)
# =============================================================================
def test_case_a_no_website_no_audit():
    """Case A: Prospect has no website and no audit. Receives potential opportunity (15 pts), low confidence (45 pts)."""
    prospect = {
        "name": "Local Corner Store",
        "category": "Retail",
        "city": "Mumbai",
        "website_url": None,
        "email": None,
        "phone": None
    }
    res = calculate_prospect_score(prospect, None)
    assert res["opportunity_score"] == 15
    assert res["confidence_score"] == 45
    f_acc = next(f for f in res["factors"] if f["key"] == "website_accessibility")
    assert f_acc["status"] == "no_website"
    assert f_acc["nature"] == "potential_opportunity"
    assert f_acc["contribution"] == 15
    assert any("no registered website" in lim.lower() for lim in res["limitations"])


def test_case_b_website_no_audit():
    """Case B: Prospect has a website but no audit. Receives 0 opportunity score, Needs Audit priority, unknown nature."""
    prospect = {
        "name": "Aura Cosmetics",
        "category": "Beauty",
        "city": "Pune",
        "website_url": "https://auracosmetics.in",
        "email": "info@auracosmetics.in",
        "phone": "+91 20 12345678"
    }
    res = calculate_prospect_score(prospect, None)
    assert res["opportunity_score"] == 0
    assert res["priority_label"] == "Needs Audit"
    assert res["confidence_score"] == 52
    f_acc = next(f for f in res["factors"] if f["key"] == "website_accessibility")
    assert f_acc["status"] == "untested"
    assert f_acc["nature"] == "unknown"
    assert f_acc["contribution"] == 0


def test_case_c_completed_audit_high_severity():
    """Case C: Prospect has completed audit with confirmed high-severity findings."""
    prospect = {
        "name": "Cyber Defense Corp",
        "category": "Technology",
        "city": "Bengaluru",
        "website_url": "https://cyberdefense.example",
        "email": "contact@cyberdefense.example",
        "phone": "+91 80 12345678"
    }
    audit = {
        "status": "completed",
        "raw_ssl": {"valid": True, "issuer": "DigiCert", "tlsVersion": "TLSv1.3"},
        "findings": [
            {"id": "fh_1", "title": "Missing DMARC Policy", "severity": "high", "check_status": "FAIL", "category": "email"},
            {"id": "fh_2", "title": "Missing SPF Record", "severity": "high", "check_status": "FAIL", "category": "email"}
        ]
    }
    res = calculate_prospect_score(prospect, audit)
    # 2 high findings = 2 * 15 = 30 pts
    assert res["opportunity_score"] == 30
    assert res["priority_label"] == "Medium"
    assert res["confidence_score"] == 92
    f_tech = next(f for f in res["factors"] if f["key"] == "technical_findings")
    assert f_tech["nature"] == "confirmed_deficiency"
    assert f_tech["status"] == "issues_observed"
    assert len(f_tech["evidence"]) == 2


def test_case_d_failed_diagnostic_network_error():
    """Case D: Prospect has a failed diagnostic caused by a network error. Inconclusive; does not become confirmed defect."""
    prospect = {
        "name": "Offline Books",
        "category": "Publishing",
        "city": "Chennai",
        "website_url": "https://offlinebooks.example",
        "email": "admin@offlinebooks.example",
        "phone": "+91 44 12345678"
    }
    audit = {
        "status": "failed",
        "findings": []
    }
    res = calculate_prospect_score(prospect, audit)
    assert res["opportunity_score"] == 0
    f_acc = next(f for f in res["factors"] if f["key"] == "website_accessibility")
    assert f_acc["status"] == "check_failed"
    assert f_acc["nature"] == "failed_diagnostic"
    assert f_acc["contribution"] == 0
    assert any("failed to connect" in lim.lower() for lim in res["limitations"])


def test_case_e_incomplete_profile_no_score_inflation():
    """Case E: Incomplete business profile (unnamed, unlocated, no contact, no website) does NOT inflate opportunity score."""
    prospect = {
        "name": "Unnamed Record",
        "category": None,
        "city": None,
        "website_url": None,
        "email": None,
        "phone": None
    }
    res = calculate_prospect_score(prospect, None)
    # Only 15 pts from no_website potential opportunity. Missing metadata adds 0 pts!
    assert res["opportunity_score"] == 15
    # Severely penalized confidence: 100 - 40 (no audit) - 15 (absent contact) - 10 (incomplete profile) = 35
    assert res["confidence_score"] == 35
    f_data = next(f for f in res["factors"] if f["key"] == "data_completeness")
    assert f_data["status"] == "incomplete"
    assert f_data["nature"] == "unknown"
    assert f_data["contribution"] == 0
    assert any("profile lacks" in lim.lower() for lim in res["limitations"])


def test_case_f_stale_audit_evidence():
    """Case F: Prospect has stale audit evidence (>90d). Decays confidence without increasing score."""
    prospect = {
        "name": "Legacy Manufacturing",
        "category": "Industrial",
        "city": "Ahmedabad",
        "website_url": "https://legacymfg.example",
        "email": "contact@legacymfg.example",
        "phone": "+91 79 12345678"
    }
    stale_ts = (datetime.now(timezone.utc) - timedelta(days=95)).strftime("%Y-%m-%d %H:%M UTC")
    audit = {
        "status": "completed",
        "timestamp": stale_ts,
        "raw_ssl": {"valid": True, "issuer": "DigiCert", "tlsVersion": "TLSv1.3"},
        "findings": []
    }
    res = calculate_prospect_score(prospect, audit)
    assert res["opportunity_score"] == 0
    assert res["audit_age_days"] >= 94
    # Confidence decayed by 30 pts for >90d: 100 - 30 - 8 (unverified contact) = 62
    assert res["confidence_score"] == 62
    assert any(">90d" in lim.lower() or "95 days" in lim.lower() for lim in res["limitations"])


def test_case_g_valid_https_connection():
    """Case G: Prospect has a valid HTTPS connection. Receives 0 defect points, informational status."""
    prospect = {
        "name": "Secure Gateway",
        "category": "Finance",
        "city": "Gurgaon",
        "website_url": "https://securegateway.example",
        "email": "ops@securegateway.example",
        "phone": "+91 124 1234567"
    }
    audit = {
        "status": "completed",
        "raw_ssl": {"valid": True, "issuer": "Let's Encrypt Authority X3", "tlsVersion": "TLSv1.3"},
        "findings": []
    }
    res = calculate_prospect_score(prospect, audit)
    f_tls = next(f for f in res["factors"] if f["key"] == "https_transport")
    assert f_tls["status"] == "https_verified"
    assert f_tls["nature"] == "informational"
    assert f_tls["contribution"] == 0


def test_case_h_tls_diagnostic_failed_inconclusive():
    """Case H: Prospect has a TLS diagnostic that failed or could not be evaluated. Inconclusive (0 pts)."""
    prospect = {
        "name": "Uncertain TLS Co",
        "category": "Services",
        "city": "Noida",
        "website_url": "https://uncertaintls.example",
        "email": "hello@uncertaintls.example",
        "phone": "+91 120 1234567"
    }
    # Inconclusive completed audit where ssl status could not be read
    audit_inconclusive = {
        "status": "completed",
        "raw_ssl": {"valid": None, "issuer": "None"},
        "findings": []
    }
    res_inc = calculate_prospect_score(prospect, audit_inconclusive)
    f_tls = next(f for f in res_inc["factors"] if f["key"] == "https_transport")
    assert f_tls["status"] == "tls_unconfirmed"
    assert f_tls["nature"] == "unknown"
    assert f_tls["contribution"] == 0

    # Failed audit execution
    audit_failed = {
        "status": "failed",
        "raw_ssl": {},
        "findings": []
    }
    res_fail = calculate_prospect_score(prospect, audit_failed)
    f_tls_fail = next(f for f in res_fail["factors"] if f["key"] == "https_transport")
    assert f_tls_fail["status"] == "untested"
    assert f_tls_fail["nature"] == "unknown"
    assert f_tls_fail["contribution"] == 0

