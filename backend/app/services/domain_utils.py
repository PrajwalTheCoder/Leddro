"""
Domain and Public Suffix Utilities for Leddro.

Provides accurate organizational (apex) domain resolution for DNS queries (DMARC, SPF),
domain normalization, tokenization, and aggregator/directory domain detection.
Correctly handles common multi-part ccTLD public suffixes (such as .co.in, .org.in,
.net.in, .gov.in, .co.uk, .org.uk, .com.au, .net.au, etc.) without naive string splitting.
"""

import re
from typing import Optional, List, Set
from urllib.parse import urlparse

# Multi-part public suffixes where the second-level domain is a public registry category
MULTI_PART_PUBLIC_SUFFIXES: Set[str] = {
    # India
    "co.in", "net.in", "org.in", "gen.in", "firm.in", "ind.in", "nic.in", "gov.in", "ac.in", "edu.in", "res.in",
    # United Kingdom
    "co.uk", "org.uk", "me.uk", "ltd.uk", "plc.uk", "net.uk", "sch.uk", "ac.uk", "gov.uk",
    # Australia
    "com.au", "net.au", "org.au", "edu.au", "gov.au", "asn.au", "id.au",
    # New Zealand
    "co.nz", "net.nz", "org.nz", "govt.nz", "ac.nz", "geek.nz",
    # South Africa
    "co.za", "net.za", "org.za", "web.za", "gov.za", "ac.za",
    # Singapore & Japan & Brazil
    "com.sg", "net.sg", "org.sg", "edu.sg", "gov.sg",
    "co.jp", "ne.jp", "or.jp", "ac.jp", "go.jp",
    "com.br", "net.br", "org.br", "gov.br",
    # General second-level registries
    "com.mx", "org.mx", "gob.mx", "com.ar", "com.co", "com.my", "com.ph", "com.pk", "com.ng"
}

# Known directory, aggregator, and social domains to prevent misclassifying them as official standalone websites
AGGREGATOR_AND_DIRECTORY_DOMAINS: Set[str] = {
    # Food & Hospitality Aggregators
    "zomato.com", "swiggy.com", "justdial.com", "justdail.com", "restaurant-guru.in",
    "tripadvisor.com", "tripadvisor.in", "eazydiner.com", "dineout.co.in", "magicpin.in",
    "district.in", "eattigo.com", "slurrp.com", "lbb.in", "dotpe.in", "thrivenow.in",
    # General Directories & Classifieds
    "yellowpages.in", "yellowpages.com", "asklaila.com", "sulekha.com", "finndit.com",
    "indiamart.com", "tradeindia.com", "in.locale.online", "zaubacorp.com", "tofler.in",
    "yelp.com", "foursquare.com",
    # Social Platforms
    "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com", "linkedin.com",
    "pinterest.com", "threads.net", "tiktok.com",
    # Search & Encyclopedias
    "google.com", "duckduckgo.com", "bing.com", "yahoo.com", "wikipedia.org", "wikidata.org",
    # Discontinued website builder platforms
    "business.site", "negocio.site"
}

# Generic words to exclude when calculating domain-to-business-name token similarity
GENERIC_BUSINESS_STOPWORDS: Set[str] = {
    "restaurant", "cafe", "bar", "hotel", "food", "kitchen", "family", "dining", "dhaba",
    "pvt", "ltd", "llp", "inc", "co", "corp", "company", "services", "solutions", "group",
    "studio", "consultants", "enterprises", "associates", "industries", "agency", "shop",
    "store", "the", "and", "of", "in", "at", "for", "with", "mumbai", "pune", "delhi", "india"
}


def clean_domain_string(raw: str) -> str:
    """Extracts a clean, lowercase hostname from a URL or raw domain string."""
    if not raw:
        return ""
    text = raw.strip().lower()
    if "://" in text:
        try:
            parsed = urlparse(text)
            text = parsed.hostname or text
        except Exception:
            pass
    # Strip port or path if any
    text = text.split("/")[0].split(":")[0].strip()
    # Strip leading www.
    if text.startswith("www."):
        text = text[4:]
    return text


def get_organizational_domain(domain: str) -> str:
    """
    Extracts the organizational (apex/registrable) domain from a hostname.
    Correctly recognizes multi-part public suffixes such as .co.in, .org.uk, .com.au,
    avoiding naive string slicing that yields invalid apex domains like 'co.in'.

    Examples:
    - 'sub.example.com' -> 'example.com'
    - 'www.mintmorsel.co.in' -> 'mintmorsel.co.in'
    - 'api.services.restaurant.org.uk' -> 'restaurant.org.uk'
    - 'example.com' -> 'example.com'
    """
    clean = clean_domain_string(domain)
    if not clean:
        return ""

    parts = clean.split(".")
    if len(parts) <= 2:
        return clean

    # Check if last 2 parts match a known multi-part public suffix
    last_two = f"{parts[-2]}.{parts[-1]}"
    if last_two in MULTI_PART_PUBLIC_SUFFIXES:
        if len(parts) >= 3:
            return ".".join(parts[-3:])
        return clean

    # Standard single-part TLD (e.g. .com, .org, .in, .net)
    return ".".join(parts[-2:])


def is_aggregator_or_directory_domain(url_or_domain: str) -> bool:
    """Checks if the domain belongs to a known public directory, social network, or aggregator."""
    clean = clean_domain_string(url_or_domain)
    if not clean:
        return False
    org_domain = get_organizational_domain(clean)
    if clean in AGGREGATOR_AND_DIRECTORY_DOMAINS or org_domain in AGGREGATOR_AND_DIRECTORY_DOMAINS:
        return True
    return any(clean.endswith(f".{agg}") for agg in AGGREGATOR_AND_DIRECTORY_DOMAINS)


def tokenize_name(name: str) -> List[str]:
    """Tokenizes a business name into meaningful alphanumeric lowercase keywords."""
    if not name:
        return []
    words = re.findall(r"[a-z0-9]+", name.lower())
    return [w for w in words if len(w) >= 2]


def calculate_domain_name_similarity(business_name: str, domain_or_url: str) -> float:
    """
    Calculates a similarity score (0.0 to 1.0) between a business name and a domain name.
    Ignores generic stopwords (restaurant, ltd, etc.) and accounts for acronyms and combined words.

    Examples:
    - 'Mint Morsel Restaurant' vs 'mintmorsel.in' -> 1.0
    - 'Cafe Leopold' vs 'leopoldcafe.com' -> 1.0
    - 'Sarvi Restaurant' vs 'justdail.com' -> 0.0
    - 'Krabi Multi-cuisine' vs 'silveroakuran.com' -> 0.0
    """
    clean_domain = clean_domain_string(domain_or_url)
    if not clean_domain:
        return 0.0

    org_domain = get_organizational_domain(clean_domain)
    domain_label = org_domain.split(".")[0]  # e.g. 'mintmorsel' from 'mintmorsel.co.in'

    biz_tokens = tokenize_name(business_name)
    content_tokens = [t for t in biz_tokens if t not in GENERIC_BUSINESS_STOPWORDS]

    if not content_tokens:
        content_tokens = biz_tokens

    if not content_tokens:
        return 0.0

    # 1. Exact match of combined tokens (e.g. 'mint' + 'morsel' == 'mintmorsel')
    combined_name = "".join(content_tokens)
    if domain_label == combined_name or domain_label.startswith(combined_name) or combined_name.startswith(domain_label):
        return 1.0

    # 2. Check token containment
    matched_tokens = 0
    total_token_chars = sum(len(t) for t in content_tokens)
    matched_chars = 0

    for token in content_tokens:
        if token in domain_label:
            matched_tokens += 1
            matched_chars += len(token)

    if matched_tokens == len(content_tokens):
        return 0.95

    if matched_chars > 0 and total_token_chars > 0:
        ratio = matched_chars / total_token_chars
        # If the most distinctive token matched (length >= 4)
        longest_token = max(content_tokens, key=len)
        if longest_token in domain_label:
            return max(0.7, ratio)
        return ratio * 0.6

    return 0.0
