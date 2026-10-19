import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("leddro.services.hunter")

HUNTER_DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"
HUNTER_ACCOUNT_URL = "https://api.hunter.io/v2/account"

async def check_hunter_api_key(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Tests Hunter.io API key by retrieving account profile and search quota."""
    key = (api_key or settings.HUNTER_API_KEY).strip()
    if not key:
        return {
            "success": False,
            "message": "Hunter.io API key is not configured. Add HUNTER_API_KEY to your .env file."
        }

    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            resp = await client.get(f"{HUNTER_ACCOUNT_URL}?api_key={key}")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                reqs = data.get("requests", {}).get("searches", {})
                available = reqs.get("available", 0)
                used = reqs.get("used", 0)
                plan = data.get("plan_name", "Free")
                email = data.get("email", "")
                return {
                    "success": True,
                    "message": f"Hunter.io authenticated successfully as {email} ({plan} plan).",
                    "plan": plan,
                    "available_searches": available,
                    "used_searches": used,
                    "email": email
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "message": "Invalid Hunter.io API key. Check your key in the Hunter.io dashboard."
                }
            else:
                return {
                    "success": False,
                    "message": f"Hunter.io API error (HTTP {resp.status_code}): {resp.text[:150]}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to Hunter.io: {str(e)}"
            }

async def search_hunter_domain(domain: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Queries Hunter.io Domain Search for verified business email addresses.
    Returns executive names, positions, confidence scores, and deliverability.
    """
    key = (api_key or settings.HUNTER_API_KEY).strip()
    if not key:
        return {
            "success": False,
            "error": "Hunter.io is not configured. Set HUNTER_API_KEY in your .env file.",
            "emails": []
        }

    clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
    if not clean_domain:
        return {
            "success": False,
            "error": "Valid domain is required for Hunter.io search.",
            "emails": []
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                HUNTER_DOMAIN_SEARCH_URL,
                params={"domain": clean_domain, "api_key": key}
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                raw_emails = data.get("emails", [])
                parsed_emails = []
                for item in raw_emails:
                    parsed_emails.append({
                        "value": item.get("value"),
                        "type": item.get("type", "generic"),
                        "confidence": item.get("confidence", 0),
                        "first_name": item.get("first_name"),
                        "last_name": item.get("last_name"),
                        "position": item.get("position"),
                        "department": item.get("department")
                    })

                primary = parsed_emails[0]["value"] if parsed_emails else None
                return {
                    "success": True,
                    "domain": clean_domain,
                    "organization": data.get("organization"),
                    "emails": parsed_emails,
                    "primary_email": primary
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid Hunter.io API key.",
                    "emails": []
                }
            elif resp.status_code == 429:
                return {
                    "success": False,
                    "error": "Hunter.io monthly search limit exceeded.",
                    "emails": []
                }
            else:
                return {
                    "success": False,
                    "error": f"Hunter.io error (HTTP {resp.status_code})",
                    "emails": []
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "emails": []
            }
