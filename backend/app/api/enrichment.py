import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import httpx

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.prospect import ProspectModel
from backend.app.models.draft import EmailDraftModel
from backend.app.services.email_scraper import scrape_website_contacts
from backend.app.services.hunter_client import search_hunter_domain, check_hunter_api_key

logger = logging.getLogger("leddro.api.enrichment")
router = APIRouter(prefix="/enrichment", tags=["Contact Enrichment & Verification"])

class ScrapeRequest(BaseModel):
    url: str
    prospect_id: Optional[str] = None

class FindEmailRequest(BaseModel):
    prospect_id: str

class TestKeyRequest(BaseModel):
    api_key: Optional[str] = None

class SaveKeysRequest(BaseModel):
    hunter_api_key: Optional[str] = None
    google_places_api_key: Optional[str] = None

def mask_api_key(key: str) -> str:
    k = (key or "").strip()
    if not k:
        return ""
    if len(k) <= 8:
        return "••••••••"
    return f"{k[:4]}••••{k[-4:]}"

@router.get("/status")
def get_enrichment_status():
    """Returns configuration status for contact discovery and enrichment providers."""
    has_hunter = bool(settings.HUNTER_API_KEY.strip())
    has_places = bool(settings.GOOGLE_PLACES_API_KEY.strip())

    return {
        "website_scraper": {
            "name": "Built-in Website Contact Crawler",
            "is_configured": True,
            "provider_id": "website_scraper",
            "description": "Autonomous contact extraction from target web pages, footer, and /contact routes with live DNS MX verification.",
            "free": True
        },
        "hunter": {
            "name": "Hunter.io B2B Email Finder",
            "is_configured": has_hunter,
            "masked_key": mask_api_key(settings.HUNTER_API_KEY),
            "provider_id": "hunter",
            "description": "Professional executive email lookup with confidence scoring and deliverability verification (25 free searches/mo).",
            "requires_key": True
        },
        "google_places": {
            "name": "Google Places API (New)",
            "is_configured": has_places,
            "masked_key": mask_api_key(settings.GOOGLE_PLACES_API_KEY),
            "provider_id": "google_places",
            "description": "Google Maps business profile lookup for verified phone numbers, official websites, and reviews ($200 free monthly credit).",
            "requires_key": True
        }
    }

@router.post("/save-keys")
def save_enrichment_keys(payload: SaveKeysRequest):
    """Saves Hunter.io or Google Places API keys locally to .env without leaking secrets."""
    from backend.app.ai.service import _persist_to_env_file
    updates = {}
    if payload.hunter_api_key is not None:
        settings.HUNTER_API_KEY = payload.hunter_api_key.strip()
        updates["HUNTER_API_KEY"] = settings.HUNTER_API_KEY
    if payload.google_places_api_key is not None:
        settings.GOOGLE_PLACES_API_KEY = payload.google_places_api_key.strip()
        updates["GOOGLE_PLACES_API_KEY"] = settings.GOOGLE_PLACES_API_KEY

    if updates:
        _persist_to_env_file(".env", updates)
        _persist_to_env_file("backend/.env", updates)

    return {
        "success": True,
        "message": "Enrichment credentials saved securely to local .env file.",
        "status": get_enrichment_status()
    }

@router.post("/scrape-website")
async def scrape_website(payload: ScrapeRequest, db: Session = Depends(get_db)):
    """
    Crawls target website to extract authentic published emails and phone numbers.
    Optionally saves verified results directly to the prospect record.
    """
    if not payload.url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target website URL is required.")

    result = await scrape_website_contacts(payload.url)
    
    # If prospect_id provided and email found, persist to prospect
    if payload.prospect_id and result.get("primary_email"):
        prospect = db.query(ProspectModel).filter(ProspectModel.id == payload.prospect_id).first()
        if prospect:
            if not prospect.email:
                prospect.email = result["primary_email"]
            if not prospect.phone and result.get("phones"):
                prospect.phone = result["phones"][0]
            
            # Update any pending drafts for this prospect with the real verified email
            drafts = db.query(EmailDraftModel).filter(
                EmailDraftModel.prospect_id == payload.prospect_id,
                EmailDraftModel.status.in_(["draft", "needs_review"])
            ).all()
            for d in drafts:
                if not d.recipient_email or not d.recipient_email.strip():
                    d.recipient_email = result["primary_email"]
            
            db.commit()

    return result

@router.post("/find-email")
async def find_email_for_prospect(payload: FindEmailRequest, db: Session = Depends(get_db)):
    """
    Orchestrates contact finding for a prospect:
    1. Checks if prospect already has verified email.
    2. Runs built-in website contact scraper on their website URL.
    3. Falls back to Hunter.io if configured.
    4. Automatically saves discovered verified email to prospect and updates open drafts.
    """
    prospect = db.query(ProspectModel).filter(ProspectModel.id == payload.prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found.")

    if prospect.email and prospect.email.strip():
        return {
            "success": True,
            "source": "database",
            "email": prospect.email,
            "message": f"Verified email already on file: {prospect.email}"
        }

    # Step 1: Built-in Website Scraper (Free)
    if prospect.website_url and prospect.website_url.strip():
        scrape_res = await scrape_website_contacts(prospect.website_url)
        if scrape_res.get("primary_email"):
            found_email = scrape_res["primary_email"]
            prospect.email = found_email
            if not prospect.phone and scrape_res.get("phones"):
                prospect.phone = scrape_res["phones"][0]
            
            # Update drafts
            drafts = db.query(EmailDraftModel).filter(
                EmailDraftModel.prospect_id == prospect.id,
                EmailDraftModel.status.in_(["draft", "needs_review"])
            ).all()
            for d in drafts:
                if not d.recipient_email or not d.recipient_email.strip():
                    d.recipient_email = found_email
            
            db.commit()
            return {
                "success": True,
                "source": "website_scraper",
                "email": found_email,
                "all_emails": scrape_res.get("emails", []),
                "message": f"Successfully extracted verified email from {prospect.website_url}: {found_email}"
            }

    # Step 2: Hunter.io B2B Enrichment (if configured)
    if settings.HUNTER_API_KEY.strip() and prospect.website_url:
        domain = prospect.website_url.replace("https://", "").replace("http://", "").split("/")[0]
        hunter_res = await search_hunter_domain(domain)
        if hunter_res.get("primary_email"):
            found_email = hunter_res["primary_email"]
            prospect.email = found_email
            
            drafts = db.query(EmailDraftModel).filter(
                EmailDraftModel.prospect_id == prospect.id,
                EmailDraftModel.status.in_(["draft", "needs_review"])
            ).all()
            for d in drafts:
                if not d.recipient_email or not d.recipient_email.strip():
                    d.recipient_email = found_email

            db.commit()
            return {
                "success": True,
                "source": "hunter_io",
                "email": found_email,
                "all_emails": [e["value"] for e in hunter_res.get("emails", [])],
                "message": f"Hunter.io verified corporate email for {domain}: {found_email}"
            }

    # No email could be found
    return {
        "success": False,
        "source": "none",
        "email": None,
        "phone": prospect.phone,
        "message": f"No verified email found for '{prospect.name}'. Use verified phone number: {prospect.phone or 'N/A'}"
    }

@router.post("/test-hunter")
async def test_hunter_connection(payload: TestKeyRequest):
    """Tests Hunter.io API key connection and returns account quota."""
    return await check_hunter_api_key(payload.api_key)

@router.post("/test-google-places")
async def test_google_places_connection(payload: TestKeyRequest):
    """Tests Google Places API key connection and verifies Google Cloud credentials."""
    key = (payload.api_key or settings.GOOGLE_PLACES_API_KEY).strip()
    if not key:
        return {
            "success": False,
            "message": "Google Places API key is not configured. Add GOOGLE_PLACES_API_KEY to your .env file."
        }

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": "places.id,places.displayName"
    }
    payload_body = {"textQuery": "coffee", "pageSize": 1}

    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            resp = await client.post(url, json=payload_body, headers=headers)
            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": "Google Places API key authenticated successfully (Places API New active)."
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "message": "Google Places API authentication rejected (HTTP 403). Ensure 'Places API (New)' is enabled in Google Cloud Console."
                }
            else:
                return {
                    "success": False,
                    "message": f"Google Places API responded with status {resp.status_code}: {resp.text[:150]}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error testing Google Places API: {str(e)}"
            }
