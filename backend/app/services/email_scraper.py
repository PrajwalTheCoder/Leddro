import re
import time
import logging
from typing import Dict, Any, List, Set, Optional
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
import dns.resolver

from backend.app.core.config import settings
from backend.app.services.ssrf_validator import validate_target_url

logger = logging.getLogger("leddro.services.email_scraper")

# Junk email extensions and placeholder domains to reject
JUNK_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp", ".ico",
    ".js", ".css", ".map", ".woff", ".woff2", ".ttf", ".eot",
    ".mp4", ".webm", ".avi", ".mov", ".pdf", ".zip"
}

JUNK_DOMAINS = {
    "example.com", "example.org", "domain.com", "yourcompany.com",
    "placeholder.com", "email.com", "sentry.io", "wixpress.com",
    "w3.org", "schema.org", "gravatar.com", "wordpress.org"
}

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")

def is_valid_email_candidate(email: str) -> bool:
    """Filters out image filenames and dummy template emails."""
    email = email.strip().lower()
    if len(email) < 6 or len(email) > 100 or "@" not in email:
        return False
    
    # Check extension
    for ext in JUNK_EXTENSIONS:
        if email.endswith(ext):
            return False
            
    parts = email.split("@")
    if len(parts) != 2:
        return False
    user, domain = parts
    
    if domain in JUNK_DOMAINS or domain.startswith("sentry-") or "sentry" in domain:
        return False
        
    if user in {"name", "user", "username", "yourname", "test", "admin@localhost"}:
        return False
        
    return True

def verify_email_mx(email: str) -> bool:
    """Verifies that the target email's domain has configured MX mail exchangers."""
    try:
        domain = email.split("@")[1].strip()
        records = dns.resolver.resolve(domain, "MX", lifetime=3.0)
        return len(records) > 0
    except Exception:
        # Fallback: check A record
        try:
            domain = email.split("@")[1].strip()
            records = dns.resolver.resolve(domain, "A", lifetime=2.0)
            return len(records) > 0
        except Exception:
            return False

def decode_cloudflare_email(cf_hex: str) -> Optional[str]:
    """
    Decodes Cloudflare's client-side XOR email obfuscation (data-cfemail or /cdn-cgi/l/email-protection#...).
    Performs deterministic XOR decoding identically to the browser's JavaScript engine.
    """
    try:
        cf_hex = cf_hex.strip()
        if len(cf_hex) < 4 or len(cf_hex) % 2 != 0:
            return None
        key = int(cf_hex[:2], 16)
        return "".join(
            chr(int(cf_hex[i:i+2], 16) ^ key)
            for i in range(2, len(cf_hex), 2)
        )
    except Exception:
        return None

def extract_contacts_from_html(html: str, base_url: str) -> Dict[str, List[str]]:
    """Extracts raw candidate emails and phone numbers from HTML DOM."""
    soup = BeautifulSoup(html, "html.parser")
    emails: Set[str] = set()
    phones: Set[str] = set()

    # 1. Check mailto: links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            raw_email = href[7:].split("?")[0].strip()
            if is_valid_email_candidate(raw_email):
                emails.add(raw_email.lower())
        elif href.lower().startswith("tel:"):
            raw_phone = href[4:].split("?")[0].strip()
            if len(raw_phone) >= 7:
                phones.add(raw_phone)

    # 2. Check Cloudflare data-cfemail attributes (<span data-cfemail="..."> or <a data-cfemail="...">)
    for el in soup.find_all(attrs={"data-cfemail": True}):
        val = el.get("data-cfemail", "")
        decoded = decode_cloudflare_email(val)
        if decoded and is_valid_email_candidate(decoded):
            emails.add(decoded.lower())

    # 3. Check Cloudflare email protection links (href="/cdn-cgi/l/email-protection#<hex>")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "/cdn-cgi/l/email-protection#" in href:
            cf_hash = href.split("/cdn-cgi/l/email-protection#")[-1].split("?")[0].strip()
            decoded = decode_cloudflare_email(cf_hash)
            if decoded and is_valid_email_candidate(decoded):
                emails.add(decoded.lower())

    # 4. Check regex across full HTML text
    text_content = soup.get_text(separator=" ")
    for match in EMAIL_REGEX.findall(text_content):
        if is_valid_email_candidate(match):
            emails.add(match.lower())

    # 5. Check regex across raw HTML attributes (data-email, placeholders, footer tags)
    for match in EMAIL_REGEX.findall(html):
        if is_valid_email_candidate(match):
            emails.add(match.lower())

    return {
        "emails": sorted(list(emails)),
        "phones": sorted(list(phones))
    }

async def scrape_website_contacts(url: str, max_pages: int = 3) -> Dict[str, Any]:
    """
    Crawls the homepage and up to 2 contact subpages (/contact, /about) with SSRF checks.
    Extracts authentic public contact emails and checks DNS MX deliverability.
    """
    is_safe, error_msg, parsed_url, _ = validate_target_url(url)
    if not is_safe:
        return {
            "success": False,
            "error": f"URL failed security validation: {error_msg}",
            "emails": [],
            "phones": []
        }

    domain = parsed_url.hostname or ""
    base_url = f"{parsed_url.scheme}://{domain}"
    
    headers = {
        "User-Agent": settings.AUDIT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    all_emails: Set[str] = set()
    all_phones: Set[str] = set()
    visited_urls: List[str] = []
    contact_subpage_links: Set[str] = set()

    transport = httpx.AsyncHTTPTransport(retries=1)
    async with httpx.AsyncClient(transport=transport, timeout=7.0, follow_redirects=True) as client:
        # 1. Fetch homepage
        try:
            resp = await client.get(url, headers=headers)
            visited_urls.append(str(resp.url))
            if resp.status_code == 200:
                contacts = extract_contacts_from_html(resp.text, str(resp.url))
                all_emails.update(contacts["emails"])
                all_phones.update(contacts["phones"])

                # Look for contact / about subpage links
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    href_lower = href.lower()
                    if any(slug in href_lower for slug in ["contact", "about", "reach-us", "touch", "location"]):
                        sub_url = urljoin(str(resp.url), href)
                        parsed_sub = urlparse(sub_url)
                        if parsed_sub.hostname == domain and sub_url not in visited_urls:
                            contact_subpage_links.add(sub_url)
        except Exception as e:
            logger.warning(f"Error fetching homepage {url}: {e}")

        # 2. Fetch contact subpages (up to max_pages)
        subpage_list = list(contact_subpage_links)[:max_pages - 1]
        for sub_url in subpage_list:
            is_sub_safe, _, _, _ = validate_target_url(sub_url)
            if not is_sub_safe or sub_url in visited_urls:
                continue
            try:
                visited_urls.append(sub_url)
                sub_resp = await client.get(sub_url, headers=headers)
                if sub_resp.status_code == 200:
                    contacts = extract_contacts_from_html(sub_resp.text, str(sub_resp.url))
                    all_emails.update(contacts["emails"])
                    all_phones.update(contacts["phones"])
            except Exception as e:
                logger.warning(f"Error fetching subpage {sub_url}: {e}")

    # 3. Validate MX records for candidate emails
    verified_emails = []
    for em in all_emails:
        if verify_email_mx(em):
            verified_emails.append(em)

    # 4. Rank discovered emails: domain matches first, then generic/gmail
    def email_rank(em: str) -> int:
        em_domain = em.split("@")[1].lower()
        if em_domain == domain.lower() or domain.lower().endswith("." + em_domain):
            return 0  # Best: exact corporate domain match
        if any(prefix in em for prefix in ["contact", "info", "hello", "sales", "support", "inquiries"]):
            return 1
        return 2

    ranked_emails = sorted(verified_emails, key=email_rank)
    primary_email = ranked_emails[0] if ranked_emails else None

    return {
        "success": True,
        "target_url": url,
        "domain": domain,
        "primary_email": primary_email,
        "emails": ranked_emails,
        "phones": sorted(list(all_phones)),
        "pages_scanned": len(visited_urls)
    }
