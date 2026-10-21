"""
Reality Check 3.0 regression tests.

All data here is a synthetic TEST FIXTURE (or a failure shape observed in earlier validation);
nothing performs live network lookups or sends email.
"""
import asyncio
import json
import sqlite3

import pytest

from backend.app.services.identity_verifier import verify_business_identity
from backend.app.services import contact_provenance as cp
from backend.app.services.social_matcher import evaluate_social_profile_match
from backend.app.services.prospect_scoring import calculate_prospect_score
from backend.app.ai.prompts import build_user_prompt


# ---------------------------------------------------------------- identity
class TestIdentity:
    def test_aggregator_domain_is_conflicting(self):
        r = verify_business_identity("Sarvi Restaurant", {"city": "Mumbai"}, "http://www.justdial.com")
        assert r["status"] == "conflicting"
        assert r["is_aggregator"] is True

    def test_discontinued_business_site_is_conflicting(self):
        r = verify_business_identity("Cafe Universal", {"city": "Mumbai"}, "https://cafe-universal.business.site")
        assert r["status"] == "conflicting"
        assert r["is_discontinued"] is True

    def test_name_similarity_never_yields_verified(self):
        r = verify_business_identity("Mint Morsel Restaurant", {"city": "Mumbai"}, "https://mintmorsel.co.in")
        assert r["status"] == "likely_match"
        assert r["status"] != "verified"

    def test_unrelated_domain_is_uncertain_not_confirmed(self):
        r = verify_business_identity("Krabi Multi-cuisine Restaurant", {"city": "Navi Mumbai"}, "https://silveroakuran.com")
        assert r["status"] == "uncertain"
        assert "silveroakuran.com" in r["conflicting_domains"]

    def test_missing_website_is_not_claimed_as_confirmed_absence(self):
        r = verify_business_identity("Kanchan Restaurant", {"city": "Navi Mumbai"}, None)
        assert r["status"] == "not_found"
        assert r["claim"] == "no_website_discovered"
        assert r["confidence_score"] <= 0.5
        assert "does not confirm" in " ".join(r["reasons"]).lower()


# ----------------------------------------------------------------- contacts
@pytest.fixture
def mx_ok(monkeypatch):
    monkeypatch.setattr(cp, "verify_email_mx", lambda email: True)


class TestContactProvenance:
    def test_blogger_address_is_conflicting(self, mx_ok):
        r = cp.classify_contact_provenance("thegobblediaries@gmail.com", "MINTMORSEL RESTAURANT", "search_snippet")
        assert r["status"] == "conflicting"

    def test_aggregator_support_is_conflicting(self, mx_ok):
        r = cp.classify_contact_provenance("support@zomato.com", "Mint Morsel", "search_snippet")
        assert r["status"] == "conflicting"

    def test_search_snippet_stays_unverified(self, mx_ok):
        r = cp.classify_contact_provenance("owner@somewhere-else.com", "Cafe Mondegar", "search_snippet")
        assert r["status"] == "unverified"
        assert r["mailbox_confirmed"] is False

    def test_mx_never_confirms_mailbox(self, mx_ok):
        r = cp.classify_contact_provenance("hello@cafemondegar.com", "Cafe Mondegar", "official_website",
                                           identity_status="verified")
        assert r["mx_verified"] is True
        assert r["mailbox_confirmed"] is False

    def test_official_source_downgraded_when_website_identity_unconfirmed(self, mx_ok):
        r = cp.classify_contact_provenance("info@other.com", "Cafe Mondegar", "official_website",
                                           identity_status="conflicting")
        assert r["status"] == "unverified"
        r2 = cp.classify_contact_provenance("info@other.com", "Cafe Mondegar", "official_website",
                                            identity_status="uncertain")
        assert r2["status"] == "unverified"

    def test_directory_is_third_party_candidate_not_official(self, mx_ok):
        r = cp.classify_contact_provenance("hello@cafemondegar.com", "Cafe Mondegar", "directory",
                                           source_provider="osm")
        assert r["status"] == "third_party_candidate"

    def test_imported_email_not_labelled_official(self, mx_ok):
        r = cp.classify_contact_provenance("hello@cafemondegar.com", "Cafe Mondegar", "imported",
                                           source_provider="csv_import")
        assert r["status"] != "official_source"

    def test_seats_username_not_flagged_as_blogger(self, mx_ok):
        # 'seats' contains 'eats'; must not be treated as a food-blogger keyword.
        assert cp.is_blogger_or_reviewer_email("seats@grandhotel.com", "Grand Hotel") is False


# ------------------------------------------------------------------- social
class TestSocial:
    def test_fan_page_is_incorrect(self):
        r = evaluate_social_profile_match("instagram", "https://instagram.com/mumbaifoodlovers_fanpage", "Creeda Cafe")
        assert r["match_status"] == "incorrect_match"

    def test_business_with_club_in_name_not_marked_fan_page(self):
        r = evaluate_social_profile_match("instagram", "https://instagram.com/bombaysailingclub", "Bombay Sailing Club")
        assert r["match_status"] != "incorrect_match"

    def test_reciprocal_requires_evidence_flag(self):
        r = evaluate_social_profile_match("instagram", "https://instagram.com/creedacafe", "Creeda Board Game Cafe",
                                          reciprocal_link_found=True, official_website="https://creeda.in")
        assert r["match_status"] == "reciprocal_match"

    def test_unrelated_handle_is_only_uncertain(self):
        r = evaluate_social_profile_match("facebook", "https://facebook.com/unrelated_user", "Creeda Cafe")
        assert r["match_status"] == "uncertain_match"

    def test_not_found_is_not_proof_of_absence(self):
        r = evaluate_social_profile_match("instagram", None, "Creeda Cafe")
        assert r["match_status"] == "not_found"
        assert r["confidence_score"] <= 0.5
        assert "does not prove" in r["evidence"]


# ------------------------------------------------------------------ scoring
def _audit(findings, status="completed"):
    return {"status": status, "timestamp": None, "findings": findings,
            "raw_ssl": {"valid": True, "issuer": "CA", "tlsVersion": "TLSv1.3"}}


def _finding(fid, title, sev="high", cat="technical", status="FAIL", http=None, observed=""):
    f = {"id": fid, "title": title, "severity": sev, "category": cat, "check_status": status, "observed": observed}
    if http:
        f["http_status"] = http
    return f


BASE = {"name": "Test Bistro", "category": "Restaurant", "city": "Mumbai",
        "website_url": "https://testbistro.example", "email": None, "phone": None}


class TestScoringInvariants:
    def test_conflicting_identity_excludes_findings_and_lowers_confidence(self):
        audit = _audit([_finding("f1", "Missing viewport", "high"), _finding("f2", "HTTP 500", "high", "reachability", http=500)])
        trusted = calculate_prospect_score({**BASE, "identity_status": "verified"}, audit)
        conflicting = calculate_prospect_score({**BASE, "identity_status": "conflicting"}, audit)
        assert conflicting["opportunity_score"] == 0
        assert conflicting["opportunity_score"] < trusted["opportunity_score"]
        assert conflicting["confidence_score"] < trusted["confidence_score"]
        assert any("identity" in l.lower() for l in conflicting["limitations"])

    def test_uncertain_identity_lowers_confidence(self):
        audit = _audit([])
        a = calculate_prospect_score({**BASE, "identity_status": "verified"}, audit)
        b = calculate_prospect_score({**BASE, "identity_status": "uncertain"}, audit)
        assert b["confidence_score"] < a["confidence_score"]

    def test_missing_audit_adds_no_defect_points(self):
        r = calculate_prospect_score({**BASE, "identity_status": "likely_match"}, None)
        assert r["opportunity_score"] == 0
        assert r["priority_label"] == "Needs Audit"

    def test_missing_contact_never_raises_opportunity(self):
        with_contact = calculate_prospect_score({**BASE, "email": "a@testbistro.example", "phone": "+912212345678"}, _audit([]))
        without = calculate_prospect_score(BASE, _audit([]))
        assert without["opportunity_score"] == with_contact["opportunity_score"]
        assert without["confidence_score"] < with_contact["confidence_score"]

    def test_transient_dns_resolver_failure_is_not_a_confirmed_defect(self):
        f = _finding("f-dns", "DNS resolver timeout", "high", "reachability",
                     observed="DNS lookup timed out (resolver error), record state unknown")
        r = calculate_prospect_score(BASE, _audit([f]))
        statuses = {x["key"]: x["status"] for x in r["factors"]}
        assert statuses["website_accessibility"] != "dns_failure"

    def test_contact_trust_levels_not_treated_identically(self):
        audit = _audit([])
        base = {**BASE, "email": "x@testbistro.example", "phone": "+912212345678", "identity_status": "verified"}
        official = calculate_prospect_score({**base, "contact_provenance": {"status": "official_source"}}, audit)
        snippet = calculate_prospect_score({**base, "contact_provenance": {"status": "unverified"}}, audit)
        conflicting = calculate_prospect_score({**base, "contact_provenance": {"status": "conflicting"}}, audit)
        assert official["confidence_score"] > snippet["confidence_score"] > conflicting["confidence_score"]
        assert official["contact_trust"] == "official_source"

    def test_duplicate_findings_do_not_inflate(self):
        one = _audit([_finding("a", "Missing viewport", "high")])
        many = _audit([_finding(f"a{i}", "Missing viewport", "high") for i in range(10)])
        assert calculate_prospect_score(BASE, one)["opportunity_score"] == calculate_prospect_score(BASE, many)["opportunity_score"]

    def test_scores_bounded(self):
        findings = [_finding(f"h{i}", f"High issue {i}", "high", status="FAIL") for i in range(30)]
        findings += [_finding("e", "HTTP 500", "high", "reachability", http=500)]
        r = calculate_prospect_score(BASE, _audit(findings))
        assert 0 <= r["opportunity_score"] <= 100
        assert 10 <= r["confidence_score"] <= 100


# ----------------------------------------------------------- AI prompt facts
PROSPECT = {"name": "Test Bistro", "category": "Restaurant", "city": "Mumbai", "state": "MH", "country": "India",
            "website_url": "https://testbistro.example", "website_status": "active", "phone": None,
            "email": "owner@testbistro.example", "source_provider": "osm", "tags": [], "notes": ""}
AUDIT = {"url": "https://testbistro.example", "status": "completed", "overall_score": 60,
         "findings": [{"id": "f_1", "title": "Missing viewport", "severity": "medium", "observed": "x",
                       "evidence": "y", "why_it_matters": "z", "category": "seo"}]}
DEV = {"name": "Dev", "title": "Consultant", "services": "Web", "email": "d@example.com"}


def _prompt(prospect, audit=AUDIT, purpose="website_improvement"):
    return build_user_prompt(prospect, audit, DEV, purpose, "professional")


class TestDraftIntegrity:
    def test_verified_site_with_findings_includes_them(self):
        p = _prompt({**PROSPECT, "identity_status": "verified"})
        assert "https://testbistro.example" in p and "f_1" in p

    def test_incomplete_audit_does_not_invent_findings(self):
        p = _prompt({**PROSPECT, "identity_status": "likely_match"}, audit=None)
        assert "No website audit report exists" in p and "f_1" not in p

    def test_no_website_not_claimed_absent(self):
        p = _prompt({**PROSPECT, "website_url": None, "identity_status": "not_found"}, audit=None,
                    purpose="new_website_proposal")
        assert "None listed" in p
        assert "Do NOT state definitively that they have no website" in p

    def test_conflicting_website_url_and_audit_withheld(self):
        p = _prompt({**PROSPECT, "identity_status": "conflicting"})
        assert "https://testbistro.example" not in p
        assert "WITHHELD" in p and "f_1" not in p

    def test_uncertain_email_is_labelled_unverified(self):
        p = _prompt({**PROSPECT, "identity_status": "verified", "contact_provenance": {"status": "unverified"}})
        assert "trust level: unverified" in p and "mailbox existence NOT confirmed" in p

    def test_uncertain_social_not_listed_as_business_profile(self):
        socials = {"instagram": {"url": "https://instagram.com/x", "match_status": "uncertain_match"},
                   "facebook": {"url": "https://facebook.com/testbistro", "match_status": "strong_match"}}
        p = _prompt({**PROSPECT, "identity_status": "verified", "social_profiles": socials})
        assert "instagram.com/x" not in p
        assert "facebook.com/testbistro" in p

    def test_no_contact_information(self):
        p = _prompt({**PROSPECT, "email": None, "phone": None, "identity_status": "verified"})
        assert "Direct Email: Not listed" in p and "Direct Phone: Not listed" in p


# ------------------------------------------------------------- audit probes
def test_ttfb_probe_blocked_by_ssrf_validation_records_error(monkeypatch):
    from backend.app.services import audit_engine as ae
    monkeypatch.setattr(ae, "validate_target_url", lambda url: (False, "private address", None, []))
    engine = ae.AuditEngine() if hasattr(ae, "AuditEngine") else None
    assert engine is not None
    results, errors = asyncio.run(engine._measure_extra_ttfb_probes("http://127.0.0.1/", {}, count=2))
    assert results == []
    assert errors and errors[0].startswith("blocked")


# ----------------------------------------------------------- API + database
class TestApiPersistence:
    def test_create_persists_identity_and_survives_reread(self, client):
        res = client.post("/api/prospects", json={
            "name": "Sarvi Test Restaurant", "category": "Restaurant",
            "location": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
            "websiteUrl": "http://www.justdial.com"})
        assert res.status_code == 201
        pid = res.json()["id"]
        detail = client.get(f"/api/prospects/{pid}").json()
        assert detail["identityStatus"] == "conflicting"
        assert detail["identityEvidence"]["is_aggregator"] is True
        assert detail["scoring"]["identityStatus"] == "conflicting"
        assert detail["scoring"]["opportunityScore"] == detail["opportunityScore"]

    def test_operator_override_recorded(self, client):
        pid = client.post("/api/prospects", json={
            "name": "Override Test Cafe", "category": "Cafe",
            "location": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
            "websiteUrl": "https://unrelated-group.example"}).json()["id"]
        res = client.patch(f"/api/prospects/{pid}", json={"identityStatus": "verified"})
        assert res.status_code == 200
        body = client.get(f"/api/prospects/{pid}").json()
        assert body["identityStatus"] == "verified"
        assert body["identityEvidence"]["operator_override"]["status"] == "verified"
        assert "previous_status" in body["identityEvidence"]["operator_override"]


def test_migration_adds_columns_and_keeps_old_rows(tmp_path):
    from sqlalchemy import create_engine
    from backend.app.core.database import migrate_db

    db_file = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE prospects (id VARCHAR PRIMARY KEY, name VARCHAR, website_url VARCHAR, email VARCHAR)")
    conn.execute("INSERT INTO prospects (id, name, website_url, email) VALUES ('p1','Legacy Cafe','https://legacy.example','a@legacy.example')")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file}")
    migrate_db(engine)
    migrate_db(engine)  # idempotent

    conn = sqlite3.connect(db_file)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(prospects)")}
    row = conn.execute("SELECT name, website_url, identity_status FROM prospects WHERE id='p1'").fetchone()
    conn.close()
    assert {"identity_status", "identity_evidence", "contact_provenance", "social_profiles"} <= cols
    assert row[0] == "Legacy Cafe" and row[1] == "https://legacy.example"
    assert row[2] == "not_checked"
