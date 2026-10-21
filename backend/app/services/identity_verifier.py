"""
Evidence-based Business Identity and Website Verification Service for Leddro.

Determines whether Leddro correctly associates each discovered business with its
real website and location, preventing false associations with third-party aggregators,
unrelated entities, or discontinued platforms.

Produces explicit statuses:
- 'verified': High-confidence match corroborated by name tokens, geo/phone alignment, or official registry.
- 'likely_match': Strong domain token match with geographic consistency, pending deeper bidirectional check.
- 'uncertain': Ambiguous or weak signals, generic name overlap, or unverified search match.
- 'conflicting': Domain clearly belongs to another business, an aggregator/portal, or different geographic region.
- 'not_found': Available discovery and crawl checks confirmed no standalone official website was found.
- 'not_checked': Newly recorded lead where identity verification has not yet run.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.services.domain_utils import (
    clean_domain_string,
    get_organizational_domain,
    is_aggregator_or_directory_domain,
    calculate_domain_name_similarity,
    tokenize_name
)

# Known discontinued platforms that are no longer operational
DISCONTINUED_PLATFORMS = {"business.site", "negocio.site"}


def verify_business_identity(
    business_name: str,
    location: Optional[Dict[str, str]] = None,
    website_url: Optional[str] = None,
    phone: Optional[str] = None,
    source_provider: Optional[str] = None,
    raw_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates business identity and candidate website association.
    Returns a structured verification result with explicit status and traceable evidence.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    location = location or {}
    city = location.get("city", "").strip()
    state = location.get("state", "").strip()

    reasons: List[str] = []
    conflicting_domains: List[str] = []

    # Case 1: No website registered or candidate provided
    if not website_url or not website_url.strip():
        return {
            "status": "not_found",
            "claim": "no_website_discovered",
            "confidence_score": 0.3,
            "reasons": [
                "No website was returned by the discovery provider. This does NOT confirm the business "
                "lacks a website; no independent search or crawl has established absence."
            ],
            "conflicting_domains": [],
            "name_similarity": 0.0,
            "is_aggregator": False,
            "is_discontinued": False,
            "canonical_url": None,
            "verified_at": now_iso
        }

    clean_domain = clean_domain_string(website_url)
    org_domain = get_organizational_domain(clean_domain)

    # Case 2: Check for discontinued website builder platforms (e.g. Google Business Site shutdown)
    is_discontinued = any(clean_domain.endswith(p) for p in DISCONTINUED_PLATFORMS)
    if is_discontinued:
        reasons.append(
            f"Domain '{clean_domain}' is hosted on Google Business Sites (.business.site), "
            "which was discontinued and shut down by Google in March 2024. Domain no longer routes to active site."
        )
        return {
            "status": "conflicting",
            "confidence_score": 0.95,
            "reasons": reasons,
            "conflicting_domains": [clean_domain],
            "name_similarity": 0.5,
            "is_aggregator": False,
            "is_discontinued": True,
            "canonical_url": website_url,
            "verified_at": now_iso
        }

    # Case 3: Check for known aggregators, directories, and social platforms
    is_aggregator = is_aggregator_or_directory_domain(clean_domain)
    if is_aggregator:
        reasons.append(
            f"Domain '{clean_domain}' is a third-party directory, delivery aggregator, or platform profile "
            f"(e.g., Justdial, Zomato, Swiggy, Instagram, Facebook), not an independent official business website."
        )
        conflicting_domains.append(clean_domain)
        return {
            "status": "conflicting",
            "confidence_score": 0.95,
            "reasons": reasons,
            "conflicting_domains": conflicting_domains,
            "name_similarity": 0.0,
            "is_aggregator": True,
            "is_discontinued": False,
            "canonical_url": website_url,
            "verified_at": now_iso
        }

    # Case 4: Calculate domain name token similarity
    sim_score = calculate_domain_name_similarity(business_name, clean_domain)

    # Case 5: Evaluate Provider Provenance
    # If source is OSM with dedicated website tag and high token similarity
    is_official_osm = source_provider in ("osm", "osm_overpass", "osm_nominatim")

    if sim_score >= 0.85:
        # Name/domain similarity is circumstantial: it never proves ownership on its own.
        # 'verified' requires independent corroboration (e.g. reciprocal social link, matching
        # phone/address on the site), which callers may upgrade via upgrade_with_corroboration().
        status = "likely_match"
        conf_score = 0.8
        reasons.append(
            f"Domain '{clean_domain}' matches business name keywords ({int(sim_score * 100)}% token alignment). "
            "Name similarity alone does not establish ownership; no independent corroboration yet."
        )
    elif sim_score >= 0.6:
        # Moderate token similarity
        status = "likely_match"
        conf_score = 0.75
        reasons.append(
            f"Domain '{clean_domain}' contains major business name tokens ({int(sim_score * 100)}% match), "
            "but requires secondary corroboration."
        )
    elif sim_score > 0.0:
        # Weak token match
        status = "uncertain"
        conf_score = 0.45
        reasons.append(
            f"Domain '{clean_domain}' has only weak token overlap ({int(sim_score * 100)}%) with '{business_name}'."
        )
    else:
        # 0.0 token similarity. Brands legitimately use unrelated domains (parent hotel group, etc.),
        # so this is 'uncertain', not proof of conflict. Flag the domain so operators can review it;
        # website-specific outreach is withheld for any non-verified/likely identity.
        status = "uncertain"
        conf_score = 0.25
        conflicting_domains.append(clean_domain)
        reasons.append(
            f"Domain '{clean_domain}' shares no name tokens with '{business_name}'. It may belong to a "
            "parent company, another business, or an unmapped portal; ownership cannot be confirmed."
        )

    return {
        "status": status,
        "confidence_score": conf_score,
        "reasons": reasons,
        "conflicting_domains": conflicting_domains,
        "name_similarity": sim_score,
        "is_aggregator": False,
        "is_discontinued": False,
        "canonical_url": website_url,
        "verified_at": now_iso
    }
