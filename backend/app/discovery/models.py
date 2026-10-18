from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class WebsiteStatusSemantic(str, Enum):
    WEBSITE_LISTED = "website_listed"
    WEBSITE_NOT_LISTED = "not_listed"
    WEBSITE_VERIFIED_ACCESSIBLE = "verified_accessible"
    WEBSITE_VERIFICATION_FAILED = "verification_failed"
    WEBSITE_VERIFICATION_REQUIRED = "verification_required"

class DiscoverySearchParams(BaseModel):
    provider: str = Field(default="osm", description="Provider ID: 'osm', 'google_places', 'csv'")
    category: str = Field(..., min_length=1, description="Business category or service (e.g. 'restaurant', 'cafe', 'interior design')")
    country: str = Field(default="India", description="Country name or ISO code")
    region: Optional[str] = Field(default=None, description="State, province, or region")
    city: Optional[str] = Field(default=None, description="City, town, or locality name")
    bbox: Optional[List[float]] = Field(default=None, description="Geographic bounding box [min_lat, min_lon, max_lat, max_lon]")
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of results (1-100)")
    condition_filter: Optional[str] = Field(default="all", description="'all', 'with_website', 'without_website'")

class NormalizedLocation(BaseModel):
    city: str = ""
    state: str = ""
    country: str = "India"
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DiscoveryResultItem(BaseModel):
    id: str
    name: str
    category: str
    location: NormalizedLocation
    website_url: Optional[str] = None
    website_status: str = "verification_required"
    phone: Optional[str] = None
    email: Optional[str] = None
    source_provider: str
    source_record_id: Optional[str] = None
    source_url: Optional[str] = None
    attribution: str = ""
    is_saved: bool = False
    matched_existing_id: Optional[str] = None
    duplicate_reason: Optional[str] = None
    opportunity_score: int = 70
    score_urgency: int = 25
    score_intent: int = 25
    score_ease: int = 20
    tags: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class ProviderConfigStatus(BaseModel):
    provider_id: str
    name: str
    is_configured: bool
    status_message: str
    supported_filters: List[str] = Field(default_factory=list)
    attribution: str = ""
    data_retention_policy: str = ""
    rate_limit_info: str = ""
    requires_api_key: bool = False

class DiscoveryRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class DiscoveryRunRecord(BaseModel):
    run_id: str
    provider: str
    params: DiscoverySearchParams
    status: DiscoveryRunStatus
    created_at: str
    completed_at: Optional[str] = None
    results_count: int = 0
    results: List[DiscoveryResultItem] = Field(default_factory=list)
    error_message: Optional[str] = None
    partial_results: bool = False
    attribution: str = ""
    warnings: List[str] = Field(default_factory=list)

class CategoryMappingInfo(BaseModel):
    category_query: str
    mapped_tag: Optional[str] = None
    confidence: str = "exact"  # exact, approximate, unmapped
    notes: str = ""
    suggested_alternatives: List[str] = Field(default_factory=list)
