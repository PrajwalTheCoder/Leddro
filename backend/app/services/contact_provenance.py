"""
Contact Intelligence and Email Provenance Service for Leddro.

Prevents Leddro from confusing a syntactically valid email address with a verified business contact.
Enforces rigorous provenance tracking, distinguishes search-snippet candidates from official
business channels, filters out food blogger/review addresses, and assesses contact confidence.

Explicit contact confidence states:
- 'official_source': Extracted directly from business's verified official website contact/about pages.
- 'corroborated': Confirmed across multiple independent reputable sources (website + directory).
- 'provider_verified': B2B provider (Hunter.io) verified with high deliverability score.
- 'third_party_candidate': Found in a public directory (Justdial, IndiaMART) connected to the listing.
- 'unverified': Extracted from a search engine snippet; owner relationship is unconfirmed.
- 'conflicting': Address belongs to a food blogger, aggregator helpdesk, or third-party reviewer.
- 'none': No email address discovered.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.services.email_scraper import is_valid_email_candidate, verify_email_mx
from backend.app.services.domain_utils import clean_domain_string, get_organizational_domain, tokenize_name

# Keywords indicating food bloggers, review accounts, or PR influencers
BLOGGER_OR_REVIEWER_KEYWORDS = {
    "blogger", "blog", "diaries", "gobble", "foodie", "critic", "review",
    "lifestyle", "influencer", "journeys", "wanderer", "nomad", "traveler",
    "craver", "chefreview", "curator"
}

# Known customer support / generic aggregator usernames
AGGREGATOR_USERNAMES = {
    "support", "help", "care", "info", "contact", "marketing", "billing",
    "grievance", "nodal", "partner", "merchant", "orders"
}


def is_blogger_or_reviewer_email(email: str, business_name: str) -> bool:
    """
    Detects whether an email address belongs to a food blogger, restaurant reviewer,
    or social influencer rather than the business owner.
    
    Example: 'thegobblediaries@gmail.com' for 'MINTMORSEL RESTAURANT' -> True
    """
    if not email or "@" not in email:
        return False
    user, domain = email.strip().lower().split("@", 1)
    
    # Check for blogger/reviewer keywords in username
    if any(kw in user for kw in BLOGGER_OR_REVIEWER_KEYWORDS):
        # Unless the business itself is explicitly named that
        biz_tokens = tokenize_name(business_name)
        if not any(token in user for token in biz_tokens if len(token) > 3):
            return True

    return False


def is_aggregator_support_email(email: str) -> bool:
    """Detects emails belonging to third-party delivery/directory platforms (e.g. support@zomato.com)."""
    if not email or "@" not in email:
        return False
    user, domain = email.strip().lower().split("@", 1)
    from backend.app.services.domain_utils import is_aggregator_or_directory_domain
    if is_aggregator_or_directory_domain(domain):
        return True
    return False


def classify_contact_provenance(
    email: Optional[str],
    business_name: str,
    source_type: str,  # 'official_website', 'directory', 'search_snippet', 'hunter_io'
    source_url: Optional[str] = None,
    source_provider: Optional[str] = None,
    provider_confidence: Optional[int] = None,
    multi_channel_count: int = 1,
    identity_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates discovered email against business identity to establish provenance,
    verifies MX deliverability, and assigns explicit confidence status.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    if not email or not email.strip():
        return {
            "email": None,
            "status": "none",
            "confidence_score": 0,
            "source_type": "none",
            "source_provider": source_provider or "none",
            "source_url": None,
            "mx_verified": False,
            "mailbox_confirmed": False,
            "is_official_domain": False,
            "rationale": "No email address discovered for business.",
            "discovered_at": now_iso
        }

    clean_email = email.strip().lower()
    
    # Check syntax
    if not is_valid_email_candidate(clean_email):
        return {
            "email": clean_email,
            "status": "conflicting",
            "confidence_score": 0,
            "source_type": source_type,
            "source_provider": source_provider or "none",
            "source_url": source_url,
            "mx_verified": False,
            "mailbox_confirmed": False,
            "is_official_domain": False,
            "rationale": "Address failed candidate syntax validation (junk extension or template domain).",
            "discovered_at": now_iso
        }

    # Check for aggregator customer support emails (e.g., info@justdial.com, support@zomato.com)
    if is_aggregator_support_email(clean_email):
        return {
            "email": clean_email,
            "status": "conflicting",
            "confidence_score": 10,
            "source_type": source_type,
            "source_provider": source_provider or "none",
            "source_url": source_url,
            "mx_verified": True,
            "mailbox_confirmed": False,
            "is_official_domain": False,
            "rationale": f"Email '{clean_email}' belongs to a directory or aggregator customer service desk, not the business.",
            "discovered_at": now_iso
        }

    # Check for food blogger / reviewer addresses
    if is_blogger_or_reviewer_email(clean_email, business_name):
        return {
            "email": clean_email,
            "status": "conflicting",
            "confidence_score": 15,
            "source_type": source_type,
            "source_provider": source_provider or "none",
            "source_url": source_url,
            "mx_verified": True,
            "mailbox_confirmed": False,
            "is_official_domain": False,
            "rationale": (
                f"Address '{clean_email}' belongs to a food blogger, influencer, or reviewer who posted about '{business_name}'. "
                "Must not be treated as the business owner's contact."
            ),
            "discovered_at": now_iso
        }

    # Check DNS MX records
    has_mx = verify_email_mx(clean_email)
    if not has_mx:
        return {
            "email": clean_email,
            "status": "unverified",
            "confidence_score": 20,
            "source_type": source_type,
            "source_provider": source_provider or "none",
            "source_url": source_url,
            "mx_verified": False,
            "mailbox_confirmed": False,
            "is_official_domain": False,
            "rationale": f"Domain for '{clean_email}' lacks active DNS MX mail routing records.",
            "discovered_at": now_iso
        }

    user, domain = clean_email.split("@", 1)
    biz_tokens = tokenize_name(business_name)
    has_name_token = any(t in user or t in domain for t in biz_tokens if len(t) > 2)

    # Status classification based on source type and corroboration
    if source_type == "official_website" and identity_status in ("conflicting", "uncertain"):
        # The page the email came from is not confirmed to belong to this business.
        status = "unverified"
        conf_score = 35
        rationale = (
            f"Extracted from {source_url or 'a website'}, but that website's association with "
            f"'{business_name}' is {identity_status}. Treat as unverified until the website is confirmed."
        )
    elif source_type == "official_website":
        status = "official_source"
        conf_score = 95 if identity_status in ("verified",) else 85
        rationale = f"Extracted directly from business website ({source_url or 'homepage'}). DNS MX active; mailbox not confirmed."
    elif source_type == "hunter_io":
        status = "provider_verified"
        conf_score = provider_confidence or 85
        rationale = f"Hunter.io verified B2B email with {conf_score}% deliverability confidence."
    elif multi_channel_count >= 2:
        status = "corroborated"
        conf_score = 85
        rationale = f"Address corroborated across multiple public business channels. DNS MX verified."
    elif source_type == "directory":
        status = "third_party_candidate"
        conf_score = 65
        rationale = f"Discovered on public directory listing ({source_provider or 'directory'}). Direct ownership unconfirmed."
    elif source_type == "search_snippet":
        # Search snippets remain unverified unless there is strong token alignment
        if has_name_token:
            status = "unverified"
            conf_score = 45
            rationale = (
                f"Address discovered in search engine snippet. Contains business keywords but "
                "direct ownership has not been independently verified."
            )
        else:
            status = "unverified"
            conf_score = 30
            rationale = (
                f"Discovered in search snippet for '{business_name}' without confirmed association. "
                "Requires operator review before outreach."
            )
    else:
        status = "unverified"
        conf_score = 40
        rationale = "Discovered via external source without confirmed ownership."

    return {
        "email": clean_email,
        "status": status,
        "confidence_score": conf_score,
        "source_type": source_type,
        "source_provider": source_provider or "crawler",
        "source_url": source_url,
        "mx_verified": True,
        "mailbox_confirmed": False,  # MX proves domain routing, not specific inbox
        "is_official_domain": source_type == "official_website",
        "rationale": rationale,
        "discovered_at": now_iso
    }
