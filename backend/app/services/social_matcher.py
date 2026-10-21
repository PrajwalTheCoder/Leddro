"""
Social Profile Matching Service for Leddro.

Evaluates public profiles across Instagram, Facebook, LinkedIn, YouTube, and directories
to prevent associating fan pages, food bloggers, or unrelated individuals with target businesses.

Matching outcomes:
- 'reciprocal_match': Official website links to social profile and profile links back to website.
- 'strong_match': Profile handle/slug and title match business name keywords and locality.
- 'uncertain_match': Generic or unconfirmed search match lacking handle or location confirmation.
- 'incorrect_match': Confirmed to belong to a review blogger, fan page, or unrelated entity.
- 'not_found': Search executed but no valid profile discovered.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
from backend.app.services.domain_utils import tokenize_name

# Common fan/review keywords in social handles or titles
FAN_PAGE_KEYWORDS = {"fanpage", "review", "blogger", "guide", "lovers", "club", "unofficial", "explore"}


def evaluate_social_profile_match(
    platform: str,
    profile_url: Optional[str],
    business_name: str,
    location: Optional[Dict[str, str]] = None,
    official_website: Optional[str] = None,
    reciprocal_link_found: bool = False,
    page_title: Optional[str] = None,
    page_snippet: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates evidence for a discovered social profile URL.
    Returns structured match status, confidence, and explanatory evidence.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    location = location or {}
    city = location.get("city", "").strip()

    if not profile_url or not profile_url.strip():
        return {
            "platform": platform,
            "url": None,
            "match_status": "not_found",
            "confidence_score": 0.3,
            "evidence": (
                f"No {platform.capitalize()} profile was discovered by the available checks. "
                "This does not prove the business has no profile."
            ),
            "contradictory_info": None,
            "last_checked": now_iso
        }

    clean_url = profile_url.strip()
    parsed = urlparse(clean_url)
    path_slug = parsed.path.strip("/").lower()

    biz_tokens = tokenize_name(business_name)
    combined_biz = "".join(biz_tokens)
    text_corpus = f"{path_slug} {page_title or ''} {page_snippet or ''}".lower()

    # 1. Check for fan page / blogger indicators
    own_name_text = business_name.lower()
    if any(fp in path_slug and fp not in own_name_text for fp in FAN_PAGE_KEYWORDS):
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "incorrect_match",
            "confidence_score": 0.75,
            "evidence": f"Profile URL handle '{path_slug}' indicates a fan page, review account, or food blog.",
            "contradictory_info": "Handle contains fan page / reviewer keywords instead of official business brand.",
            "last_checked": now_iso
        }

    # 2. Reciprocal link verification
    if reciprocal_link_found:
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "reciprocal_match",
            "confidence_score": 0.99,
            "evidence": f"Verified bidirectional cross-link between official website ({official_website}) and {platform.capitalize()}.",
            "contradictory_info": None,
            "last_checked": now_iso
        }

    # 3. Handle / slug alignment
    handle_match = False
    distinctive_tokens = [t for t in biz_tokens if len(t) >= 4 and t not in {"cafe", "club", "shop", "food"}]
    primary_distinctive = distinctive_tokens[0] if distinctive_tokens else (biz_tokens[0] if biz_tokens else "")

    if combined_biz and (combined_biz in path_slug or path_slug.startswith(combined_biz)):
        handle_match = True
    elif primary_distinctive and primary_distinctive in path_slug:
        # e.g. 'creeda' in 'creedacafe'
        handle_match = True
    elif sum(1 for t in biz_tokens if t in path_slug) >= max(1, len(biz_tokens) - 1):
        handle_match = True

    # 4. Geographic consistency
    geo_match = bool(city and city.lower() in text_corpus)

    if handle_match and geo_match:
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "strong_match",
            "confidence_score": 0.88,
            "evidence": f"Handle '{path_slug}' closely matches business name and search corpus confirms locality '{city}'.",
            "contradictory_info": None,
            "last_checked": now_iso
        }
    elif handle_match:
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "strong_match",
            "confidence_score": 0.80,
            "evidence": f"Profile handle '{path_slug}' matches business name tokens.",
            "contradictory_info": "Locality could not be independently corroborated from snippet text.",
            "last_checked": now_iso
        }
    elif any(t in path_slug for t in biz_tokens if len(t) > 3):
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "uncertain_match",
            "confidence_score": 0.50,
            "evidence": f"Partial keyword match in handle '{path_slug}'. Unconfirmed without reciprocal backlink.",
            "contradictory_info": "Handle does not uniquely match full business brand name.",
            "last_checked": now_iso
        }
    else:
        return {
            "platform": platform,
            "url": clean_url,
            "match_status": "uncertain_match",
            "confidence_score": 0.35,
            "evidence": f"Discovered via search query but profile handle '{path_slug}' does not match brand name.",
            "contradictory_info": "Possible unrelated account or regional branch.",
            "last_checked": now_iso
        }
