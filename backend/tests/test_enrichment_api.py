import pytest
import httpx
from unittest.mock import patch, AsyncMock
from backend.app.core.config import settings
from backend.app.models.prospect import ProspectModel
from backend.app.models.draft import EmailDraftModel
from backend.app.services.email_scraper import (
    is_valid_email_candidate,
    extract_contacts_from_html,
    scrape_website_contacts
)
from backend.app.services.hunter_client import (
    search_hunter_domain,
    check_hunter_api_key
)

def test_email_candidate_filter():
    assert is_valid_email_candidate("info@business.com") is True
    assert is_valid_email_candidate("sales.contact@mumbai-tech.in") is True
    # Rejections
    assert is_valid_email_candidate("logo.png") is False
    assert is_valid_email_candidate("user@example.com") is False
    assert is_valid_email_candidate("contact@sentry.io") is False
    assert is_valid_email_candidate("bad") is False

def test_extract_contacts_from_html():
    sample_html = """
    <html>
      <body>
        <h1>Contact Us</h1>
        <p>Email us at: <a href="mailto:support@silveroakuran.com?subject=Inquiry">support@silveroakuran.com</a></p>
        <p>General queries: info@silveroakuran.com</p>
        <p>Call our reception: <a href="tel:+919876543210">+91 98765 43210</a></p>
        <img src="banner@2x.png" />
      </body>
    </html>
    """
    contacts = extract_contacts_from_html(sample_html, "https://silveroakuran.com")
    assert "support@silveroakuran.com" in contacts["emails"]
    assert "info@silveroakuran.com" in contacts["emails"]
    assert "banner@2x.png" not in contacts["emails"]
    assert any("9876543210" in p or "98765" in p for p in contacts["phones"])

def test_enrichment_status_endpoint(client):
    res = client.get("/api/enrichment/status")
    assert res.status_code == 200
    data = res.json()
    assert "website_scraper" in data
    assert "hunter" in data
    assert "google_places" in data
    assert data["website_scraper"]["is_configured"] is True

@pytest.mark.asyncio
async def test_hunter_client_no_key():
    with patch.object(settings, "HUNTER_API_KEY", ""):
        res = await search_hunter_domain("example.com")
        assert res["success"] is False
        assert "not configured" in res["error"]

        test_res = await check_hunter_api_key("")
        assert test_res["success"] is False
        assert "not configured" in test_res["message"]

@pytest.mark.asyncio
async def test_hunter_client_mock_success():
    mock_data = {
        "data": {
            "domain": "acme.com",
            "organization": "Acme Corp",
            "emails": [
                {
                    "value": "john.doe@acme.com",
                    "type": "personal",
                    "confidence": 92,
                    "first_name": "John",
                    "last_name": "Doe",
                    "position": "Director"
                }
            ]
        }
    }
    mock_resp = httpx.Response(
        200,
        json=mock_data,
        request=httpx.Request("GET", "https://api.hunter.io/v2/domain-search")
    )
    with patch.object(settings, "HUNTER_API_KEY", "mock_hunter_key_123"):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            res = await search_hunter_domain("acme.com")
            assert res["success"] is True
            assert res["primary_email"] == "john.doe@acme.com"
            assert res["emails"][0]["confidence"] == 92

def test_find_email_endpoint_existing_email(client, db_session):
    p = ProspectModel(
        id="pros_has_email",
        name="Existing Business",
        website_url="https://business.com",
        email="verified@business.com",
        phone="+91 22 1234 5678"
    )
    db_session.add(p)
    db_session.commit()

    res = client.post("/api/enrichment/find-email", json={"prospect_id": "pros_has_email"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["email"] == "verified@business.com"
    assert res.json()["source"] == "database"
