import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.deep_search_enrichment import (
    decode_bing_url,
    rank_candidate_emails,
    deep_search_prospect,
    FSSAI_REGEX,
    GSTIN_REGEX
)
from backend.app.models.prospect import ProspectModel
from backend.app.models.draft import EmailDraftModel

def test_decode_bing_url():
    # Base64 encoded: "https://www.facebook.com/mintmorsel/" -> a1aHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL21pbnRtb3JzZWwv
    sample_bing = "https://www.bing.com/ck/a?!&&p=abc&u=a1aHR0cHM6Ly93d3cuZmFjZWJvb2suY29tL21pbnRtb3JzZWwv&ntb=1"
    decoded = decode_bing_url(sample_bing)
    assert decoded == "https://www.facebook.com/mintmorsel/"

    # Normal direct URL unchanged
    assert decode_bing_url("https://www.instagram.com/mintmorsel/") == "https://www.instagram.com/mintmorsel/"
    assert decode_bing_url("") == ""

def test_rank_candidate_emails():
    candidates = {
        "random.person@gmail.com",
        "mintmorsel.vasai@gmail.com",
        "info@mintmorsel.com",
        "catering@yahoo.com"
    }
    ranked = rank_candidate_emails(candidates, "MintMorsel Restaurant")
    # info@mintmorsel.com (domain match) or mintmorsel.vasai@gmail.com (name match) should be prioritized
    assert ranked[0] in ["info@mintmorsel.com", "mintmorsel.vasai@gmail.com"]
    assert ranked[-1] == "random.person@gmail.com"

def test_fssai_and_gstin_regex():
    sample_text = "FSSAI Lic. No: 11522026000123. GSTIN: 27AAAAA0000A1Z5. Food safety certified."
    fssai_match = FSSAI_REGEX.search(sample_text)
    gstin_match = GSTIN_REGEX.search(sample_text)
    assert fssai_match is not None
    assert fssai_match.group(1) == "11522026000123"
    assert gstin_match is not None
    assert gstin_match.group(0) == "27AAAAA0000A1Z5"

@pytest.mark.asyncio
async def test_deep_search_prospect_mocked():
    def mock_search_fn(query, max_results=5):
        if "FSSAI" in query:
            return [
                {
                    "title": "Public FSSAI Registrations",
                    "url": "https://foscos.fssai.gov.in/check",
                    "snippet": "MintMorsel Restaurant FSSAI Lic No: 11521025000456"
                }
            ]
        elif "facebook" in query or "Vasai" in query:
            return [
                {
                    "title": "MintMorsel - Best Restaurant in Vasai",
                    "url": "https://www.facebook.com/p/MintMorsel-61570232361014/",
                    "snippet": "Contact us at mintmorsel.vasai@gmail.com or call 9326376877 for catering."
                },
                {
                    "title": "MintMorsel (@mintmorsel) • Instagram photos",
                    "url": "https://www.instagram.com/mintmorsel/",
                    "snippet": "Chinese | Indian | Tandoor | DM or email mintmorsel@gmail.com"
                },
                {
                    "title": "MintMorsel Restaurant, Vasai - Justdial",
                    "url": "https://www.justdial.com/Mumbai/MintMorsel-Vasai/022PXX22",
                    "snippet": "Rated 4.5 based on 250 reviews."
                }
            ]
        return []

    with patch("backend.app.services.deep_search_enrichment.execute_multi_engine_search", side_effect=mock_search_fn), \
         patch("backend.app.services.deep_search_enrichment.verify_email_mx", return_value=True):

        result = await deep_search_prospect("MintMorsel Restaurant", "Vasai", "+91 9326376877")
        assert result["success"] is True
        assert result["primary_email"] in ["mintmorsel.vasai@gmail.com", "mintmorsel@gmail.com"]
        assert result["social_profiles"]["facebook"] == "https://www.facebook.com/p/MintMorsel-61570232361014/"
        assert result["social_profiles"]["instagram"] == "https://www.instagram.com/mintmorsel/"
        assert result["social_profiles"]["justdial"] == "https://www.justdial.com/Mumbai/MintMorsel-Vasai/022PXX22"
        assert result["whatsapp"]["phone_e164"] == "+919326376877"
        assert result["whatsapp"]["wa_link"] == "https://wa.me/919326376877"
        assert result["fssai_info"]["license_number"] == "11521025000456"

def test_api_find_email_zero_website_fallback(client, db_session):
    # Create prospect without website
    prospect = ProspectModel(
        id="prospect_zero_web_test",
        name="Zero Web Cafe",
        city="Mumbai",
        website_url=None,
        email=None,
        phone="+919820123456"
    )
    db_session.add(prospect)
    db_session.commit()

    with patch("backend.app.api.enrichment.deep_search_prospect") as mock_deep:
        mock_deep.return_value = {
            "success": True,
            "primary_email": "zerowebcafe@gmail.com",
            "all_emails": ["zerowebcafe@gmail.com"],
            "social_profiles": {"facebook": "https://facebook.com/zerowebcafe"},
            "whatsapp": {"phone_e164": "+919820123456", "wa_link": "https://wa.me/919820123456"},
            "fssai_info": None,
            "directory_metadata": {},
            "sources_hit": ["Facebook Page", "Search Dorking"],
            "discovered_website": None,
            "message": "Verified email: zerowebcafe@gmail.com"
        }

        res = client.post("/api/enrichment/find-email", json={"prospect_id": prospect.id})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["email"] == "zerowebcafe@gmail.com"
        assert data["source"] == "deep_search_enrichment"

        # Verify DB updated
        db_session.refresh(prospect)
        assert prospect.email == "zerowebcafe@gmail.com"
