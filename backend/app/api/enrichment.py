import json
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
from backend.app.services.deep_search_enrichment import deep_search_prospect
from backend.app.services.contact_provenance import classify_contact_provenance
from backend.app.services.identity_verifier import verify_business_identity

logger = logging.getLogger("leddro.api.enrichment")
router = APIRouter(prefix="/enrichment", tags=["Contact Enrichment & Verification"])

class ScrapeRequest(BaseModel):
    url: str
    prospect_id: Optional[str] = None

class FindEmailRequest(BaseModel):
    prospect_id: str

class DeepSearchRequest(BaseModel):
    prospect_id: Optional[str] = None
    business_name: Optional[str] = None
    location: Optional[str] = "Mumbai"
    phone: Optional[str] = None

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
        "deep_search": {
            "name": "Multi-Channel Social & Deep Search Dorking",
            "is_configured": True,
            "provider_id": "deep_search",
            "description": "Cross-platform contact intelligence targeting Facebook Pages, Instagram bios, Google/Bing search dorks, WhatsApp Business, Justdial, and FSSAI/GSTIN records for businesses without websites.",
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
            prov = classify_contact_provenance(
                email=result["primary_email"],
                business_name=prospect.name,
                source_type="official_website",
                source_url=payload.url,
                source_provider="website_scraper"
            )
            prospect.contact_provenance = json.dumps(prov)

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
            "message": f"Email already on file: {prospect.email} (mailbox existence is not confirmed; inspect provenance before outreach)"
        }

    # Step 1: Built-in Website Scraper (Free)
    if prospect.website_url and prospect.website_url.strip():
        scrape_res = await scrape_website_contacts(prospect.website_url)
        if scrape_res.get("primary_email"):
            found_email = scrape_res["primary_email"]
            prospect.email = found_email
            prov = classify_contact_provenance(
                email=found_email,
                business_name=prospect.name,
                source_type="official_website",
                source_url=prospect.website_url,
                source_provider="website_scraper",
                identity_status=prospect.identity_status
            )
            prospect.contact_provenance = json.dumps(prov)

            if not prospect.phone and scrape_res.get("phones"):
                prospect.phone = scrape_res["phones"][0]
            
            # Update drafts only when the address provenance is trustworthy
            if prov.get("status") in ("official_source", "corroborated", "provider_verified"):
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
                "contact_provenance": prov,
                "all_emails": scrape_res.get("emails", []),
                "message": f"Extracted email from {prospect.website_url}: {found_email} (source: website; mailbox existence not confirmed)"
            }

    # Step 2: Hunter.io B2B Enrichment (if configured)
    if settings.HUNTER_API_KEY.strip() and prospect.website_url:
        domain = prospect.website_url.replace("https://", "").replace("http://", "").split("/")[0]
        hunter_res = await search_hunter_domain(domain)
        if hunter_res.get("primary_email"):
            found_email = hunter_res["primary_email"]
            prospect.email = found_email
            prov = classify_contact_provenance(
                email=found_email,
                business_name=prospect.name,
                source_type="hunter_io",
                source_url=prospect.website_url,
                source_provider="hunter_io",
                provider_confidence=85
            )
            prospect.contact_provenance = json.dumps(prov)
            
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
                "contact_provenance": prov,
                "all_emails": [e["value"] for e in hunter_res.get("emails", [])],
                "message": f"Hunter.io verified corporate email for {domain}: {found_email}"
            }

    # Step 3: Multi-Channel Social & Deep Search Dorking (Autonomous fallback for businesses without official websites)
    logger.info(f"Running deep multi-channel search for '{prospect.name}' ({prospect.city})...")
    deep_res = await deep_search_prospect(
        prospect_name=prospect.name,
        location=prospect.city or "Mumbai",
        known_phone=prospect.phone
    )

    if deep_res.get("primary_email"):
        found_email = deep_res["primary_email"]
        prospect.email = found_email
        if deep_res.get("contact_provenance"):
            prospect.contact_provenance = json.dumps(deep_res["contact_provenance"])
        if deep_res.get("identity_verification"):
            prospect.identity_status = deep_res["identity_verification"]["status"]
            prospect.identity_evidence = json.dumps(deep_res["identity_verification"])
        if deep_res.get("social_matches"):
            prospect.social_profiles = json.dumps(deep_res["social_matches"])

        if not prospect.phone and deep_res.get("phone"):
            prospect.phone = deep_res["phone"]

        # Only promote website if verified or likely match
        id_status = deep_res.get("identity_verification", {}).get("status")
        if not prospect.website_url and deep_res.get("discovered_website"):
            if id_status in ("verified", "likely_match"):
                prospect.website_url = deep_res["discovered_website"]
                prospect.website_status = "active"
            elif id_status == "conflicting":
                prospect.website_status = "conflicting"

        # Safe draft promotion: only promote if contact is corroborated or provider verified
        is_trustworthy = deep_res.get("contact_provenance", {}).get("status") in ("official_source", "corroborated", "provider_verified")
        if is_trustworthy:
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
            "source": "deep_search_enrichment",
            "email": found_email,
            "contact_provenance": deep_res.get("contact_provenance"),
            "identity_verification": deep_res.get("identity_verification"),
            "all_emails": deep_res.get("all_emails", []),
            "social_profiles": deep_res.get("social_profiles", {}),
            "social_matches": deep_res.get("social_matches", {}),
            "whatsapp": deep_res.get("whatsapp"),
            "fssai_info": deep_res.get("fssai_info"),
            "directory_metadata": deep_res.get("directory_metadata", {}),
            "sources_hit": deep_res.get("sources_hit", []),
            "discovered_website": deep_res.get("discovered_website"),
            "message": f"Discovered verified contact for '{prospect.name}': {deep_res.get('message')}"
        }

    # If email wasn't found but socials / WhatsApp were found, persist phone/website if discovered
    has_intel = bool(deep_res.get("whatsapp") or any(deep_res.get("social_profiles", {}).values()) or deep_res.get("discovered_website"))
    if has_intel:
        if not prospect.phone and deep_res.get("phone"):
            prospect.phone = deep_res["phone"]
        if not prospect.website_url and deep_res.get("discovered_website"):
            prospect.website_url = deep_res["discovered_website"]
            prospect.website_status = "active"
        db.commit()

        return {
            "success": True,
            "source": "deep_search_intel",
            "email": None,
            "phone": prospect.phone,
            "social_profiles": deep_res.get("social_profiles", {}),
            "whatsapp": deep_res.get("whatsapp"),
            "fssai_info": deep_res.get("fssai_info"),
            "directory_metadata": deep_res.get("directory_metadata", {}),
            "sources_hit": deep_res.get("sources_hit", []),
            "discovered_website": deep_res.get("discovered_website"),
            "message": f"Discovered online presence for '{prospect.name}': {deep_res.get('message')}"
        }

    # No email or social intelligence could be found
    return {
        "success": False,
        "source": "none",
        "email": None,
        "phone": prospect.phone,
        "message": f"No verified email or public profile discovered for '{prospect.name}'. Use phone: {prospect.phone or 'N/A'}"
    }

@router.post("/deep-search")
async def execute_deep_search(payload: DeepSearchRequest, db: Session = Depends(get_db)):
    """
    Executes comprehensive 5-channel search across:
    1. Facebook Pages & Instagram Bios (India's primary local business storefronts).
    2. Search Engine Dorking (Gmail, Yahoo, bookings, catering queries).
    3. WhatsApp Business profile metadata & phone dorking.
    4. Local Indian directories (Justdial, Zomato, Swiggy, IndiaMART).
    5. Government registrations (FSSAI licenses & GSTIN records).
    """
    biz_name = payload.business_name
    loc = payload.location or "Mumbai"
    phone = payload.phone
    prospect = None

    if payload.prospect_id:
        prospect = db.query(ProspectModel).filter(ProspectModel.id == payload.prospect_id).first()
        if prospect:
            biz_name = prospect.name
            loc = prospect.city or loc
            phone = prospect.phone or phone

    if not biz_name or not biz_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business name is required for deep search.")

    result = await deep_search_prospect(
        prospect_name=biz_name,
        location=loc,
        known_phone=phone
    )

    # If attached to a prospect record, persist discoveries
    if prospect:
        updated = False
        if result.get("contact_provenance"):
            prospect.contact_provenance = json.dumps(result["contact_provenance"])
            updated = True
        if result.get("identity_verification"):
            prospect.identity_status = result["identity_verification"]["status"]
            prospect.identity_evidence = json.dumps(result["identity_verification"])
            updated = True
        if result.get("social_matches"):
            prospect.social_profiles = json.dumps(result["social_matches"])
            updated = True

        if result.get("primary_email") and not prospect.email:
            prospect.email = result["primary_email"]
            updated = True
            
            # Safe draft promotion: only promote if contact is corroborated or provider verified
            is_trustworthy = result.get("contact_provenance", {}).get("status") in ("official_source", "corroborated", "provider_verified")
            if is_trustworthy:
                drafts = db.query(EmailDraftModel).filter(
                    EmailDraftModel.prospect_id == prospect.id,
                    EmailDraftModel.status.in_(["draft", "needs_review"])
                ).all()
                for d in drafts:
                    if not d.recipient_email or not d.recipient_email.strip():
                        d.recipient_email = result["primary_email"]

        if result.get("phone") and not prospect.phone:
            prospect.phone = result["phone"]
            updated = True

        if result.get("discovered_website") and not prospect.website_url:
            id_status = result.get("identity_verification", {}).get("status")
            if id_status in ("verified", "likely_match"):
                prospect.website_url = result["discovered_website"]
                prospect.website_status = "active"
                updated = True
            elif id_status == "conflicting":
                prospect.website_status = "conflicting"
                updated = True

        if updated:
            db.commit()

    return result

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
