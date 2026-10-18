import re
from typing import Optional, Tuple, Any
from urllib.parse import urlparse

# Common business entity suffixes to strip during name normalization
COMMON_SUFFIXES = [
    r"\bpvt\.?\s*ltd\.?\b",
    r"\bprivate\s+limited\b",
    r"\bltd\.?\b",
    r"\blimited\b",
    r"\binc\.?\b",
    r"\bincorporated\b",
    r"\bllc\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bco\.?\b",
    r"\bgmbh\b",
    r"\bllp\b",
]
SUFFIX_REGEX = re.compile(r"|".join(COMMON_SUFFIXES), flags=re.IGNORECASE)

# Dangerous leading characters in spreadsheet formula injection (RFC 4180 / OWASP)
DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

def normalize_business_name(name: Optional[str]) -> str:
    """
    Normalizes a business name for deterministic duplicate comparison.
    Lowercases, removes punctuation, and strips common company suffixes.
    """
    if not name:
        return ""
    text = name.strip().lower()
    # Remove common corporate designations
    text = SUFFIX_REGEX.sub("", text)
    # Remove non-alphanumeric characters (preserving spaces)
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_website_url(url: Optional[str]) -> Optional[str]:
    """
    Cleans and canonicalizes a website URL.
    Returns None if empty or invalid.
    """
    if not url:
        return None
    cleaned = url.strip()
    if not cleaned or cleaned.lower() in ("none", "null", "n/a", "undefined"):
        return None
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    cleaned = cleaned.rstrip("/")
    return cleaned

def extract_registered_domain(url: Optional[str]) -> Optional[str]:
    """
    Extracts the lowercase root/host domain from a URL, stripping 'www.'.
    Returns None if URL cannot be parsed.
    """
    canonical_url = normalize_website_url(url)
    if not canonical_url:
        return None
    try:
        parsed = urlparse(canonical_url)
        host = (parsed.hostname or "").lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host if host else None
    except Exception:
        return None

def classify_website_status(
    has_website_url: bool,
    audit_status: Optional[str] = None
) -> str:
    """
    Conservative website-status classification:
    - If provider did not return a website URL -> 'not_listed'
    - If URL is returned but unverified -> 'verification_required'
    - If audit succeeded -> 'verified_accessible' (or 'active')
    - If audit failed -> 'verification_failed' (or specific error like 'unreachable')
    """
    if not has_website_url:
        return "not_listed"
    
    if audit_status == "completed":
        return "verified_accessible"
    elif audit_status in ("failed", "unreachable", "dns_error", "ssl_expired", "broken_pages"):
        return "verification_failed"
    
    return "verification_required"

def sanitize_csv_cell(val: Any) -> str:
    """
    Protects CSV cells from Spreadsheet Formula Injection (CSV DDE Injection / OWASP).
    If a cell value starts with '=', '+', '-', '@', tab, or return,
    it is prepended with a single quote (') so spreadsheet engines treat it strictly as text.
    """
    if val is None:
        return ""
    raw_str = str(val)
    # Check if raw string or space-stripped string begins with dangerous formula prefix
    stripped_spaces = raw_str.lstrip(" ")
    if stripped_spaces.startswith(DANGEROUS_FORMULA_PREFIXES):
        return "'" + raw_str
    return raw_str.strip()

def calculate_discovery_score(
    website_status: str,
    category: str,
    has_phone: bool,
    has_email: bool
) -> Tuple[int, int, int, int]:
    """
    Generates deterministic opportunity score and breakdown:
    Returns (total_score, urgency, intent, ease).
    """
    if website_status == "not_listed":
        # Missing website is a high-opportunity digital conversion target
        urgency = 36
        intent = 26
        ease = 26
    elif website_status in ("verification_failed", "ssl_expired", "broken_pages", "dns_error"):
        # Broken website represents immediate technical urgency
        urgency = 38
        intent = 28
        ease = 24
    else:
        # Standard unverified or active listing
        urgency = 25
        intent = 25
        ease = 20

    if has_phone or has_email:
        intent = min(40, intent + 3)

    total = urgency + intent + ease
    return total, urgency, intent, ease
