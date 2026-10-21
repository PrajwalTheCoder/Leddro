"""
Deterministic, explainable prospect scoring service for Leddro.

Separates:
1. Opportunity Score (0-100 heuristic of observed technical improvement opportunity)
2. Data Confidence (0-100 measure of evidence completeness, freshness, and reliability)
3. Audit Severity (Counts of observed high, medium, low, and info findings)
4. Contact Readiness (verified, unverified, absent, unknown)

Pure, deterministic calculations independent of HTTP handlers and database queries.
Missing metadata does NOT inflate the Opportunity Score; it lowers Data Confidence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

SCORING_VERSION = "1.0"

# Factor Weights for Opportunity Score (Total Max: 100 points)
# Points reflect confirmed technical room for improvement or verified absence of web presence.
MAX_ACCESSIBILITY_WEIGHT = 25
MAX_TECHNICAL_FINDINGS_WEIGHT = 55
MAX_HTTPS_WEIGHT = 20
MAX_CONTACT_WEIGHT = 0
MAX_DATA_COMPLETENESS_WEIGHT = 0

# Freshness Thresholds (Days)
AUDIT_AGE_RECENT_DAYS = 14
AUDIT_AGE_STALE_DAYS = 30
AUDIT_AGE_VERY_STALE_DAYS = 90


def _get_val(obj: Any, *keys: str, default: Any = None) -> Any:
    """Helper to safely extract field values from either objects or dicts using snake_case or camelCase."""
    if obj is None:
        return default
    for k in keys:
        if isinstance(obj, dict):
            if k in obj and obj[k] is not None:
                return obj[k]
        elif hasattr(obj, k):
            val = getattr(obj, k)
            if val is not None:
                return val
    return default


def _parse_json_field(val: Any) -> Dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return json.loads(val)
        except Exception:
            return {}
    return {}


def calculate_audit_age_days(audit_timestamp: Optional[str], audit_created_at: Optional[Any] = None) -> Optional[int]:
    """Calculates age in whole days of an audit from timestamp or created_at."""
    dt = None
    if audit_created_at:
        if isinstance(audit_created_at, datetime):
            dt = audit_created_at
        elif isinstance(audit_created_at, str):
            try:
                dt = datetime.fromisoformat(audit_created_at.replace("Z", "+00:00"))
            except Exception:
                pass

    if dt is None and audit_timestamp:
        cleaned = audit_timestamp.replace(" UTC", "").strip()
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
                break
            except Exception:
                continue

    if dt:
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (now - dt).total_seconds() / 86400.0
        return max(0, int(age))
    return None


def calculate_prospect_score(
    prospect: Any,
    latest_audit: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Pure, deterministic scoring calculation.
    
    Accepts:
    - prospect: ProspectModel instance, Pydantic schema, or dictionary.
    - latest_audit: Optional AuditReportModel instance or dictionary with report fields and findings.

    Returns a structured dictionary matching the explainability contract:
    - opportunity_score (0-100)
    - score_version ("1.0")
    - confidence_score (0-100)
    - priority_label ("High", "Medium", "Low", "Needs Audit")
    - contact_readiness ("verified", "unverified", "absent", "unknown")
    - audit_status ("completed", "failed", "running", "none")
    - audit_age_days (int or None)
    - audit_timestamp (str or None)
    - severity_summary ({high, medium, low, info})
    - factors (List of structured factor breakdowns with evidence and nature)
    - limitations (List of caveats / unknown factors)
    - recommended_actions (List of next investigation steps)
    """
    # 1. Normalize prospect input fields
    p_name = _get_val(prospect, "name", default="Unknown")
    p_url = _get_val(prospect, "website_url", "websiteUrl")
    p_email = _get_val(prospect, "email")
    p_phone = _get_val(prospect, "phone")
    p_city = _get_val(prospect, "city")
    if not p_city:
        loc = _get_val(prospect, "location")
        p_city = _get_val(loc, "city")
    p_category = _get_val(prospect, "category")
    p_last_verified = _get_val(prospect, "last_verified_at", "lastVerifiedAt")
    identity_status = str(_get_val(prospect, "identity_status", "identityStatus", default="not_checked") or "not_checked")
    contact_prov = _parse_json_field(_get_val(prospect, "contact_provenance", "contactProvenance"))
    contact_trust = contact_prov.get("status") if contact_prov else None
    # A website whose ownership is conflicting/uncertain cannot be used as evidence about this business.
    identity_untrusted = bool(p_url) and identity_status in ("conflicting", "uncertain")

    # 2. Normalize audit input
    audit_status = "none"
    audit_timestamp = None
    audit_created_at = None
    raw_ssl = {}
    findings_list = []

    if latest_audit:
        audit_status = _get_val(latest_audit, "status", default="completed")
        audit_timestamp = _get_val(latest_audit, "timestamp")
        audit_created_at = _get_val(latest_audit, "created_at", "createdAt")
        
        raw_ssl_val = _get_val(latest_audit, "raw_ssl", "rawSsl")
        raw_ssl = _parse_json_field(raw_ssl_val)

        raw_findings = _get_val(latest_audit, "findings", default=[])
        findings_list = list(raw_findings or [])
        if identity_untrusted:
            findings_list = []

    audit_age_days = calculate_audit_age_days(audit_timestamp, audit_created_at)

    factors: List[Dict[str, Any]] = []
    limitations: List[str] = []
    recommended_actions: List[str] = []

    # ---------------------------------------------------------
    # FACTOR 1: WEBSITE ACCESSIBILITY (0 - 25 pts)
    # ---------------------------------------------------------
    f1_contribution = 0
    f1_status = "untested"
    f1_nature = "unknown"
    f1_summary = ""
    f1_evidence: List[Dict[str, Any]] = []

    if not p_url:
        f1_contribution = 15
        f1_status = "no_website"
        f1_nature = "potential_opportunity"
        f1_summary = "No website registered for business. Potential opportunity for digital presence creation."
        limitations.append("Business has no registered website; outreach focuses on web presence setup.")
        recommended_actions.append("Pitch custom website development or digital listing creation.")
    elif identity_untrusted:
        f1_contribution = 0
        f1_status = "identity_unconfirmed"
        f1_nature = "unknown"
        f1_summary = (
            f"Website association is '{identity_status}'; its condition cannot be attributed to this business. "
            "No website defect points awarded until the domain is confirmed."
        )
        limitations.append(f"Website identity is '{identity_status}'; audit findings are excluded from the opportunity score.")
        recommended_actions.append("Confirm the business's official website before auditing or pitching website fixes.")
    elif audit_status == "none":
        f1_contribution = 0
        f1_status = "untested"
        f1_nature = "unknown"
        f1_summary = "Website URL configured but no diagnostic audit has been performed."
        limitations.append("Website reachability has not been verified by an audit.")
        recommended_actions.append("Execute initial website audit to confirm server reachability and DNS health.")
    elif audit_status == "completed":
        # Check HTTP response codes from findings or audit
        _transient = ("timeout", "timed out", "servfail", "temporar", "resolver", "unreachable")
        dns_failures = [
            f for f in findings_list 
            if _get_val(f, "category") == "reachability" 
            and _get_val(f, "check_status", "checkStatus") == "FAIL"
            and any(w in str(_get_val(f, "title", "")).lower() or w in str(_get_val(f, "observed", "")).lower() for w in ("dns", "nxdomain", "record", "resolve"))
            and not any(t in (str(_get_val(f, "title", "")) + " " + str(_get_val(f, "observed", ""))).lower() for t in _transient)
        ]
        
        # Check for confirmed server error
        http_errors = [
            f for f in findings_list 
            if (_get_val(f, "http_status", "httpStatus") is not None and _get_val(f, "http_status", "httpStatus") >= 400)
            or ("http" in str(_get_val(f, "title", "")).lower() and any(w in str(_get_val(f, "title", "")).lower() for w in ("error", "fail", "500", "502", "503", "404")))
        ]

        if http_errors:
            f1_contribution = 20
            f1_status = "http_error"
            f1_nature = "confirmed_deficiency"
            first_err = http_errors[0]
            err_code = _get_val(first_err, "http_status", "httpStatus", default=500)
            f1_summary = f"Observed HTTP {err_code} client/server error on domain."
            f1_evidence.append({
                "finding_id": _get_val(first_err, "id"),
                "title": _get_val(first_err, "title", default="HTTP Error"),
                "severity": _get_val(first_err, "severity", default="high"),
                "observed": _get_val(first_err, "observed", default=f"HTTP {err_code}"),
                "contribution": 20
            })
            recommended_actions.append(f"Highlight HTTP {err_code} server reachability failure in consultation.")
        elif dns_failures:
            f1_contribution = 25
            f1_status = "dns_failure"
            f1_nature = "confirmed_deficiency"
            first_dns = dns_failures[0]
            f1_summary = "DNS resolution failed for domain (no valid A/AAAA records)."
            f1_evidence.append({
                "finding_id": _get_val(first_dns, "id"),
                "title": _get_val(first_dns, "title", default="DNS Resolution Failure"),
                "severity": _get_val(first_dns, "severity", default="high"),
                "observed": _get_val(first_dns, "observed", default="Missing DNS records"),
                "contribution": 25
            })
            recommended_actions.append("Highlight broken DNS zone configuration and missing A records.")
        else:
            f1_contribution = 0
            f1_status = "confirmed_reachable"
            f1_nature = "informational"
            f1_summary = "Website is actively reachable with valid DNS resolution and HTTP response."
    else:
        # Audit status is failed / running / error
        # An unsuccessful audit does not automatically prove the website is broken.
        f1_contribution = 0
        f1_status = "check_failed"
        f1_nature = "failed_diagnostic"
        f1_summary = "Audit diagnostic failed to complete or encountered a connection error. Website reachability is inconclusive."
        limitations.append("Diagnostic audit failed to connect; this does not prove the website is defective.")
        recommended_actions.append("Re-run audit check to verify whether reachability issue was temporary network failure.")

    factors.append({
        "key": "website_accessibility",
        "label": "Website Accessibility",
        "contribution": min(MAX_ACCESSIBILITY_WEIGHT, f1_contribution),
        "max_contribution": MAX_ACCESSIBILITY_WEIGHT,
        "status": f1_status,
        "nature": f1_nature,
        "summary": f1_summary,
        "evidence": f1_evidence
    })

    # ---------------------------------------------------------
    # FACTOR 2: TECHNICAL FINDINGS AND SEVERITY (0 - 55 pts)
    # ---------------------------------------------------------
    f2_contribution = 0
    f2_status = "no_findings"
    f2_nature = "informational"
    f2_summary = ""
    f2_evidence: List[Dict[str, Any]] = []

    high_count = 0
    med_count = 0
    low_count = 0
    info_count = 0

    seen_finding_keys = set()
    deduped_findings = []

    for f in findings_list:
        f_id = _get_val(f, "id", default="")
        f_title = str(_get_val(f, "title", default="Observation"))
        f_sev = str(_get_val(f, "severity", default="medium")).lower()
        f_status = str(_get_val(f, "check_status", "checkStatus", default="WARNING")).upper()
        f_cat = str(_get_val(f, "category", default="general")).lower()
        f_obs = str(_get_val(f, "observed", default=""))

        if f_status in ("PASS", "NOT_CHECKED") or f_sev == "info":
            info_count += 1
            continue

        dedup_key = (f_cat, f_title.strip().lower())
        if dedup_key in seen_finding_keys:
            continue
        seen_finding_keys.add(dedup_key)
        deduped_findings.append({
            "id": f_id,
            "title": f_title,
            "severity": f_sev,
            "category": f_cat,
            "observed": f_obs
        })

        if f_sev == "high":
            high_count += 1
        elif f_sev == "medium":
            med_count += 1
        elif f_sev == "low":
            low_count += 1

    # Tiered severity weighting:
    # High: 15 pts each (capped at 35 pts)
    # Medium: 5 pts each (capped at 20 pts)
    # Low: 1 pt each (capped at 5 pts)
    high_pts = min(35, high_count * 15)
    med_pts = min(20, med_count * 5)
    low_pts = min(5, low_count * 1)
    f2_contribution = min(MAX_TECHNICAL_FINDINGS_WEIGHT, high_pts + med_pts + low_pts)

    if deduped_findings:
        f2_status = "issues_observed"
        f2_nature = "confirmed_deficiency"
        f2_summary = f"Observed {high_count} high, {med_count} medium, and {low_count} low severity technical issue(s)."
        for df in deduped_findings[:5]:
            item_contrib = 15 if df["severity"] == "high" else (5 if df["severity"] == "medium" else 1)
            f2_evidence.append({
                "finding_id": df["id"],
                "title": df["title"],
                "severity": df["severity"],
                "category": df["category"],
                "observed": df["observed"][:160] if df["observed"] else "",
                "contribution": item_contrib
            })
        if high_count > 0:
            recommended_actions.append(f"Review {high_count} high-severity website finding(s) as primary value proposition.")
    elif audit_status == "completed":
        f2_status = "clean"
        f2_nature = "informational"
        f2_summary = "Latest audit observed no high or medium technical defects."
    else:
        f2_status = "no_audit"
        f2_nature = "unknown"
        f2_summary = "No audit findings available for evaluation."

    factors.append({
        "key": "technical_findings",
        "label": "Technical Findings & Severity",
        "contribution": f2_contribution,
        "max_contribution": MAX_TECHNICAL_FINDINGS_WEIGHT,
        "status": f2_status,
        "nature": f2_nature,
        "summary": f2_summary,
        "evidence": f2_evidence
    })

    # ---------------------------------------------------------
    # FACTOR 3: HTTPS & TRANSPORT SECURITY (0 - 20 pts)
    # ---------------------------------------------------------
    f3_contribution = 0
    f3_status = "unknown"
    f3_nature = "unknown"
    f3_summary = ""
    f3_evidence: List[Dict[str, Any]] = []

    if not p_url:
        f3_status = "not_applicable"
        f3_nature = "informational"
        f3_summary = "No website configured to evaluate TLS."
    elif identity_untrusted:
        f3_status = "identity_unconfirmed"
        f3_nature = "unknown"
        f3_summary = "TLS evidence not attributed: website association is unconfirmed."
    elif audit_status == "completed":
        ssl_valid = raw_ssl.get("valid")
        ssl_issuer = raw_ssl.get("issuer", "Unknown CA")
        tls_ver = raw_ssl.get("tlsVersion", "N/A")

        if ssl_valid is True:
            f3_contribution = 0
            f3_status = "https_verified"
            f3_nature = "informational"
            f3_summary = f"HTTPS verified with valid TLS certificate ({ssl_issuer}, {tls_ver})."
        elif ssl_valid is False and ssl_issuer != "None":
            f3_contribution = MAX_HTTPS_WEIGHT
            f3_status = "tls_invalid"
            f3_nature = "confirmed_deficiency"
            f3_summary = f"HTTPS certificate validation failed: {ssl_issuer}."
            recommended_actions.append("Highlight SSL/TLS certificate security issue to prospect.")
        elif str(p_url).startswith("http://"):
            f3_contribution = 15
            f3_status = "http_only"
            f3_nature = "confirmed_deficiency"
            f3_summary = "Website is served over unencrypted HTTP without verified HTTPS redirect."
            recommended_actions.append("Recommend TLS/HTTPS transport encryption implementation.")
        else:
            f3_contribution = 0
            f3_status = "tls_unconfirmed"
            f3_nature = "unknown"
            f3_summary = "TLS certificate status could not be conclusively determined."
            limitations.append("TLS certificate status was not confirmed by the audit.")
    else:
        if p_url and str(p_url).startswith("http://"):
            f3_contribution = 0
            f3_status = "unverified_http"
            f3_nature = "unknown"
            f3_summary = "Configured URL uses HTTP; HTTPS status unconfirmed by audit."
            limitations.append("HTTPS status unverified prior to audit execution.")
        else:
            f3_contribution = 0
            f3_status = "untested"
            f3_nature = "unknown"
            f3_summary = "HTTPS and TLS security have not yet been tested."

    factors.append({
        "key": "https_transport",
        "label": "HTTPS & Transport Security",
        "contribution": min(MAX_HTTPS_WEIGHT, f3_contribution),
        "max_contribution": MAX_HTTPS_WEIGHT,
        "status": f3_status,
        "nature": f3_nature,
        "summary": f3_summary,
        "evidence": f3_evidence
    })

    # ---------------------------------------------------------
    # FACTOR 4: CONTACT READINESS (Tracked separately; 0 pts to Opportunity Score)
    # ---------------------------------------------------------
    contact_readiness = "absent"
    has_email = bool(p_email and "@" in str(p_email))
    has_phone = bool(p_phone and len(str(p_phone).strip()) >= 5)
    is_verified = bool(p_last_verified)

    if has_email and has_phone:
        if is_verified:
            contact_readiness = "verified"
            f4_summary = f"Direct email ({p_email}) and phone ({p_phone}) are present and verified."
        else:
            contact_readiness = "unverified"
            f4_summary = f"Email ({p_email}) and phone ({p_phone}) are present but unverified."
            limitations.append("Contact information has not been verified; confirm prior to outreach.")
    elif has_email or has_phone:
        channel_name = f"Email ({p_email})" if has_email else f"Phone ({p_phone})"
        if is_verified:
            contact_readiness = "verified"
            f4_summary = f"{channel_name} is present and verified."
        else:
            contact_readiness = "unverified"
            f4_summary = f"{channel_name} is present but unverified."
            limitations.append(f"{channel_name} is unverified.")
            recommended_actions.append("Verify contact channel before generating dispatch.")
    else:
        contact_readiness = "absent"
        f4_summary = "No email address or phone number is recorded for this business."
        limitations.append("No direct contact details available; research required before outreach.")
        recommended_actions.append("Find direct business email or phone contact.")

    factors.append({
        "key": "contact_readiness",
        "label": "Contact Readiness",
        "contribution": 0,
        "max_contribution": 0,
        "status": contact_readiness,
        "nature": "informational",
        "summary": f4_summary,
        "evidence": []
    })

    # ---------------------------------------------------------
    # FACTOR 5: DATA COMPLETENESS (Tracked separately; 0 pts to Opportunity Score)
    # ---------------------------------------------------------
    completeness_missing = []
    if not p_city:
        completeness_missing.append("location")
    if not p_category or p_category in ("Commercial Services", "Uncategorized"):
        completeness_missing.append("specific category")
    if not p_name or str(p_name).lower().startswith("unnamed"):
        completeness_missing.append("business name")

    if completeness_missing:
        f5_status = "incomplete"
        f5_nature = "unknown"
        f5_summary = f"Missing profile information: {', '.join(completeness_missing)}."
        limitations.append(f"Business profile lacks {', '.join(completeness_missing)}.")
    else:
        f5_status = "complete"
        f5_nature = "informational"
        f5_summary = "Complete business identity recorded (name, verified locality, and category)."

    factors.append({
        "key": "data_completeness",
        "label": "Data Completeness",
        "contribution": 0,
        "max_contribution": 0,
        "status": f5_status,
        "nature": f5_nature,
        "summary": f5_summary,
        "evidence": []
    })

    # ---------------------------------------------------------
    # OPPORTUNITY SCORE CALCULATION
    # Strictly bounded 0 - 100 based ONLY on technical deficits and web presence need
    # ---------------------------------------------------------
    opportunity_score = sum(f["contribution"] for f in factors)
    opportunity_score = max(0, min(100, int(round(opportunity_score))))

    # ---------------------------------------------------------
    # DATA CONFIDENCE CALCULATION (0 - 100)
    # Measures completeness, recency, and diagnostic reliability
    # ---------------------------------------------------------
    confidence = 100

    # 1. Audit existence penalty
    if audit_status == "none":
        confidence -= 40
        limitations.append("No technical audit on file; confidence is constrained to baseline discovery data.")
    elif audit_status != "completed":
        confidence -= 35
        limitations.append("Latest audit did not complete successfully; technical diagnostic is unconfirmed.")

    # 2. Audit recency decay penalty
    if audit_age_days is not None:
        if audit_age_days > AUDIT_AGE_VERY_STALE_DAYS:
            confidence -= 30
            limitations.append(f"Audit is {audit_age_days} days old (>90d); technical status may be outdated.")
            recommended_actions.append("Re-audit website to update stale findings.")
        elif audit_age_days > AUDIT_AGE_STALE_DAYS:
            confidence -= 15
            limitations.append(f"Audit is {audit_age_days} days old (>30d); findings should be refreshed.")
            recommended_actions.append("Re-audit website to verify current state.")
        elif audit_age_days > AUDIT_AGE_RECENT_DAYS:
            confidence -= 5

    # 3. Contact verification penalty (differentiated by provenance when available)
    if contact_readiness == "absent":
        confidence -= 15
    elif contact_trust in ("official_source", "corroborated", "provider_verified") and has_email:
        confidence -= 0
    elif contact_trust == "conflicting" and has_email:
        confidence -= 15
        limitations.append("Recorded email has conflicting provenance (e.g. third-party/blogger/aggregator address); do not treat as the business's contact.")
    elif contact_readiness == "unverified":
        confidence -= 8

    # 3b. Identity penalty: unconfirmed website ownership lowers trust in everything about the site
    if identity_untrusted:
        confidence -= 30
        limitations.append(f"Website identity status is '{identity_status}'; ownership of the domain is not confirmed.")
    elif p_url and identity_status == "likely_match":
        confidence -= 5
        limitations.append("Website association is a likely (not independently verified) match.")

    # 4. Incomplete data penalty
    if completeness_missing:
        confidence -= 10

    confidence_score = max(10, min(100, confidence))

    # ---------------------------------------------------------
    # PRIORITY LABEL
    # ---------------------------------------------------------
    if identity_untrusted:
        priority_label = "Needs Audit"
    elif audit_status == "none" and p_url:
        priority_label = "Needs Audit"
    elif confidence_score < 40:
        priority_label = "Needs Audit" if p_url else "Low"
    elif opportunity_score >= 60:
        priority_label = "High"
    elif opportunity_score >= 25:
        priority_label = "Medium"
    else:
        priority_label = "Low"

    if not recommended_actions:
        recommended_actions.append("Review prospect details and prepare tailored draft.")

    return {
        "opportunity_score": opportunity_score,
        "score_version": SCORING_VERSION,
        "confidence_score": confidence_score,
        "priority_label": priority_label,
        "contact_readiness": contact_readiness,
        "contact_trust": contact_trust or ("none" if not has_email else "unverified"),
        "identity_status": identity_status,
        "audit_status": audit_status,
        "audit_age_days": audit_age_days,
        "audit_timestamp": audit_timestamp,
        "severity_summary": {
            "high": high_count,
            "medium": med_count,
            "low": low_count,
            "info": info_count
        },
        "factors": factors,
        "limitations": limitations,
        "recommended_actions": recommended_actions
    }
