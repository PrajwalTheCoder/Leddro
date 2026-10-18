import pytest
import httpx
from unittest.mock import patch, MagicMock

from backend.app.discovery.models import DiscoverySearchParams
from backend.app.discovery.providers.osm import OsmDiscoveryProvider, OSM_CATEGORY_MAPPINGS
from backend.app.discovery.providers.google_places import GooglePlacesDiscoveryProvider
from backend.app.discovery.normalizer import (
    normalize_business_name,
    normalize_website_url,
    extract_registered_domain,
    classify_website_status,
    sanitize_csv_cell,
    calculate_discovery_score
)

# Sample mock Overpass response
MOCK_OVERPASS_SUCCESS = {
    "version": 0.6,
    "generator": "Overpass API",
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 19.033,
            "lon": 73.029,
            "tags": {
                "name": "Aura Spatial Consultants",
                "amenity": "restaurant",
                "addr:city": "Navi Mumbai",
                "addr:state": "Maharashtra",
                "addr:street": "Palm Beach Road",
                "website": "https://auraspatial.in",
                "phone": "+91 22 2789 0001",
                "email": "info@auraspatial.in"
            }
        },
        {
            "type": "way",
            "id": 2002,
            "center": {"lat": 19.035, "lon": 73.030},
            "tags": {
                "name": "Zenith Wooden Crafts",
                "amenity": "restaurant",
                "addr:city": "Navi Mumbai",
                "addr:state": "Maharashtra"
                # website missing
            }
        },
        {
            "type": "node",
            "id": 3003,
            "lat": 19.036,
            "lon": 73.031,
            "tags": {
                # unnamed node should be skipped
                "amenity": "restaurant"
            }
        }
    ]
}

# Sample mock Nominatim response
MOCK_NOMINATIM_SUCCESS = [
    {
        "place_id": 1001,
        "osm_type": "node",
        "osm_id": 1001,
        "lat": "19.033",
        "lon": "73.029",
        "name": "Aura Spatial Consultants",
        "display_name": "Aura Spatial Consultants, Palm Beach Road, Navi Mumbai, Maharashtra, India",
        "address": {
            "amenity": "Aura Spatial Consultants",
            "road": "Palm Beach Road",
            "city": "Navi Mumbai",
            "state": "Maharashtra",
            "country": "India"
        },
        "extratags": {
            "website": "https://auraspatial.in",
            "phone": "+91 22 2789 0001",
            "email": "info@auraspatial.in"
        }
    },
    {
        "place_id": 2002,
        "osm_type": "way",
        "osm_id": 2002,
        "lat": "19.035",
        "lon": "73.030",
        "name": "Zenith Wooden Crafts",
        "display_name": "Zenith Wooden Crafts, Navi Mumbai, Maharashtra, India",
        "address": {
            "city": "Navi Mumbai",
            "state": "Maharashtra",
            "country": "India"
        },
        "extratags": {}
    },
    {
        "place_id": 3003,
        "osm_type": "node",
        "osm_id": 3003,
        "name": "",
        "display_name": "Unnamed Entity",
        "address": {}
    }
]

# --- Normalizer Tests ---

def test_normalize_business_name():
    assert normalize_business_name("Northstar Interiors Pvt. Ltd.") == "northstar interiors"
    assert normalize_business_name("Zenith Metalworks LLC") == "zenith metalworks"
    assert normalize_business_name("  Apex Tools Incorporated  ") == "apex tools"
    assert normalize_business_name("Aura & Co.") == "aura"
    assert normalize_business_name("") == ""

def test_normalize_website_url():
    assert normalize_website_url("example.com") == "https://example.com"
    assert normalize_website_url("http://test.in/") == "http://test.in"
    assert normalize_website_url("https://sub.domain.co.in/path/") == "https://sub.domain.co.in/path"
    assert normalize_website_url("none") is None
    assert normalize_website_url("") is None

def test_extract_registered_domain():
    assert extract_registered_domain("https://www.example.com/contact") == "example.com"
    assert extract_registered_domain("http://northstar.co.in") == "northstar.co.in"
    assert extract_registered_domain("invalid-url") == "invalid-url"
    assert extract_registered_domain(None) is None

def test_classify_website_status():
    assert classify_website_status(False) == "not_listed"
    assert classify_website_status(True) == "verification_required"
    assert classify_website_status(True, "completed") == "verified_accessible"
    assert classify_website_status(True, "unreachable") == "verification_failed"
    assert classify_website_status(True, "ssl_expired") == "verification_failed"

def test_sanitize_csv_cell_formula_injection():
    # Formula injection vectors
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert sanitize_csv_cell("+123+456") == "'+123+456"
    assert sanitize_csv_cell("-5+10") == "'-5+10"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    assert sanitize_csv_cell("\tTabbed") == "'\tTabbed"
    assert sanitize_csv_cell("Normal Text") == "Normal Text"

def test_calculate_discovery_score():
    score_not_listed, urg, intent, ease = calculate_discovery_score("not_listed", "restaurant", True, True)
    assert score_not_listed >= 80
    assert urg == 36
    score_active, urg_act, _, _ = calculate_discovery_score("verified_accessible", "restaurant", False, False)
    assert urg_act == 25

# --- OpenStreetMap Provider Tests ---

@pytest.mark.asyncio
async def test_osm_provider_valid_request():
    provider = OsmDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="osm",
        category="restaurant",
        city="Navi Mumbai",
        limit=10
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_NOMINATIM_SUCCESS

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        results = await provider.search(params)

        assert len(results) == 2  # 3rd entity was unnamed, so 2 results
        first = results[0]
        assert first.name == "Aura Spatial Consultants"
        assert first.location.city == "Navi Mumbai"
        assert first.website_url == "https://auraspatial.in"
        assert first.website_status == "verification_required"
        assert first.source_record_id == "node/1001"
        assert "OpenStreetMap" in first.attribution

        second = results[1]
        assert second.name == "Zenith Wooden Crafts"
        assert second.website_url is None
        assert second.website_status == "not_listed"
        assert second.source_record_id == "way/2002"

@pytest.mark.asyncio
async def test_osm_provider_bbox_overpass():
    provider = OsmDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="osm",
        category="restaurant",
        bbox=[18.99, 72.97, 19.19, 73.05],
        limit=10
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OVERPASS_SUCCESS

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        results = await provider.search(params)

        assert len(results) == 2
        assert results[0].name == "Aura Spatial Consultants"
        assert results[0].source_record_id == "node/1001"

@pytest.mark.asyncio
async def test_osm_provider_unmapped_category():
    provider = OsmDiscoveryProvider()
    tag_key, tag_val, info = provider.resolve_category("astrophysics research")
    assert tag_key is None
    assert info.confidence == "unmapped"
    assert len(info.suggested_alternatives) > 0

    params = DiscoverySearchParams(
        provider="osm",
        category="astrophysics research",
        city="Pune",
        limit=5
    )
    # When category cannot be represented reliably, returns empty list without fabricating
    results = await provider.search(params)
    assert results == []

@pytest.mark.asyncio
async def test_osm_provider_rate_limit_error():
    provider = OsmDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="osm",
        category="cafe",
        city="Mumbai",
        limit=5
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Too Many Requests"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc:
            await provider.search(params)
        assert "rate limit reached (HTTP 429)" in str(exc.value)

@pytest.mark.asyncio
async def test_osm_provider_timeout_error():
    provider = OsmDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="osm",
        category="hotel",
        city="Bengaluru",
        limit=5
    )

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timed out")), \
         patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(RuntimeError) as exc:
            await provider.search(params)
        assert "timed out" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_osm_provider_empty_results():
    provider = OsmDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="osm",
        category="bakery",
        city="TinyVillage",
        limit=5
    )

    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = []

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {"version": 0.6, "elements": []}

    with patch("httpx.AsyncClient.get", return_value=mock_get), \
         patch("httpx.AsyncClient.post", return_value=mock_post):
        results = await provider.search(params)
        assert results == []

# --- Google Places Provider Tests ---

def test_google_places_not_configured_by_default():
    provider = GooglePlacesDiscoveryProvider()
    with patch.object(provider, "_get_api_key", return_value=""):
        status = provider.get_configuration_status()
        assert status.is_configured is False
        assert "Not configured" in status.status_message
        assert status.requires_api_key is True

@pytest.mark.asyncio
async def test_google_places_search_without_key_raises_value_error():
    provider = GooglePlacesDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="google_places",
        category="dentist",
        city="Mumbai"
    )
    with patch.object(provider, "_get_api_key", return_value=""):
        with pytest.raises(ValueError) as exc:
            await provider.search(params)
        assert "not configured" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_google_places_configured_mock_search():
    provider = GooglePlacesDiscoveryProvider()
    params = DiscoverySearchParams(
        provider="google_places",
        category="architect",
        city="Mumbai",
        limit=5
    )

    mock_places_resp = {
        "places": [
            {
                "id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "displayName": {"text": "Vertex Design Studio"},
                "primaryType": "architect",
                "formattedAddress": "Bandra West, Mumbai",
                "websiteUri": "https://vertexdesign.in",
                "nationalPhoneNumber": "022 2640 1234",
                "rating": 4.8,
                "userRatingCount": 35,
                "location": {"latitude": 19.0596, "longitude": 72.8295}
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_places_resp

    with patch.object(provider, "_get_api_key", return_value="test_api_key_12345"):
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            results = await provider.search(params)
            assert len(results) == 1
            item = results[0]
            assert item.name == "Vertex Design Studio"
            assert item.source_provider == "google_places"
            assert item.website_url == "https://vertexdesign.in"
            assert item.website_status == "verification_required"
            assert item.attribution == "Powered by Google (Places API)"
