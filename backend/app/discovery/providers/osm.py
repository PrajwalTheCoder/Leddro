import re
import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple

from backend.app.core.config import settings
from backend.app.discovery.base import BaseDiscoveryProvider
from backend.app.discovery.models import (
    DiscoverySearchParams,
    DiscoveryResultItem,
    NormalizedLocation,
    ProviderConfigStatus,
    CategoryMappingInfo
)
from backend.app.discovery.normalizer import (
    normalize_website_url,
    classify_website_status,
    calculate_discovery_score
)

logger = logging.getLogger("leddro.discovery.osm")

# Predefined category mappings for OpenStreetMap Overpass QL
OSM_CATEGORY_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "restaurant": {
        "tag_key": "amenity",
        "tag_val": "restaurant",
        "confidence": "exact",
        "label": "Restaurant",
        "notes": "Exact mapping: amenity=restaurant"
    },
    "cafe": {
        "tag_key": "amenity",
        "tag_val": "cafe",
        "confidence": "exact",
        "label": "Cafe",
        "notes": "Exact mapping: amenity=cafe"
    },
    "hotel": {
        "tag_key": "tourism",
        "tag_val": "hotel",
        "confidence": "exact",
        "label": "Hotel",
        "notes": "Exact mapping: tourism=hotel"
    },
    "retail": {
        "tag_key": "shop",
        "tag_val": None,  # any shop
        "confidence": "broad",
        "label": "Retail Shop",
        "notes": "Broad mapping: shop=* tag"
    },
    "bakery": {
        "tag_key": "shop",
        "tag_val": "bakery",
        "confidence": "exact",
        "label": "Bakery",
        "notes": "Exact mapping: shop=bakery"
    },
    "supermarket": {
        "tag_key": "shop",
        "tag_val": "supermarket",
        "confidence": "exact",
        "label": "Supermarket",
        "notes": "Exact mapping: shop=supermarket"
    },
    "clothing": {
        "tag_key": "shop",
        "tag_val": "clothes",
        "confidence": "exact",
        "label": "Clothing Store",
        "notes": "Exact mapping: shop=clothes"
    },
    "furniture": {
        "tag_key": "shop",
        "tag_val": "furniture",
        "confidence": "exact",
        "label": "Furniture & Home Decor",
        "notes": "Exact mapping: shop=furniture"
    },
    "office": {
        "tag_key": "office",
        "tag_val": None,
        "confidence": "broad",
        "label": "Commercial Office",
        "notes": "Broad mapping: office=* tag"
    },
    "company": {
        "tag_key": "office",
        "tag_val": "company",
        "confidence": "exact",
        "label": "Corporate Company",
        "notes": "Exact mapping: office=company"
    },
    "it": {
        "tag_key": "office",
        "tag_val": "it",
        "confidence": "exact",
        "label": "IT & Software Services",
        "notes": "Exact mapping: office=it"
    },
    "architect": {
        "tag_key": "office",
        "tag_val": "architect",
        "confidence": "exact",
        "label": "Architecture Studio",
        "notes": "Exact mapping: office=architect"
    },
    "interior design": {
        "tag_key": "shop",
        "tag_val": "interior_decoration",
        "confidence": "approximate",
        "label": "Interior Design & Decoration",
        "notes": "Approximate mapping: OpenStreetMap maps interior designers variably under shop=interior_decoration, craft=interior_work, or office=architect. Perfect coverage is not guaranteed."
    },
    "interior designers": {
        "tag_key": "shop",
        "tag_val": "interior_decoration",
        "confidence": "approximate",
        "label": "Interior Design & Decoration",
        "notes": "Approximate mapping: OpenStreetMap maps interior designers variably under shop=interior_decoration or office=architect."
    },
    "industrial": {
        "tag_key": "industrial",
        "tag_val": None,
        "confidence": "broad",
        "label": "Industrial Business",
        "notes": "Broad mapping: industrial=* tag"
    },
    "manufacturing": {
        "tag_key": "craft",
        "tag_val": None,
        "confidence": "approximate",
        "label": "Manufacturing / Craft",
        "notes": "Approximate mapping: craft=* tag"
    },
    "clinic": {
        "tag_key": "amenity",
        "tag_val": "clinic",
        "confidence": "exact",
        "label": "Medical Clinic",
        "notes": "Exact mapping: amenity=clinic"
    },
    "hospital": {
        "tag_key": "amenity",
        "tag_val": "hospital",
        "confidence": "exact",
        "label": "Hospital",
        "notes": "Exact mapping: amenity=hospital"
    },
    "pharmacy": {
        "tag_key": "amenity",
        "tag_val": "pharmacy",
        "confidence": "exact",
        "label": "Pharmacy",
        "notes": "Exact mapping: amenity=pharmacy"
    },
    "lawyer": {
        "tag_key": "office",
        "tag_val": "lawyer",
        "confidence": "exact",
        "label": "Law Practice",
        "notes": "Exact mapping: office=lawyer"
    },
    "accountant": {
        "tag_key": "office",
        "tag_val": "accountant",
        "confidence": "exact",
        "label": "Accounting Office",
        "notes": "Exact mapping: office=accountant"
    },
    "gym": {
        "tag_key": "leisure",
        "tag_val": "fitness_centre",
        "confidence": "exact",
        "label": "Fitness Center / Gym",
        "notes": "Exact mapping: leisure=fitness_centre"
    },
    "auto repair": {
        "tag_key": "shop",
        "tag_val": "car_repair",
        "confidence": "exact",
        "label": "Auto Repair",
        "notes": "Exact mapping: shop=car_repair"
    }
}

class OsmDiscoveryProvider(BaseDiscoveryProvider):
    """
    OpenStreetMap Overpass API discovery provider.
    Accesses public geospatial OSM entities under the Open Database License (ODbL).
    """

    @property
    def provider_id(self) -> str:
        return "osm"

    @property
    def name(self) -> str:
        return "OpenStreetMap (Overpass API)"

    @property
    def attribution(self) -> str:
        return "Data © OpenStreetMap contributors, available under the Open Database License (ODbL 1.0)."

    @property
    def data_retention_policy(self) -> str:
        return "OpenStreetMap data may be persisted and distributed with appropriate ODbL attribution."

    def get_configuration_status(self) -> ProviderConfigStatus:
        return ProviderConfigStatus(
            provider_id=self.provider_id,
            name=self.name,
            is_configured=True,
            status_message="Configured (Active public Overpass API endpoint)",
            supported_filters=["category", "city", "region", "country", "bbox", "limit"],
            attribution=self.attribution,
            data_retention_policy=self.data_retention_policy,
            rate_limit_info="Overpass public instances enforce max 2 concurrent requests/IP. Bounded query timeout is 25s.",
            requires_api_key=False
        )

    def resolve_category(self, category_str: str) -> Tuple[Optional[str], Optional[str], CategoryMappingInfo]:
        """
        Resolves a user-provided category into OSM tag key, tag value, and mapping confidence.
        """
        cleaned = category_str.strip().lower()
        if cleaned in OSM_CATEGORY_MAPPINGS:
            m = OSM_CATEGORY_MAPPINGS[cleaned]
            info = CategoryMappingInfo(
                category_query=category_str,
                mapped_tag=f"{m['tag_key']}={m['tag_val']}" if m['tag_val'] else f"{m['tag_key']}=*",
                confidence=m['confidence'],
                notes=m['notes'],
                suggested_alternatives=[]
            )
            return m['tag_key'], m['tag_val'], info

        # Check partial/substring match in known keys
        for key, m in OSM_CATEGORY_MAPPINGS.items():
            if key in cleaned or cleaned in key:
                info = CategoryMappingInfo(
                    category_query=category_str,
                    mapped_tag=f"{m['tag_key']}={m['tag_val']}" if m['tag_val'] else f"{m['tag_key']}=*",
                    confidence="approximate",
                    notes=f"Mapped to nearest matching category '{key}'. {m['notes']}",
                    suggested_alternatives=[k for k in OSM_CATEGORY_MAPPINGS.keys() if k != key][:4]
                )
                return m['tag_key'], m['tag_val'], info

        # Unmapped category
        suggested = ["restaurant", "cafe", "hotel", "office", "retail", "interior design", "company", "architect"]
        info = CategoryMappingInfo(
            category_query=category_str,
            mapped_tag=None,
            confidence="unmapped",
            notes=(
                f"Category '{category_str}' does not map cleanly to standard OpenStreetMap tags. "
                "OpenStreetMap may not consistently categorize this business type."
            ),
            suggested_alternatives=suggested
        )
        return None, None, info

    def validate_search_params(self, params: DiscoverySearchParams) -> None:
        if not params.category or not params.category.strip():
            raise ValueError("Category parameter is required.")
        if not params.city and not params.bbox and not params.region:
            raise ValueError("At least one geographic specifier (city, region, or bbox) is required for bounded search.")
        if params.bbox and len(params.bbox) != 4:
            raise ValueError("Bounding box must contain exactly 4 coordinates: [min_lat, min_lon, max_lat, max_lon].")
        if params.limit < 1 or params.limit > settings.DISCOVERY_MAX_RESULTS:
            raise ValueError(f"Limit must be between 1 and {settings.DISCOVERY_MAX_RESULTS}.")

    def build_overpass_query(
        self,
        params: DiscoverySearchParams,
        tag_key: str,
        tag_val: Optional[str]
    ) -> str:
        """
        Builds a safe, bounded Overpass QL query string.
        """
        timeout = int(settings.DISCOVERY_DEFAULT_TIMEOUT)
        limit = params.limit

        tag_filter = f'["{tag_key}"="{tag_val}"]' if tag_val else f'["{tag_key}"]'

        if params.bbox:
            min_lat, min_lon, max_lat, max_lon = params.bbox
            query = f"""
[out:json][timeout:{timeout}];
(
  node{tag_filter}({min_lat},{min_lon},{max_lat},{max_lon});
  way{tag_filter}({min_lat},{min_lon},{max_lat},{max_lon});
);
out center {limit};
"""
            return query.strip()

        # Location by City area
        city_escaped = params.city.strip().replace('"', '\\"')
        query = f"""
[out:json][timeout:{timeout}];
area["name"~"^{city_escaped}$",i]->.searchArea;
(
  node{tag_filter}(area.searchArea);
  way{tag_filter}(area.searchArea);
);
out center {limit};
"""
        return query.strip()

    async def _search_nominatim(
        self,
        client: httpx.AsyncClient,
        params: DiscoverySearchParams,
        mapping_info: CategoryMappingInfo
    ) -> List[DiscoveryResultItem]:
        """
        Fast OpenStreetMap POI search using official Nominatim search endpoint.
        Extremely responsive (<1s) for city and locality queries without Overpass gateway timeouts.
        """
        parts = [params.category]
        if params.city:
            parts.append(f"in {params.city}")
        if params.region:
            parts.append(params.region)
        if params.country:
            parts.append(params.country)
        query_text = ", ".join(parts)

        query_params = {
            "q": query_text,
            "format": "json",
            "addressdetails": "1",
            "extratags": "1",
            "limit": str(min(params.limit * 2, 50))
        }

        if params.bbox:
            min_lat, min_lon, max_lat, max_lon = params.bbox
            query_params["viewbox"] = f"{min_lon},{max_lat},{max_lon},{min_lat}"
            query_params["bounded"] = "1"

        headers = {
            "User-Agent": settings.OSM_USER_AGENT,
            "Accept": "application/json"
        }

        try:
            response = await client.get(
                settings.OSM_NOMINATIM_URL,
                params=query_params,
                headers=headers
            )
            if response.status_code == 429:
                raise RuntimeError("OpenStreetMap API rate limit reached (HTTP 429). Please wait a moment before searching again.")
            elif response.status_code == 504:
                raise RuntimeError("OpenStreetMap API timed out (HTTP 504). Please narrow your search.")
            elif response.status_code != 200:
                raise RuntimeError(f"OpenStreetMap Nominatim returned HTTP {response.status_code}: {response.text[:200]}")

            items = response.json()
        except httpx.TimeoutException:
            raise RuntimeError("Request to OpenStreetMap API timed out. Try searching with a smaller city or bounding box.")
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network error contacting OpenStreetMap API: {str(exc)}")

        results: List[DiscoveryResultItem] = []
        if not isinstance(items, list):
            return results

        for item in items:
            name = (
                item.get("name") or 
                (item.get("address") or {}).get("amenity") or 
                (item.get("address") or {}).get("shop") or 
                (item.get("address") or {}).get("office") or 
                ""
            ).strip()

            if not name:
                continue

            elem_id = item.get("osm_id") or item.get("place_id")
            elem_type = item.get("osm_type", "node")
            record_id = f"{elem_type}/{elem_id}"

            extratags = item.get("extratags") or {}
            raw_url = (
                extratags.get("website") or 
                extratags.get("contact:website") or 
                extratags.get("url") or 
                extratags.get("contact:url") or
                extratags.get("brand:website")
            )
            canonical_url = normalize_website_url(raw_url)
            condition = classify_website_status(bool(canonical_url))

            if params.condition_filter == "with_website" and not canonical_url:
                continue
            if params.condition_filter == "without_website" and canonical_url:
                continue

            phone = extratags.get("phone") or extratags.get("contact:phone")
            email = extratags.get("email") or extratags.get("contact:email")

            lat = float(item["lat"]) if "lat" in item and item["lat"] is not None else None
            lon = float(item["lon"]) if "lon" in item and item["lon"] is not None else None

            addr = item.get("address") or {}
            city = addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("suburb") or params.city or ""
            state = addr.get("state") or params.region or ""
            country = addr.get("country") or params.country or ""
            formatted_address = item.get("display_name")
            postal_code = addr.get("postcode")

            total_score, urgency, intent, ease = calculate_discovery_score(
                condition,
                params.category,
                bool(phone),
                bool(email)
            )

            result_item = DiscoveryResultItem(
                id=f"osm_{elem_type}_{elem_id}",
                name=name,
                category=mapping_info.category_query.title(),
                location=NormalizedLocation(
                    city=city,
                    state=state,
                    country=country,
                    address=formatted_address,
                    postal_code=postal_code,
                    latitude=lat,
                    longitude=lon
                ),
                website_url=canonical_url,
                website_status=condition,
                phone=phone,
                email=email,
                source_provider=self.provider_id,
                source_record_id=record_id,
                source_url=f"https://www.openstreetmap.org/{elem_type}/{elem_id}",
                attribution=self.attribution,
                is_saved=False,
                matched_existing_id=None,
                duplicate_reason=None,
                opportunity_score=total_score,
                score_urgency=urgency,
                score_intent=intent,
                score_ease=ease,
                tags=["OpenStreetMap", params.category.title()],
                raw_metadata={
                    "osm_type": elem_type,
                    "osm_id": elem_id,
                    "extratags": extratags,
                    "mapping_confidence": mapping_info.confidence
                }
            )
            results.append(result_item)
            if len(results) >= params.limit:
                break

        return results

    async def _search_overpass(
        self,
        client: httpx.AsyncClient,
        params: DiscoverySearchParams,
        tag_key: str,
        tag_val: Optional[str],
        mapping_info: CategoryMappingInfo
    ) -> List[DiscoveryResultItem]:
        """
        Geospatial bounding box search using OpenStreetMap Overpass QL.
        """
        query_str = self.build_overpass_query(params, tag_key, tag_val)
        headers = {
            "User-Agent": settings.OSM_USER_AGENT,
            "Accept": "application/json"
        }

        try:
            response = await client.post(
                settings.OSM_OVERPASS_URL,
                data={"data": query_str},
                headers=headers
            )
            if response.status_code == 429:
                raise RuntimeError("OpenStreetMap API rate limit reached (HTTP 429). Please wait a moment before searching again.")
            elif response.status_code == 504:
                raise RuntimeError("OpenStreetMap API timed out (HTTP 504). Please narrow your geographic boundary.")
            elif response.status_code != 200:
                raise RuntimeError(f"OpenStreetMap Overpass API returned HTTP {response.status_code}: {response.text[:200]}")

            data = response.json()
        except httpx.TimeoutException:
            raise RuntimeError("Request to OpenStreetMap Overpass API timed out. Try searching with a smaller city or bounding box.")
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network error contacting OpenStreetMap Overpass API: {str(exc)}")

        elements = data.get("elements", [])
        results: List[DiscoveryResultItem] = []

        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name") or tags.get("brand") or tags.get("operator")
            if not name:
                continue

            elem_id = elem.get("id")
            elem_type = elem.get("type", "node")
            record_id = f"{elem_type}/{elem_id}"

            raw_url = (
                tags.get("website") or 
                tags.get("contact:website") or 
                tags.get("url") or 
                tags.get("contact:url")
            )
            canonical_url = normalize_website_url(raw_url)
            condition = classify_website_status(bool(canonical_url))

            if params.condition_filter == "with_website" and not canonical_url:
                continue
            if params.condition_filter == "without_website" and canonical_url:
                continue

            phone = tags.get("phone") or tags.get("contact:phone")
            email = tags.get("email") or tags.get("contact:email")

            lat = elem.get("lat") or elem.get("center", {}).get("lat")
            lon = elem.get("lon") or elem.get("center", {}).get("lon")

            street = tags.get("addr:street")
            housenumber = tags.get("addr:housenumber")
            full_addr = tags.get("addr:full")
            address = full_addr or (f"{housenumber or ''} {street or ''}".strip() if street else None)

            city = tags.get("addr:city") or params.city or "Mumbai"
            state = tags.get("addr:state") or params.region or "Maharashtra"
            country = tags.get("addr:country") or params.country or "India"

            total_score, urgency, intent, ease = calculate_discovery_score(
                condition,
                params.category,
                bool(phone),
                bool(email)
            )

            item = DiscoveryResultItem(
                id=f"osm_{elem_type}_{elem_id}",
                name=name.strip(),
                category=mapping_info.category_query.title(),
                location=NormalizedLocation(
                    city=city,
                    state=state,
                    country=country,
                    address=address,
                    latitude=lat,
                    longitude=lon
                ),
                website_url=canonical_url,
                website_status=condition,
                phone=phone,
                email=email,
                source_provider=self.provider_id,
                source_record_id=record_id,
                source_url=f"https://www.openstreetmap.org/{elem_type}/{elem_id}",
                attribution=self.attribution,
                is_saved=False,
                matched_existing_id=None,
                duplicate_reason=None,
                opportunity_score=total_score,
                score_urgency=urgency,
                score_intent=intent,
                score_ease=ease,
                tags=["OpenStreetMap", params.category.title()],
                raw_metadata={
                    "osm_type": elem_type,
                    "osm_id": elem_id,
                    "all_tags": tags,
                    "mapping_confidence": mapping_info.confidence
                }
            )
            results.append(item)
            if len(results) >= params.limit:
                break

        return results

    async def search(self, params: DiscoverySearchParams) -> List[DiscoveryResultItem]:
        self.validate_search_params(params)
        tag_key, tag_val, mapping_info = self.resolve_category(params.category)

        if not tag_key:
            # Category cannot be represented reliably; return empty list with warning
            logger.warning(f"Unmapped category requested: {params.category}")
            return []

        async with httpx.AsyncClient(timeout=settings.DISCOVERY_DEFAULT_TIMEOUT) as client:
            # If explicit bounding box without city is specified, use Overpass
            if params.bbox and not params.city:
                return await self._search_overpass(client, params, tag_key, tag_val, mapping_info)

            # For city searches, use official Nominatim POI search for instant, reliable results
            try:
                results = await self._search_nominatim(client, params, mapping_info)
                if results:
                    return results
            except (RuntimeError, Exception) as exc:
                # If explicit rate limit, re-raise
                if "rate limit reached" in str(exc).lower():
                    raise
                logger.warning(f"Nominatim search failed or empty, falling back to Overpass: {exc}")

            # Fallback to Overpass API
            return await self._search_overpass(client, params, tag_key, tag_val, mapping_info)
