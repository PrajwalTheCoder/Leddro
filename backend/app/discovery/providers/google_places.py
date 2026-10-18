import os
import logging
import httpx
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.discovery.base import BaseDiscoveryProvider
from backend.app.discovery.models import (
    DiscoverySearchParams,
    DiscoveryResultItem,
    NormalizedLocation,
    ProviderConfigStatus
)
from backend.app.discovery.normalizer import (
    normalize_website_url,
    classify_website_status,
    calculate_discovery_score
)

logger = logging.getLogger("leddro.discovery.google_places")

GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

class GooglePlacesDiscoveryProvider(BaseDiscoveryProvider):
    """
    Optional Google Places API (New) discovery provider.
    Ensures strict adherence to Google Maps Platform Terms of Service:
    - API keys remain strictly on the backend.
    - Fields are restricted via FieldMask.
    - Results are transient provider-result objects (no persistent caching without explicit license).
    - Status is displayed honestly as 'Not configured' if API key is absent.
    """

    @property
    def provider_id(self) -> str:
        return "google_places"

    @property
    def name(self) -> str:
        return "Google Places API"

    @property
    def attribution(self) -> str:
        return "Powered by Google (Places API)"

    @property
    def data_retention_policy(self) -> str:
        return "Transient search results. Google Maps Platform Terms of Service prohibit persistent caching of place details without explicit license."

    def _get_api_key(self) -> str:
        return (settings.GOOGLE_PLACES_API_KEY or os.environ.get("GOOGLE_PLACES_API_KEY") or "").strip()

    def get_configuration_status(self) -> ProviderConfigStatus:
        api_key = self._get_api_key()
        is_configured = bool(api_key)
        status_msg = (
            "Configured (API key active)" 
            if is_configured 
            else "Not configured (GOOGLE_PLACES_API_KEY environment variable is not set)"
        )

        return ProviderConfigStatus(
            provider_id=self.provider_id,
            name=self.name,
            is_configured=is_configured,
            status_message=status_msg,
            supported_filters=["category", "city", "region", "country", "limit"],
            attribution=self.attribution,
            data_retention_policy=self.data_retention_policy,
            rate_limit_info="Subject to Google Maps Platform quotas and project billing limits.",
            requires_api_key=True
        )

    def validate_search_params(self, params: DiscoverySearchParams) -> None:
        if not self._get_api_key():
            raise ValueError("Google Places provider is not configured. Set the GOOGLE_PLACES_API_KEY environment variable on your backend.")
        if not params.category or not params.category.strip():
            raise ValueError("Category parameter is required.")
        if not params.city and not params.region and not params.country:
            raise ValueError("A location (city, region, or country) is required for Google Places search.")
        if params.limit < 1 or params.limit > settings.DISCOVERY_MAX_RESULTS:
            raise ValueError(f"Limit must be between 1 and {settings.DISCOVERY_MAX_RESULTS}.")

    async def search(self, params: DiscoverySearchParams) -> List[DiscoveryResultItem]:
        self.validate_search_params(params)
        api_key = self._get_api_key()

        # Construct search text query
        location_parts = [p for p in [params.city, params.region, params.country] if p]
        text_query = f"{params.category} in {', '.join(location_parts)}"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.primaryType,"
                "places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,"
                "places.rating,places.userRatingCount,places.location"
            )
        }

        payload: Dict[str, Any] = {
            "textQuery": text_query,
            "pageSize": min(params.limit, 20)  # Google Places searchText max pageSize is 20 per request
        }

        async with httpx.AsyncClient(timeout=settings.DISCOVERY_DEFAULT_TIMEOUT) as client:
            try:
                response = await client.post(
                    GOOGLE_PLACES_TEXT_SEARCH_URL,
                    json=payload,
                    headers=headers
                )
                if response.status_code == 403:
                    raise RuntimeError("Google Places API request forbidden: Check API key validity and enabled APIs in Google Cloud Console.")
                elif response.status_code == 429:
                    raise RuntimeError("Google Places API quota exceeded (HTTP 429).")
                elif response.status_code != 200:
                    raise RuntimeError(f"Google Places API error (HTTP {response.status_code}): {response.text[:200]}")

                data = response.json()
            except httpx.TimeoutException:
                raise RuntimeError("Request to Google Places API timed out.")
            except httpx.RequestError as exc:
                raise RuntimeError(f"Network error contacting Google Places API: {str(exc)}")

        places = data.get("places", [])
        results: List[DiscoveryResultItem] = []

        for place in places:
            display_name = place.get("displayName", {}).get("text", "")
            if not display_name:
                continue

            place_id = place.get("id", "")
            website_uri = place.get("websiteUri")
            canonical_url = normalize_website_url(website_uri)
            condition = classify_website_status(bool(canonical_url))

            if params.condition_filter == "with_website" and not canonical_url:
                continue
            if params.condition_filter == "without_website" and canonical_url:
                continue

            phone = place.get("nationalPhoneNumber")
            address = place.get("formattedAddress")
            loc_coords = place.get("location", {})
            lat = loc_coords.get("latitude")
            lon = loc_coords.get("longitude")

            total_score, urgency, intent, ease = calculate_discovery_score(
                condition,
                params.category,
                bool(phone),
                False
            )

            results.append(
                DiscoveryResultItem(
                    id=f"gp_{place_id}",
                    name=display_name.strip(),
                    category=place.get("primaryType", params.category).replace("_", " ").title(),
                    location=NormalizedLocation(
                        city=params.city or "",
                        state=params.region or "",
                        country=params.country or "India",
                        address=address,
                        latitude=lat,
                        longitude=lon
                    ),
                    website_url=canonical_url,
                    website_status=condition,
                    phone=phone,
                    email=None,
                    source_provider=self.provider_id,
                    source_record_id=place_id,
                    source_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    attribution=self.attribution,
                    is_saved=False,
                    opportunity_score=total_score,
                    score_urgency=urgency,
                    score_intent=intent,
                    score_ease=ease,
                    tags=["Google Places", params.category.title()],
                    raw_metadata={
                        "rating": place.get("rating"),
                        "userRatingCount": place.get("userRatingCount"),
                        "primaryType": place.get("primaryType")
                    }
                )
            )
            if len(results) >= params.limit:
                break

        return results
