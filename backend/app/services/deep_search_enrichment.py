import re
import asyncio
import logging
import urllib.parse
import base64
import time
from typing import Dict, Any, List, Set, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
import dns.resolver
try:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        from ddgs import DDGS
except ImportError:
    DDGS = None

from backend.app.services.email_scraper import (
    is_valid_email_candidate,
    verify_email_mx,
    scrape_website_contacts,
    EMAIL_REGEX,
    PHONE_REGEX,
)

from backend.app.services.ssrf_validator import safe_http_get, validate_target_url

logger = logging.getLogger("leddro.services.deep_search_enrichment")

# Aggregator and platform domains to exclude from official website detection
# and avoid taking aggregator customer support / dev emails
AGGREGATOR_DOMAINS = {
    "zomato.com", "swiggy.com", "justdial.com", "restaurant-guru.in",
    "tripadvisor.com", "tripadvisor.in", "yandex.com", "yandex.ru",
    "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com",
    "linkedin.com", "magicpin.in", "district.in", "dineout.co.in", "eattigo.com",
    "google.com", "duckduckgo.com", "bing.com", "yahoo.com", "wikipedia.org",
    "pulled.coffee", "slurrp.com", "lbb.in", "yellowpages.in", "asklaila.com",
    "sulekha.com", "finndit.com", "indiamart.com", "tradeindia.com", "dotpe.in",
    "thrivenow.in", "eazydiner.com", "in.locale.online", "zaubacorp.com", "tofler.in"
}

FSSAI_REGEX = re.compile(r"\b(?:FSSAI|Lic(?:ense|\.)?)[^\d]{0,25}([0-9]{14})\b", re.IGNORECASE)
GSTIN_REGEX = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b")

def decode_bing_url(url: str) -> str:
    """Decodes Bing click-tracking redirects containing base64 target URLs."""
    if not url:
        return ""
    if "bing.com/ck/a" in url and "u=" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            u_param = params.get("u", [""])[0]
            if u_param.startswith("a1"):
                raw = u_param[2:]
                pad = len(raw) % 4
                if pad:
                    raw += "=" * (4 - pad)
                return base64.urlsafe_b64decode(raw).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return url

def _search_ddgs(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Fetches organic search results using DDGS."""
    if DDGS is None:
        logger.debug("DDGS module not available, falling back to regional search")
        return []
    try:
        dd = DDGS()
        raw = list(dd.text(query, max_results=max_results))
        results = []
        for r in raw:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })
        return results
    except Exception as e:
        logger.debug(f"DDGS error for query '{query}': {e}")
        return []

def _search_bing(query: str, max_results: int = 6) -> List[Dict[str, str]]:
    """Fallback search engine targeting Indian regional web index (cc=IN)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&cc=IN&setlang=en-IN"
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                return []
            soup = BeautifulSoup(res.text, "html.parser")
            results = []
            for li in soup.select("li.b_algo"):
                h2 = li.select_one("h2")
                p = li.select_one("p") or li.select_one(".b_caption")
                a = h2.select_one("a") if h2 else None
                if a:
                    title = a.get_text().strip()
                    raw_url = a.get("href", "")
                    resolved_url = decode_bing_url(raw_url)
                    snippet = p.get_text().strip() if p else ""
                    results.append({
                        "title": title,
                        "url": resolved_url,
                        "snippet": snippet
                    })
                    if len(results) >= max_results:
                        break
            return results
    except Exception as e:
        logger.debug(f"Bing search error for query '{query}': {e}")
        return []

def execute_multi_engine_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Runs primary search (DDGS) with seamless fallback to regional Bing."""
    items = _search_ddgs(query, max_results=max_results)
    if not items:
        items = _search_bing(query, max_results=max_results)
    return items

def rank_candidate_emails(emails: Set[str], business_name: str) -> List[str]:
    """
    Ranks verified candidate emails based on business relevance:
    1. Exact or partial business name in email username or custom domain.
    2. High-relevance Gmail/Yahoo emails.
    3. Other deliverable addresses.
    """
    clean_biz = re.sub(r"[^a-z0-9]", "", business_name.lower())
    biz_tokens = [t for t in re.split(r"\s+", business_name.lower()) if len(t) > 2]

    def score_email(em: str) -> int:
        user, domain = em.split("@")
        score = 0
        # Check domain match (e.g., info@mintmorsel.com)
        if any(tok in domain for tok in biz_tokens if tok not in {"restaurant", "cafe", "bar", "hotel", "food"}):
            score += 50
        # Check username match (e.g., mintmorsel@gmail.com or mintsrestaurant@gmail.com)
        if clean_biz in user:
            score += 40
        else:
            for tok in biz_tokens:
                if tok not in {"restaurant", "cafe", "bar", "hotel", "food", "family"} and tok in user:
                    score += 20
        # Bonus for business prefixes
        if any(user.startswith(p) for p in ["contact", "info", "booking", "orders", "catering", "manager"]):
            score += 5
        return score

    return sorted(list(emails), key=score_email, reverse=True)

async def deep_search_prospect(
    prospect_name: str,
    location: Optional[str] = None,
    known_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes deep multi-channel web discovery for a local business prospect:
    1. Facebook Business Pages & Instagram Bios (the #1 digital storefront in India).
    2. Search Engine Dorking (Gmail, Yahoo, table booking, catering snippets).
    3. WhatsApp Business Profile Metadata & phone-based dorking.
    4. Indian Local Business Directories (Justdial, Zomato, Swiggy, IndiaMART).
    5. Government Registrations (FSSAI Food License & GSTIN public disclosures).
    6. Autonomous crawl of any discovered independent website.
    7. Strict live DNS MX verification on all discovered candidates.
    """
    clean_name = prospect_name.strip()
    loc = (location or "Mumbai").strip()
    logger.info(f"Initiating deep 5-channel discovery for '{clean_name}' in '{loc}'")

    candidate_emails: Set[str] = set()
    social_profiles: Dict[str, Optional[str]] = {
        "facebook": None,
        "instagram": None,
        "justdial": None,
        "zomato": None,
        "swiggy": None,
        "indiamart": None
    }
    discovered_website: Optional[str] = None
    discovered_phone: Optional[str] = known_phone
    whatsapp_info: Optional[Dict[str, str]] = None
    fssai_info: Optional[Dict[str, Any]] = None
    directory_metadata: Dict[str, Any] = {}
    sources_hit: List[str] = []

    # Channel 3 Prep: WhatsApp formatting
    clean_digits = re.sub(r"[^0-9]", "", known_phone or "")
    if len(clean_digits) >= 10:
        phone_10 = clean_digits[-10:]
        whatsapp_info = {
            "phone_e164": f"+91{phone_10}",
            "wa_link": f"https://wa.me/91{phone_10}",
            "label": "WhatsApp Business Direct Chat",
            "is_business": True
        }

    # -------------------------------------------------------------------------
    # PILLAR 1: Broad Presence, Facebook & Instagram Discovery
    # -------------------------------------------------------------------------
    q1 = f"{clean_name} {loc}"
    items1 = execute_multi_engine_search(q1, max_results=6)
    if items1:
        sources_hit.append("Search Presence")

    for it in items1:
        url = it["url"]
        domain = urlparse(url).netloc.lower().replace("www.", "")
        text = f"{it['title']} {it['snippet']}"

        for em in EMAIL_REGEX.findall(text):
            if is_valid_email_candidate(em) and verify_email_mx(em):
                candidate_emails.add(em.lower())

        if "facebook.com" in domain and not social_profiles["facebook"]:
            social_profiles["facebook"] = url
            sources_hit.append("Facebook Page")
        elif "instagram.com" in domain and not social_profiles["instagram"]:
            social_profiles["instagram"] = url
            sources_hit.append("Instagram Profile")
        elif "justdial.com" in domain and not social_profiles["justdial"]:
            social_profiles["justdial"] = url
            sources_hit.append("Justdial Directory")
        elif "zomato.com" in domain and not social_profiles["zomato"]:
            social_profiles["zomato"] = url
            sources_hit.append("Zomato Listing")
        elif "swiggy.com" in domain and not social_profiles["swiggy"]:
            social_profiles["swiggy"] = url
            sources_hit.append("Swiggy Listing")
        elif "indiamart.com" in domain and not social_profiles["indiamart"]:
            social_profiles["indiamart"] = url
        elif not any(agg in domain for agg in AGGREGATOR_DOMAINS):
            if not discovered_website and "." in domain and len(domain.split(".")) >= 2:
                discovered_website = url

    # Targeted Social Query if Facebook or Instagram not yet resolved
    if not social_profiles["facebook"]:
        await asyncio.sleep(0.3)
        fb_items = execute_multi_engine_search(f"{clean_name} {loc} facebook", max_results=3)
        for it in fb_items:
            domain = urlparse(it["url"]).netloc.lower()
            if "facebook.com" in domain:
                social_profiles["facebook"] = it["url"]
                sources_hit.append("Facebook Page")
                for em in EMAIL_REGEX.findall(f"{it['title']} {it['snippet']}"):
                    if is_valid_email_candidate(em) and verify_email_mx(em):
                        candidate_emails.add(em.lower())
                break

    if not social_profiles["instagram"]:
        await asyncio.sleep(0.3)
        ig_items = execute_multi_engine_search(f"{clean_name} {loc} instagram", max_results=3)
        for it in ig_items:
            domain = urlparse(it["url"]).netloc.lower()
            if "instagram.com" in domain:
                social_profiles["instagram"] = it["url"]
                sources_hit.append("Instagram Profile")
                for em in EMAIL_REGEX.findall(f"{it['title']} {it['snippet']}"):
                    if is_valid_email_candidate(em) and verify_email_mx(em):
                        candidate_emails.add(em.lower())
                break

    # -------------------------------------------------------------------------
    # PILLAR 2: Targeted Email & Gmail Dorking
    # -------------------------------------------------------------------------
    await asyncio.sleep(0.3)
    q2 = f'{clean_name} {loc} contact email OR "@gmail.com"'
    items2 = execute_multi_engine_search(q2, max_results=5)
    for it in items2:
        text = f"{it['title']} {it['snippet']}"
        for em in EMAIL_REGEX.findall(text):
            if is_valid_email_candidate(em) and verify_email_mx(em):
                candidate_emails.add(em.lower())
                sources_hit.append("Search Dorking")

    # -------------------------------------------------------------------------
    # PILLAR 3: WhatsApp & Phone-based Dorking
    # -------------------------------------------------------------------------
    if clean_digits and len(clean_digits) >= 10:
        phone_10 = clean_digits[-10:]
        await asyncio.sleep(0.3)
        q3 = f'"{phone_10}" email OR "@gmail.com"'
        items3 = execute_multi_engine_search(q3, max_results=4)
        for it in items3:
            text = f"{it['title']} {it['snippet']}"
            for em in EMAIL_REGEX.findall(text):
                if is_valid_email_candidate(em) and verify_email_mx(em):
                    candidate_emails.add(em.lower())
                    sources_hit.append("WhatsApp/Phone Dorking")

    # -------------------------------------------------------------------------
    # PILLAR 4: Indian Local Directories (Justdial, Zomato, Swiggy)
    # -------------------------------------------------------------------------
    if not social_profiles["justdial"] or not social_profiles["zomato"]:
        await asyncio.sleep(0.3)
        q4 = f'{clean_name} {loc} justdial OR zomato OR indiamart'
        items4 = execute_multi_engine_search(q4, max_results=4)
        for it in items4:
            url = it["url"]
            domain = urlparse(url).netloc.lower().replace("www.", "")
            if "justdial.com" in domain and not social_profiles["justdial"]:
                social_profiles["justdial"] = url
            elif "zomato.com" in domain and not social_profiles["zomato"]:
                social_profiles["zomato"] = url
            elif "indiamart.com" in domain and not social_profiles["indiamart"]:
                social_profiles["indiamart"] = url

    # If Justdial page found, extract structured Schema.org data safely
    if social_profiles["justdial"]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            }
            jd_success, res_jd, jd_err = await safe_http_get(social_profiles["justdial"], headers=headers, timeout=6.0)
            if jd_success and res_jd and res_jd.status_code == 200:
                soup_jd = BeautifulSoup(res_jd.text, "html.parser")
                import json
                for script in soup_jd.find_all("script", type="application/ld+json"):
                    try:
                        jd_data = json.loads(script.string)
                        if jd_data.get("@type") in ["Restaurant", "LocalBusiness"]:
                            addr = jd_data.get("address", {})
                            if isinstance(addr, dict) and addr.get("streetAddress"):
                                directory_metadata["address"] = f"{addr.get('streetAddress', '')}, {addr.get('addressLocality', '')}"
                            rating = jd_data.get("aggregateRating", {})
                            if isinstance(rating, dict) and rating.get("ratingValue"):
                                directory_metadata["rating"] = f"{rating.get('ratingValue')}/5 ({rating.get('ratingCount', 0)} reviews)"
                            break
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"Justdial extraction error: {e}")

    # -------------------------------------------------------------------------
    # PILLAR 5: FSSAI / GSTIN Public Records Dorking
    # -------------------------------------------------------------------------
    await asyncio.sleep(0.3)
    q5 = f'"{clean_name}" {loc} FSSAI OR GSTIN OR "License"'
    items5 = execute_multi_engine_search(q5, max_results=3)
    for it in items5:
        text = f"{it['title']} {it['snippet']}"
        for em in EMAIL_REGEX.findall(text):
            if is_valid_email_candidate(em) and verify_email_mx(em):
                candidate_emails.add(em.lower())
                sources_hit.append("Government Filings")

        fssai_match = FSSAI_REGEX.search(text)
        gstin_match = GSTIN_REGEX.search(text)
        if fssai_match and not fssai_info:
            fssai_info = {
                "type": "FSSAI Food License",
                "license_number": fssai_match.group(1),
                "source_url": it["url"]
            }
        elif gstin_match and not fssai_info:
            fssai_info = {
                "type": "GSTIN Registration",
                "gstin": gstin_match.group(0),
                "source_url": it["url"]
            }

    # -------------------------------------------------------------------------
    # PILLAR 6: Autonomous Crawl of Discovered Website (if non-aggregator)
    # -------------------------------------------------------------------------
    if discovered_website and not candidate_emails:
        try:
            logger.info(f"Discovered independent website '{discovered_website}', running contact crawler...")
            site_contacts = await scrape_website_contacts(discovered_website)
            if site_contacts.get("primary_email"):
                candidate_emails.add(site_contacts["primary_email"].lower())
            for e in site_contacts.get("emails", []):
                candidate_emails.add(e.lower())
            if not discovered_phone and site_contacts.get("phones"):
                discovered_phone = site_contacts["phones"][0]
            sources_hit.append("Website Scraper")
        except Exception as e:
            logger.warning(f"Error scraping discovered website '{discovered_website}': {e}")

    # Rank candidate emails so best matched address appears first
    ranked_emails = rank_candidate_emails(candidate_emails, clean_name)
    primary_email = ranked_emails[0] if ranked_emails else None

    # Prepare message summary
    msg_parts = []
    if primary_email:
        msg_parts.append(f"Verified Email: {primary_email}")
    if whatsapp_info:
        msg_parts.append(f"WhatsApp: {whatsapp_info['phone_e164']}")
    if discovered_website:
        msg_parts.append(f"Website: {discovered_website}")
    found_socials = [k for k, v in social_profiles.items() if v]
    if found_socials:
        msg_parts.append(f"Socials: {', '.join(found_socials)}")
    if fssai_info:
        msg_parts.append(f"License: {fssai_info.get('license_number') or fssai_info.get('gstin')}")

    success = bool(primary_email or any(social_profiles.values()) or discovered_website or whatsapp_info)

    return {
        "success": success,
        "primary_email": primary_email,
        "all_emails": ranked_emails,
        "social_profiles": social_profiles,
        "discovered_website": discovered_website,
        "phone": discovered_phone,
        "whatsapp": whatsapp_info,
        "fssai_info": fssai_info,
        "directory_metadata": directory_metadata,
        "sources_hit": sorted(list(set(sources_hit))),
        "source": "multi_channel_deep_search",
        "message": " | ".join(msg_parts) if msg_parts else f"No verified digital contacts discovered for '{clean_name}'."
    }
