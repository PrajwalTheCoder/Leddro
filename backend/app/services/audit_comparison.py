"""
Deterministic Website Audit Comparison & Change Detection Engine for Leddro.

Provides deterministic, evidence-based before/after audit comparison:
1. Four finding classifications:
   - RESOLVED: Confirmed in older audit, positive proof of pass in newer audit.
   - NEW: Not present in older audit, confirmed in newer audit, older check ran.
   - PERSISTENT: Confirmed in both audits.
   - INCONCLUSIVE: Missing evidence, audit failure, check skipped, or diagnostic error.
2. Technical measurement comparisons (TTFB, DOM ready, DNS latency, SSL expiry, TLS version, HTTP status).
3. Audit-level reliability validation (domain matching, execution status, timestamp order).
4. Pure deterministic calculations independent of external network or AI services.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

from backend.app.discovery.normalizer import extract_registered_domain, normalize_website_url

# Standard check keys mapping
KNOWN_CHECK_KEYS = {
    "reachability.dns_a_record": {
        "title": "DNS A/IPv4 Record Resolution",
        "category": "reachability",
        "description": "Domain resolves to valid IPv4 addresses"
    },
    "reachability.dns_mx_record": {
        "title": "Mail Exchange (MX) Configuration",
        "category": "reachability",
        "description": "Domain advertises valid MX mail routers"
    },
    "reachability.http_server_response": {
        "title": "HTTP Server Availability & Status",
        "category": "reachability",
        "description": "Web server returns successful HTTP response codes"
    },
    "security.ssrf_prevention": {
        "title": "SSRF & Network Address Routing",
        "category": "security",
        "description": "Requests target publicly routable addresses without internal hops"
    },
    "security.tls_certificate": {
        "title": "SSL/TLS Certificate Validity & Expiration",
        "category": "security",
        "description": "Valid, unexpired TLS certificate issued by trusted CA"
    },
    "security.tls_handshake": {
        "title": "TLS Connection Handshake",
        "category": "security",
        "description": "Successful cryptographic TLS handshake on port 443"
    },
    "security.dns_dmarc_record": {
        "title": "DMARC Email Authentication Policy",
        "category": "security",
        "description": "Domain defines an active DMARC policy record"
    },
    "performance.document_download_size": {
        "title": "Initial Document Download Payload Size",
        "category": "performance",
        "description": "HTML payload stays within recommended payload thresholds"
    },
    "performance.time_to_first_byte": {
        "title": "Time to First Byte (TTFB)",
        "category": "performance",
        "description": "Server responds within latency thresholds (< 800ms)"
    },
    "performance.mobile_viewport": {
        "title": "Mobile Responsive Viewport Meta",
        "category": "performance",
        "description": "HTML document defines a responsive meta viewport tag"
    },
    "seo_meta.dns_spf_record": {
        "title": "Sender Policy Framework (SPF) DNS Record",
        "category": "seo_meta",
        "description": "Domain defines authorized outgoing mail servers"
    },
    "seo_meta.page_title": {
        "title": "HTML Document Page Title",
        "category": "seo_meta",
        "description": "Document includes a descriptive, non-empty <title> tag"
    },
    "seo_meta.meta_description": {
        "title": "Search Snippet Meta Description",
        "category": "seo_meta",
        "description": "Document contains a curated meta description tag"
    },
    "conversion.contact_pathway": {
        "title": "Internal Contact & Inquiry Pathways",
        "category": "conversion",
        "description": "Navigation provides clear contact or inquiry routes"
    }
}


def derive_check_key(category: Optional[str], title: Optional[str], finding_id: Optional[str] = None) -> str:
    """
    Derives a stable, deterministic check key from finding attributes.
    Prefers well-defined check identifiers, normalized titles, and categories.
    Guarantees strict category boundary enforcement to prevent disparate checks
    with similar wording from colliding.
    """
    norm_title = (title or "").lower().strip()
    norm_cat = (category or "").lower().strip()
    norm_id = (finding_id or "").lower().strip()

    # Direct canonical check key match
    if norm_id in KNOWN_CHECK_KEYS:
        return norm_id

    # 1. Match from ID prefix patterns if present
    if "f-dns-a" in norm_id:
        return "reachability.dns_a_record"
    if "f-dns-mx" in norm_id:
        return "reachability.dns_mx_record"
    if "f-dns-spf" in norm_id:
        return "seo_meta.dns_spf_record"
    if "f-dns-dmarc" in norm_id:
        return "security.dns_dmarc_record"
    if "f-ssl-exp" in norm_id or "f-ssl-warn" in norm_id or "f-ssl-pass" in norm_id or "f-ssl-err" in norm_id:
        return "security.tls_certificate"
    if "f-ssrf" in norm_id:
        return "security.ssrf_prevention"
    if any(k in norm_id for k in ("f-http-404", "f-http-500", "f-http-pass", "f-timeout", "f-conn-err", "f-http-err")):
        return "reachability.http_server_response"
    if "f-size" in norm_id:
        return "performance.document_download_size"
    if "f-ttfb" in norm_id:
        return "performance.time_to_first_byte"
    if "f-html-vp" in norm_id:
        return "performance.mobile_viewport"
    if "f-html-title" in norm_id:
        return "seo_meta.page_title"
    if "f-html-desc" in norm_id:
        return "seo_meta.meta_description"
    if "f-html-nocontact" in norm_id or "f-html-contact" in norm_id:
        return "conversion.contact_pathway"

    # 2. Match from title patterns strictly segregated by check category domain
    # Reachability
    if norm_cat in ("", "reachability", "network", "dns", "general"):
        if "dns a/ipv4" in norm_title or "dns a record" in norm_title or "ipv4 record" in norm_title or "dns a resolution" in norm_title:
            return "reachability.dns_a_record"
        if "mail exchange" in norm_title or "mx record" in norm_title:
            return "reachability.dns_mx_record"
        if any(term in norm_title for term in ("404", "500", "http status", "connection timed out", "tcp connection", "http request failed", "http server")):
            return "reachability.http_server_response"

    # Security
    if norm_cat in ("", "security", "ssl", "tls", "dns", "general"):
        if "dmarc" in norm_title or "v=dmarc1" in norm_title:
            return "security.dns_dmarc_record"
        if any(term in norm_title for term in ("ssl/tls certificate", "certificate expired", "certificate expiring", "tls connection", "tls handshake", "ssl/tls", "valid ssl/tls")):
            return "security.tls_certificate"
        if any(term in norm_title for term in ("security filter", "ssrf", "prohibited ip")):
            return "security.ssrf_prevention"

    # Performance
    if norm_cat in ("", "performance", "speed", "mobile", "general"):
        if "download size" in norm_title or "payload" in norm_title or "maximum download" in norm_title:
            return "performance.document_download_size"
        if "ttfb" in norm_title or "time to first byte" in norm_title or "latency" in norm_title:
            return "performance.time_to_first_byte"
        if "viewport" in norm_title or "mobile viewport" in norm_title:
            return "performance.mobile_viewport"

    # SEO & Metadata
    if norm_cat in ("", "seo_meta", "seo", "dns", "meta", "general"):
        if "sender policy framework" in norm_title or "spf" in norm_title or "v=spf1" in norm_title:
            return "seo_meta.dns_spf_record"
        if "page title" in norm_title or "title tag" in norm_title:
            return "seo_meta.page_title"
        if "meta description" in norm_title or "description tag" in norm_title:
            return "seo_meta.meta_description"

    # Conversion
    if norm_cat in ("", "conversion", "ux", "content", "general"):
        if "contact" in norm_title or "inquiry" in norm_title or "contact pathway" in norm_title:
            return "conversion.contact_pathway"

    # 3. Fallback deterministic slug from category and title (preserving up to 80 chars)
    cat_slug = norm_cat if norm_cat else "general"
    clean_title = re.sub(r"[^a-z0-9]+", "_", norm_title).strip("_")
    if clean_title:
        return f"{cat_slug}.{clean_title[:80]}"
    clean_id = re.sub(r"[^a-z0-9]+", "_", norm_id).strip("_")
    if clean_id:
        return f"{cat_slug}.{clean_id[:80]}"
    return f"{cat_slug}.unknown_check"


def normalize_check_status(finding_or_dict: Any) -> str:
    """
    Normalizes a finding into standard semantic status:
    - confirmed_pass
    - confirmed_fail
    - skipped
    - check_failed
    - unknown
    """
    if finding_or_dict is None:
        return "unknown"

    raw_status = _get_field(finding_or_dict, "check_status", "checkStatus", default="")
    severity = _get_field(finding_or_dict, "severity", default="")
    title = str(_get_field(finding_or_dict, "title", default="")).lower()
    fid = str(_get_field(finding_or_dict, "id", default="")).lower()

    raw_upper = str(raw_status).upper().strip()
    sev_lower = str(severity).lower().strip()

    if raw_upper == "PASS":
        return "confirmed_pass"
    if raw_upper in ("NOT_CHECKED", "SKIPPED"):
        return "skipped"
    if raw_upper == "ERROR":
        return "check_failed"
    if raw_upper in ("FAIL", "WARNING"):
        return "confirmed_fail"

    # Fallback to severity heuristic only when check_status was omitted
    if sev_lower in ("high", "medium", "low"):
        return "confirmed_fail"
    if sev_lower == "info":
        # Only treat info as confirmed pass if there is positive passing indication in title or ID
        if "pass" in fid or any(term in title for term in ("pass", "verified", "operational", "healthy")):
            return "confirmed_pass"

    return "unknown"


def is_finding_defect(finding: Any) -> bool:
    """Returns True if the finding documents a confirmed problem or warning."""
    status = normalize_check_status(finding)
    if status == "confirmed_fail":
        return True
    if status in ("confirmed_pass", "check_failed", "skipped"):
        return False
    sev = str(_get_field(finding, "severity", default="")).lower()
    return sev in ("high", "medium", "low")


def is_finding_pass(finding: Any) -> bool:
    """Returns True if the finding documents a verified passing check."""
    status = normalize_check_status(finding)
    return status == "confirmed_pass"


def is_finding_error(finding: Any) -> bool:
    """Returns True if the check failed diagnostically (timeout, connection refused, execution crash)."""
    status = normalize_check_status(finding)
    return status == "check_failed"


def is_finding_skipped(finding: Any) -> bool:
    """Returns True if the check was marked NOT_CHECKED / skipped."""
    status = normalize_check_status(finding)
    return status == "skipped"


def _get_field(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely extracts attributes from ORM models or dicts."""
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


def _parse_json(val: Any, default: Any = None) -> Any:
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return json.loads(val)
        except Exception:
            return default
    return default


def _parse_timestamp(ts_val: Any) -> Optional[datetime]:
    if isinstance(ts_val, datetime):
        return ts_val if ts_val.tzinfo else ts_val.replace(tzinfo=timezone.utc)
    if not ts_val or not isinstance(ts_val, str):
        return None
    s = ts_val.strip()
    # Try ISO format
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        pass
    # Try standard formats
    for fmt in (
        "%Y-%m-%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M UTC",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


class AuditComparisonService:
    """
    Core service to compare two audits of the same website/prospect.
    Computes findings diff across four states: resolved, new, persistent, inconclusive.
    Computes comparable technical measurements with direction and safety checks.
    """

    def compare_audits(
        self,
        older_audit: Any,
        newer_audit: Any,
        prospect: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes a deterministic comparison between older_audit and newer_audit.
        """
        # 1. Audit-Level Identity and Timestamp Validations
        self._validate_comparison_preconditions(older_audit, newer_audit)

        older_id = str(_get_field(older_audit, "id"))
        newer_id = str(_get_field(newer_audit, "id"))
        older_ts = str(_get_field(older_audit, "timestamp") or "")
        newer_ts = str(_get_field(newer_audit, "timestamp") or "")
        older_url = str(_get_field(older_audit, "url") or "")
        newer_url = str(_get_field(newer_audit, "url") or older_url)

        older_status = str(_get_field(older_audit, "status", default="completed")).lower()
        newer_status = str(_get_field(newer_audit, "status", default="completed")).lower()

        # Determine overall execution status
        if older_status == "completed" and newer_status == "completed":
            exec_status = "both_completed"
            is_reliable = True
        elif older_status == "completed" and newer_status != "completed":
            exec_status = "newer_failed"
            is_reliable = False
        elif older_status != "completed" and newer_status == "completed":
            exec_status = "older_failed"
            is_reliable = False
        else:
            exec_status = "both_failed"
            is_reliable = False

        limitations: List[str] = []
        if exec_status == "newer_failed":
            limitations.append(
                "Newer audit failed or timed out during execution. Disappeared findings cannot be confirmed resolved and are classified as inconclusive."
            )
        elif exec_status == "older_failed":
            limitations.append(
                "Older audit did not complete successfully. New issues cannot be confirmed as newly introduced because baseline evidence is incomplete."
            )
        elif exec_status == "both_failed":
            limitations.append(
                "Both audits experienced diagnostic failures. Finding comparisons are largely inconclusive."
            )

        # 2. Extract and Deduplicate Findings by Check Key
        older_findings_raw = _get_field(older_audit, "findings", default=[])
        newer_findings_raw = _get_field(newer_audit, "findings", default=[])

        older_findings_by_key = self._index_findings_by_key(older_findings_raw)
        newer_findings_by_key = self._index_findings_by_key(newer_findings_raw)

        # 3. Classify Findings across the 4 States
        classified = self._classify_findings(
            older_findings_by_key=older_findings_by_key,
            newer_findings_by_key=newer_findings_by_key,
            older_status=older_status,
            newer_status=newer_status,
            older_ts=older_ts,
            newer_ts=newer_ts
        )

        # 4. Compare Technical Measurements
        measurements = self._compare_measurements(older_audit, newer_audit, older_status, newer_status)

        comparable_measurements_count = sum(1 for m in measurements if m.get("status") == "comparable")

        summary = {
            "resolvedCount": len(classified["resolved"]),
            "newCount": len(classified["new"]),
            "persistentCount": len(classified["persistent"]),
            "inconclusiveCount": len(classified["inconclusive"]),
            "comparableMeasurementsCount": comparable_measurements_count,
            "totalFindingsEvaluated": len(classified["resolved"]) + len(classified["new"]) + len(classified["persistent"]) + len(classified["inconclusive"]),
            "isReliable": is_reliable,
            "executionStatus": exec_status
        }

        # Prospect details
        prospect_id = _get_field(prospect, "id") or _get_field(older_audit, "prospect_id", "prospectId")
        prospect_name = _get_field(prospect, "name") if prospect else None

        return {
            "olderAuditId": older_id,
            "newerAuditId": newer_id,
            "olderTimestamp": older_ts,
            "newerTimestamp": newer_ts,
            "url": newer_url,
            "prospectId": prospect_id,
            "prospectName": prospect_name,
            "executionStatus": exec_status,
            "isReliable": is_reliable,
            "summary": summary,
            "resolvedFindings": classified["resolved"],
            "newFindings": classified["new"],
            "persistentFindings": classified["persistent"],
            "inconclusiveFindings": classified["inconclusive"],
            "measurements": measurements,
            "limitations": limitations
        }

    def _validate_comparison_preconditions(self, older_audit: Any, newer_audit: Any) -> None:
        """Validates that the two audits are valid for comparison."""
        older_id = _get_field(older_audit, "id")
        newer_id = _get_field(newer_audit, "id")

        if not older_id or not newer_id:
            raise ValueError("Both older_audit_id and newer_audit_id are required.")

        if older_id == newer_id:
            raise ValueError("Cannot compare an audit with itself. Please select two distinct audits.")

        # Validate prospect identity
        older_pid = _get_field(older_audit, "prospect_id", "prospectId")
        newer_pid = _get_field(newer_audit, "prospect_id", "prospectId")

        # Reject cross-prospect comparison unconditionally when both are associated with prospects
        if older_pid and newer_pid and older_pid != newer_pid:
            raise ValueError(
                f"Audits belong to different prospects ('{older_pid}' vs '{newer_pid}'). Cross-prospect comparisons are not permitted."
            )

        # Validate domain / website identity
        older_url = _get_field(older_audit, "url")
        newer_url = _get_field(newer_audit, "url")

        older_domain = extract_registered_domain(older_url)
        newer_domain = extract_registered_domain(newer_url)

        # If domains are identifiable and differ -> Reject
        if older_domain and newer_domain and older_domain != newer_domain:
            raise ValueError(
                f"Audits belong to different websites ('{older_domain}' vs '{newer_domain}'). Comparisons are only supported for the same website identity."
            )

        # Timestamp order check
        older_dt = _parse_timestamp(_get_field(older_audit, "timestamp")) or _parse_timestamp(_get_field(older_audit, "created_at"))
        newer_dt = _parse_timestamp(_get_field(newer_audit, "timestamp")) or _parse_timestamp(_get_field(newer_audit, "created_at"))

        if older_dt and newer_dt:
            if older_dt > newer_dt:
                raise ValueError(
                    f"Invalid audit ordering: The older audit ({older_dt.strftime('%Y-%m-%d %H:%M')}) is more recent than the newer audit ({newer_dt.strftime('%Y-%m-%d %H:%M')}). Please select the earlier audit as the older audit."
                )

    def _index_findings_by_key(self, findings: List[Any]) -> Dict[str, Dict[str, Any]]:
        """
        Indexes findings by deterministic check key, resolving duplicates consistently.
        Deduplication rule: If an audit produces multiple findings for the same check key,
        we pick the highest severity defect (or most informative pass) and preserve references.
        """
        severity_rank = {"high": 4, "medium": 3, "low": 2, "info": 1}
        indexed: Dict[str, Dict[str, Any]] = {}

        for f in findings:
            cat = _get_field(f, "category", default="")
            title = _get_field(f, "title", default="")
            fid = _get_field(f, "id", default="")
            explicit_key = _get_field(f, "check_key", "checkKey")
            key = str(explicit_key).strip() if (explicit_key and str(explicit_key).strip()) else derive_check_key(cat, title, fid)

            is_defect = is_finding_defect(f)
            is_pass = is_finding_pass(f)
            is_error = is_finding_error(f)
            is_skipped = is_finding_skipped(f)
            status = normalize_check_status(f)
            sev = str(_get_field(f, "severity", default="info")).lower()
            rank = severity_rank.get(sev, 0)

            if key not in indexed:
                indexed[key] = {
                    "primary_finding": f,
                    "check_key": key,
                    "title": title,
                    "category": cat,
                    "severity": sev,
                    "status": status,
                    "is_defect": is_defect,
                    "is_pass": is_pass,
                    "is_error": is_error,
                    "is_skipped": is_skipped,
                    "all_finding_ids": [fid] if fid else [],
                    "all_evidence": [_get_field(f, "evidence", default="")],
                    "all_observed": [_get_field(f, "observed", default="")],
                    "rank": rank
                }
            else:
                existing = indexed[key]
                if fid:
                    existing["all_finding_ids"].append(fid)
                ev = _get_field(f, "evidence", default="")
                if ev:
                    existing["all_evidence"].append(ev)
                ob = _get_field(f, "observed", default="")
                if ob:
                    existing["all_observed"].append(ob)

                # If this finding has a higher severity or converts pass to defect
                if (is_defect and not existing["is_defect"]) or (rank > existing["rank"]):
                    existing["primary_finding"] = f
                    existing["title"] = title
                    existing["category"] = cat
                    existing["severity"] = sev
                    existing["status"] = status
                    existing["is_defect"] = is_defect
                    existing["is_pass"] = is_pass
                    existing["is_error"] = is_error
                    existing["is_skipped"] = is_skipped
                    existing["rank"] = rank

        return indexed

    def _classify_findings(
        self,
        older_findings_by_key: Dict[str, Dict[str, Any]],
        newer_findings_by_key: Dict[str, Dict[str, Any]],
        older_status: str,
        newer_status: str,
        older_ts: str,
        newer_ts: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classifies findings into resolved, new, persistent, inconclusive.
        """
        resolved: List[Dict[str, Any]] = []
        new: List[Dict[str, Any]] = []
        persistent: List[Dict[str, Any]] = []
        inconclusive: List[Dict[str, Any]] = []

        all_keys = set(older_findings_by_key.keys()).union(set(newer_findings_by_key.keys()))

        for key in sorted(all_keys):
            older_item = older_findings_by_key.get(key)
            newer_item = newer_findings_by_key.get(key)

            # Extract details
            older_f = older_item["primary_finding"] if older_item else None
            newer_f = newer_item["primary_finding"] if newer_item else None

            title = (
                (newer_item and newer_item["title"])
                or (older_item and older_item["title"])
                or KNOWN_CHECK_KEYS.get(key, {}).get("title", key)
            )
            category = (
                (newer_item and newer_item["category"])
                or (older_item and older_item["category"])
                or KNOWN_CHECK_KEYS.get(key, {}).get("category", "reachability")
            )
            severity = (
                (newer_item and newer_item["severity"])
                or (older_item and older_item["severity"])
                or "medium"
            )

            older_id = _get_field(older_f, "id")
            newer_id = _get_field(newer_f, "id")
            older_ev = _get_field(older_f, "evidence")
            newer_ev = _get_field(newer_f, "evidence")
            older_ob = _get_field(older_f, "observed")
            newer_ob = _get_field(newer_f, "observed")

            older_is_defect = older_item["is_defect"] if older_item else False
            newer_is_defect = newer_item["is_defect"] if newer_item else False
            older_is_pass = older_item["is_pass"] if older_item else False
            newer_is_pass = newer_item["is_pass"] if newer_item else False
            older_is_error = older_item["is_error"] if older_item else False
            newer_is_error = newer_item["is_error"] if newer_item else False
            newer_is_skipped = newer_item["is_skipped"] if newer_item else False
            older_is_skipped = older_item["is_skipped"] if older_item else False

            # CASE 1: Issue was present in older audit
            if older_is_defect:
                if newer_status != "completed":
                    # Newer audit failed; previous issue cannot be verified as resolved
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Newer audit failed or timed out during execution. Previous defect cannot be verified as resolved."
                    })
                elif newer_is_error:
                    # Newer check threw a diagnostic error
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Newer check failed with a diagnostic error or connection timeout; cannot verify if defect is resolved."
                    })
                elif newer_is_skipped:
                    # Newer check was skipped
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Check was skipped in newer audit. Disappearance of finding does not imply resolution."
                    })
                elif newer_is_defect:
                    # Issue confirmed in both audits
                    persistent.append({
                        "state": "persistent",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": f"Underlying defect confirmed in both audits ({older_ts} and {newer_ts})."
                    })
                elif newer_is_pass:
                    # Positive evidence that the check completed and passed!
                    resolved.append({
                        "state": "resolved",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": f"Positive verification: Check completed on {newer_ts} and confirmed the previous issue is no longer present."
                    })
                else:
                    # Finding disappeared from newer findings, but NO explicit PASS evidence exists!
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Issue omitted from newer audit findings, but the newer audit does not contain positive pass evidence for this check. Resolution cannot be inferred."
                    })

            # CASE 2: Issue was NOT present in older audit, but is present in newer audit
            elif newer_is_defect:
                if older_status != "completed":
                    # Older audit was failed; cannot confirm whether issue is newly introduced
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Issue confirmed in newer audit, but older audit was incomplete or failed. Cannot determine if issue is newly introduced or previously unobserved."
                    })
                elif older_is_error or older_is_skipped:
                    # Older audit experienced an error or skipped this check
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Older audit did not execute this check successfully. Cannot establish whether the issue was absent or unobserved in older audit."
                    })
                elif older_is_pass or (older_item is not None and older_status == "completed"):
                    # Older audit successfully ran the check and confirmed pass / no defect
                    new.append({
                        "state": "new",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": f"Newly detected issue confirmed in newer audit ({newer_ts}) with evidence. Check was operational or passed in older audit ({older_ts})."
                    })
                else:
                    # Older audit omitted check without pass evidence
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": severity,
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Defect confirmed in newer audit, but older audit contains no record of this check. Cannot reliably determine introduction time."
                    })

            # CASE 3: Neither was a defect (e.g. both passed, or errors without defect)
            else:
                if older_is_error or newer_is_error:
                    inconclusive.append({
                        "state": "inconclusive",
                        "checkKey": key,
                        "title": title,
                        "category": category,
                        "severity": "info",
                        "olderFindingId": older_id,
                        "newerFindingId": newer_id,
                        "olderEvidence": older_ev,
                        "newerEvidence": newer_ev,
                        "olderObserved": older_ob,
                        "newerObserved": newer_ob,
                        "reason": "Diagnostic execution error occurred in one or both audit checks."
                    })

        return {
            "resolved": resolved,
            "new": new,
            "persistent": persistent,
            "inconclusive": inconclusive
        }

    def _compare_measurements(
        self,
        older_audit: Any,
        newer_audit: Any,
        older_status: str,
        newer_status: str
    ) -> List[Dict[str, Any]]:
        """
        Extracts and compares technical measurements between both audits.
        Guarantees:
        - Missing values are distinguished from zero.
        - No division by zero.
        - Units are preserved and validated.
        - HTTP status codes and TLS versions are compared using semantic domains, not simple numeric arithmetic.
        """
        measurements: List[Dict[str, Any]] = []

        older_perf = _parse_json(_get_field(older_audit, "performance"), {})
        newer_perf = _parse_json(_get_field(newer_audit, "performance"), {})

        older_dns = _parse_json(_get_field(older_audit, "raw_dns", "rawDns"), {})
        newer_dns = _parse_json(_get_field(newer_audit, "raw_dns", "rawDns"), {})

        older_ssl = _parse_json(_get_field(older_audit, "raw_ssl", "rawSsl"), {})
        newer_ssl = _parse_json(_get_field(newer_audit, "raw_ssl", "rawSsl"), {})

        # 1. HTTP Response Time (TTFB in ms)
        older_ttfb = older_perf.get("ttfbMs")
        newer_ttfb = newer_perf.get("ttfbMs")
        measurements.append(self._compare_numeric_metric(
            key="http_ttfb",
            label="HTTP Response Latency (TTFB)",
            before=older_ttfb,
            after=newer_ttfb,
            unit="ms",
            lower_is_better=True,
            can_compare=(older_status == "completed" and newer_status == "completed")
        ))

        # 2. DOM Ready / Processing Time (ms)
        older_dom = older_perf.get("domReadyMs")
        newer_dom = newer_perf.get("domReadyMs")
        measurements.append(self._compare_numeric_metric(
            key="dom_ready",
            label="Document Processing Time",
            before=older_dom,
            after=newer_dom,
            unit="ms",
            lower_is_better=True,
            can_compare=(older_status == "completed" and newer_status == "completed")
        ))

        # 3. HTML Payload Size (KB)
        older_size = older_perf.get("pageSizeKb")
        newer_size = newer_perf.get("pageSizeKb")
        measurements.append(self._compare_numeric_metric(
            key="page_size",
            label="HTML Page Size",
            before=older_size,
            after=newer_size,
            unit="KB",
            lower_is_better=True,
            can_compare=(older_status == "completed" and newer_status == "completed")
        ))

        # 4. Mobile Viewport Meta Presence (Boolean)
        older_vp = older_perf.get("mobileViewportPresent")
        newer_vp = newer_perf.get("mobileViewportPresent")
        measurements.append(self._compare_boolean_metric(
            key="mobile_viewport",
            label="Responsive Viewport Meta",
            before=older_vp,
            after=newer_vp,
            true_is_better=True,
            can_compare=(older_status == "completed" and newer_status == "completed")
        ))

        # 5. DNS Resolution Latency (ms)
        older_dns_ms = older_dns.get("responseMs")
        newer_dns_ms = newer_dns.get("responseMs")
        older_dns_ok = older_dns.get("aRecord") not in ("N/A", "Unresolved", "None", "", None) and older_status == "completed"
        newer_dns_ok = newer_dns.get("aRecord") not in ("N/A", "Unresolved", "None", "", None) and newer_status == "completed"
        measurements.append(self._compare_numeric_metric(
            key="dns_latency",
            label="DNS Resolution Time",
            before=older_dns_ms,
            after=newer_dns_ms,
            unit="ms",
            lower_is_better=True,
            can_compare=(older_dns_ok and newer_dns_ok),
            allow_negative=False
        ))

        # Check for TLS diagnostic failures
        older_tls_failed = (
            older_ssl.get("issuer") == "Connection Failed"
            or older_ssl.get("tlsVersion") in ("None", "N/A", "")
            or older_status != "completed"
        )
        newer_tls_failed = (
            newer_ssl.get("issuer") == "Connection Failed"
            or newer_ssl.get("tlsVersion") in ("None", "N/A", "")
            or newer_status != "completed"
        )
        can_compare_ssl = not (older_tls_failed or newer_tls_failed)

        # 6. TLS Certificate Validity (Boolean)
        older_ssl_valid = older_ssl.get("valid")
        newer_ssl_valid = newer_ssl.get("valid")
        measurements.append(self._compare_boolean_metric(
            key="tls_validity",
            label="TLS Certificate Validity",
            before=older_ssl_valid,
            after=newer_ssl_valid,
            true_is_better=True,
            can_compare=can_compare_ssl
        ))

        # 7. Certificate Days Remaining (Days)
        older_exp = older_ssl.get("expiresDays")
        newer_exp = newer_ssl.get("expiresDays")
        measurements.append(self._compare_cert_expiry_metric(
            before=older_exp,
            after=newer_exp,
            older_valid=bool(older_ssl_valid),
            newer_valid=bool(newer_ssl_valid),
            can_compare=can_compare_ssl
        ))

        # 8. TLS Protocol Version (Categorical / Semantic)
        older_tls_ver = older_ssl.get("tlsVersion")
        newer_tls_ver = newer_ssl.get("tlsVersion")
        measurements.append(self._compare_tls_version_metric(
            before=older_tls_ver,
            after=newer_tls_ver
        ))

        # 9. HTTP Status Code (Semantic)
        older_http_code = self._extract_http_status_code(older_audit)
        newer_http_code = self._extract_http_status_code(newer_audit)
        measurements.append(self._compare_http_status_metric(
            before=older_http_code,
            after=newer_http_code,
            older_status=older_status,
            newer_status=newer_status
        ))

        return measurements

    def _compare_numeric_metric(
        self,
        key: str,
        label: str,
        before: Any,
        after: Any,
        unit: str,
        lower_is_better: bool = True,
        can_compare: bool = True,
        allow_negative: bool = False
    ) -> Dict[str, Any]:
        """Compares numeric metrics avoiding division by zero, invalid units, or negative numbers."""
        if not can_compare or before is None or after is None:
            return {
                "key": key,
                "label": label,
                "before": before,
                "after": after,
                "unit": unit,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "inconclusive",
                "reason": "Measurement incomplete or unavailable in one of the audits."
            }

        try:
            b_val = float(before)
            a_val = float(after)
        except (ValueError, TypeError):
            return {
                "key": key,
                "label": label,
                "before": before,
                "after": after,
                "unit": unit,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "not_comparable",
                "reason": "Non-numeric metric values cannot be numerically compared."
            }

        if not allow_negative and (b_val < 0 or a_val < 0):
            return {
                "key": key,
                "label": label,
                "before": before,
                "after": after,
                "unit": unit,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "not_comparable",
                "reason": "Negative values are invalid for physical latency or payload size measurements."
            }

        diff = round(a_val - b_val, 2)
        # Avoid division by zero
        pct_change = None
        if b_val != 0:
            pct_change = round(((a_val - b_val) / abs(b_val)) * 100, 1)

        if diff == 0:
            direction = "unchanged"
        elif (diff < 0 and lower_is_better) or (diff > 0 and not lower_is_better):
            direction = "improved"
        else:
            direction = "degraded"

        return {
            "key": key,
            "label": label,
            "before": b_val if not b_val.is_integer() else int(b_val),
            "after": a_val if not a_val.is_integer() else int(a_val),
            "unit": unit,
            "change": diff if not diff.is_integer() else int(diff),
            "changePercent": pct_change,
            "direction": direction,
            "status": "comparable",
            "reason": None
        }

    def _compare_boolean_metric(
        self,
        key: str,
        label: str,
        before: Any,
        after: Any,
        true_is_better: bool = True,
        can_compare: bool = True
    ) -> Dict[str, Any]:
        if not can_compare or before is None or after is None:
            return {
                "key": key,
                "label": label,
                "before": before,
                "after": after,
                "unit": None,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "inconclusive",
                "reason": "Observation missing in one of the audits."
            }

        b_bool = bool(before)
        a_bool = bool(after)

        if b_bool == a_bool:
            direction = "unchanged"
        elif (a_bool and true_is_better) or (not a_bool and not true_is_better):
            direction = "improved"
        else:
            direction = "degraded"

        return {
            "key": key,
            "label": label,
            "before": "Yes" if b_bool else "No",
            "after": "Yes" if a_bool else "No",
            "unit": None,
            "change": None,
            "changePercent": None,
            "direction": direction,
            "status": "comparable",
            "reason": None
        }

    def _compare_cert_expiry_metric(
        self,
        before: Any,
        after: Any,
        older_valid: bool,
        newer_valid: bool,
        can_compare: bool = True
    ) -> Dict[str, Any]:
        """
        Compares certificate days remaining.
        Guarantees:
        - Missing or diagnostic-failed TLS is reported as inconclusive.
        - Expired/invalid certificates are never reported as improved.
        - Renewal is only marked improved when newer certificate is confirmed valid.
        - Natural time decay without entering warning window (<= 14 days) is neutral.
        """
        if not can_compare or before is None or after is None:
            return {
                "key": "cert_expiry",
                "label": "Certificate Days Remaining",
                "before": before,
                "after": after,
                "unit": "days",
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "inconclusive",
                "reason": "Certificate expiry data missing or diagnostic failed in one or both audits."
            }

        try:
            b_days = int(before)
            a_days = int(after)
        except (ValueError, TypeError):
            return {
                "key": "cert_expiry",
                "label": "Certificate Days Remaining",
                "before": before,
                "after": after,
                "unit": "days",
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "not_comparable",
                "reason": "Non-integer certificate expiry values cannot be evaluated."
            }

        diff = a_days - b_days

        # Case 1: Validity transitions
        if not older_valid and newer_valid:
            direction = "improved"
        elif older_valid and not newer_valid:
            direction = "degraded"
        elif not older_valid and not newer_valid:
            # Both invalid/expired
            direction = "unchanged"
        elif newer_valid and a_days > b_days:
            # Confirmed valid certificate renewal
            direction = "improved"
        elif a_days < 0 and b_days >= 0:
            # Expired between audits
            direction = "degraded"
        elif a_days <= 14 and b_days > 14:
            # Entered warning threshold (<= 14 days)
            direction = "degraded"
        elif diff == 0:
            direction = "unchanged"
        else:
            # Both valid with natural time decay or adequate remaining validity
            direction = "neutral"

        pct_change = round(((a_days - b_days) / abs(b_days)) * 100, 1) if b_days != 0 else None

        return {
            "key": "cert_expiry",
            "label": "Certificate Days Remaining",
            "before": b_days,
            "after": a_days,
            "unit": "days",
            "change": diff,
            "changePercent": pct_change,
            "direction": direction,
            "status": "comparable",
            "reason": None
        }

    def _compare_tls_version_metric(self, before: Any, after: Any) -> Dict[str, Any]:
        """
        Compares TLS protocol versions categorically based on security hierarchy:
        TLSv1.3 > TLSv1.2 > TLSv1.1 > TLSv1.0.
        Unknown or unverified versions are treated as not comparable or inconclusive.
        """
        ranking = {
            "tlsv1.3": 4,
            "tlsv1.2": 3,
            "tlsv1.1": 2,
            "tlsv1.0": 1,
            "sslv3": 0,
        }

        b_str = str(before or "None").strip()
        a_str = str(after or "None").strip()

        # Both missing or none
        if b_str.lower() in ("none", "n/a", "") and a_str.lower() in ("none", "n/a", ""):
            return {
                "key": "tls_version",
                "label": "TLS Protocol Version",
                "before": b_str,
                "after": a_str,
                "unit": None,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "inconclusive",
                "reason": "Neither audit recorded a negotiated TLS protocol version."
            }

        # Check for unknown protocol versions
        b_key = b_str.lower()
        a_key = a_str.lower()

        if (b_key not in ranking and b_key not in ("none", "n/a", "")) or \
           (a_key not in ranking and a_key not in ("none", "n/a", "")):
            return {
                "key": "tls_version",
                "label": "TLS Protocol Version",
                "before": b_str,
                "after": a_str,
                "unit": None,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "not_comparable",
                "reason": f"Unrecognized TLS protocol version ('{b_str}' vs '{a_str}') cannot be safely evaluated in security ranking."
            }

        b_rank = ranking.get(b_key, 0)
        a_rank = ranking.get(a_key, 0)

        if b_rank == a_rank:
            direction = "unchanged"
        elif a_rank > b_rank:
            direction = "improved"
        else:
            direction = "degraded"

        return {
            "key": "tls_version",
            "label": "TLS Protocol Version",
            "before": b_str,
            "after": a_str,
            "unit": None,
            "change": None,
            "changePercent": None,
            "direction": direction,
            "status": "comparable",
            "reason": None
        }

    def _extract_http_status_code(self, audit: Any) -> Optional[int]:
        """Extracts HTTP status code from findings or headers."""
        findings = _get_field(audit, "findings", default=[])
        for f in findings:
            code = _get_field(f, "http_status", "httpStatus")
            if code is not None and isinstance(code, int) and code > 0:
                return code
        return None

    def _compare_http_status_metric(
        self,
        before: Optional[int],
        after: Optional[int],
        older_status: str,
        newer_status: str
    ) -> Dict[str, Any]:
        """
        Compares HTTP status codes using semantic categories rather than simple numeric subtraction.
        - 2xx / 3xx: Success / Reachable
        - 4xx: Client Error / Not Found
        - 5xx: Server Failure
        - 0 or None: Unreachable / Timeout
        """
        if before is None or after is None:
            return {
                "key": "http_status",
                "label": "HTTP Response Status Code",
                "before": before or "N/A",
                "after": after or "N/A",
                "unit": None,
                "change": None,
                "changePercent": None,
                "direction": "unknown",
                "status": "inconclusive",
                "reason": "HTTP response code missing from one or both audits."
            }

        b_code = int(before)
        a_code = int(after)

        def is_ok(code: int) -> bool:
            return 200 <= code < 400

        def is_err(code: int) -> bool:
            return code >= 400 or code == 0

        if b_code == a_code:
            direction = "unchanged"
        elif is_err(b_code) and is_ok(a_code):
            direction = "improved"
        elif is_ok(b_code) and is_err(a_code):
            direction = "degraded"
        elif b_code >= 500 and 400 <= a_code < 500:
            # 500 server crash to 404 is still an error but server is at least responding
            direction = "improved"
        elif 400 <= b_code < 500 and a_code >= 500:
            direction = "degraded"
        else:
            direction = "neutral"

        return {
            "key": "http_status",
            "label": "HTTP Response Status Code",
            "before": b_code,
            "after": a_code,
            "unit": None,
            "change": None,  # Omit meaningless arithmetic difference like 200 - 500 = -300
            "changePercent": None,
            "direction": direction,
            "status": "comparable",
            "reason": None
        }


audit_comparison_service = AuditComparisonService()
compare_audits = audit_comparison_service.compare_audits
