import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.discovery.base import BaseDiscoveryProvider
from backend.app.discovery.models import (
    DiscoverySearchParams,
    DiscoveryResultItem,
    ProviderConfigStatus,
    DiscoveryRunRecord,
    DiscoveryRunStatus,
    CategoryMappingInfo
)
from backend.app.discovery.providers.osm import OsmDiscoveryProvider, OSM_CATEGORY_MAPPINGS
from backend.app.discovery.providers.google_places import GooglePlacesDiscoveryProvider
from backend.app.discovery.deduplication import (
    annotate_discovery_results_with_duplicates,
    check_single_duplicate
)
from backend.app.models.prospect import ProspectModel
import json

logger = logging.getLogger("leddro.discovery.service")

class DiscoveryService:
    """
    Central discovery service managing providers, asynchronous search runs,
    deduplication against the active SQLite database, and pipeline ingestion.
    """

    def __init__(self):
        self._providers: Dict[str, BaseDiscoveryProvider] = {
            "osm": OsmDiscoveryProvider(),
            "google_places": GooglePlacesDiscoveryProvider(),
        }
        # In-memory store for transient discovery runs
        self._runs: Dict[str, DiscoveryRunRecord] = {}

    def get_providers(self) -> List[ProviderConfigStatus]:
        return [p.get_configuration_status() for p in self._providers.values()]

    def get_provider(self, provider_id: str) -> BaseDiscoveryProvider:
        provider = self._providers.get(provider_id)
        if not provider:
            raise ValueError(f"Provider '{provider_id}' is not supported. Supported: {list(self._providers.keys())}")
        return provider

    def get_supported_categories(self) -> Dict[str, Any]:
        """
        Returns supported category mappings and metadata for UI guidance.
        """
        categories = []
        for cat_name, info in OSM_CATEGORY_MAPPINGS.items():
            categories.append({
                "category": cat_name,
                "label": info["label"],
                "confidence": info["confidence"],
                "notes": info["notes"],
                "tag": f"{info['tag_key']}={info['tag_val']}" if info['tag_val'] else f"{info['tag_key']}=*"
            })
        return {
            "total_supported": len(categories),
            "categories": sorted(categories, key=lambda x: x["category"]),
            "unmapped_guidance": (
                "Categories not listed above (e.g. specialized consultants) may be mapped "
                "approximately or return 0 records due to inconsistent tagging in geographic registries. "
                "Use broad keywords (e.g., 'office', 'shop', 'architect') for better coverage."
            )
        }

    def get_run(self, run_id: str) -> Optional[DiscoveryRunRecord]:
        return self._runs.get(run_id)

    async def execute_search(
        self,
        params: DiscoverySearchParams,
        db: Session
    ) -> DiscoveryRunRecord:
        """
        Executes business search using the selected provider,
        annotates matches against existing database prospects,
        and saves run record into transient storage.
        """
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = DiscoveryRunRecord(
            run_id=run_id,
            provider=params.provider,
            params=params,
            status=DiscoveryRunStatus.RUNNING,
            created_at=now_iso,
            results_count=0,
            results=[],
            error_message=None,
            partial_results=False,
            attribution="",
            warnings=[]
        )
        self._runs[run_id] = record

        try:
            provider = self.get_provider(params.provider)
            record.attribution = provider.attribution

            # Execute provider search
            results = await provider.search(params)

            # Annotate with duplicate state against SQLite database
            annotated_results = annotate_discovery_results_with_duplicates(db, results)

            record.results = annotated_results
            record.results_count = len(annotated_results)
            record.status = DiscoveryRunStatus.COMPLETED
            record.completed_at = datetime.now(timezone.utc).isoformat()

            # Add warning if category is approximate
            if hasattr(provider, "resolve_category"):
                _, _, cat_info = provider.resolve_category(params.category)
                if cat_info.confidence != "exact" and cat_info.notes:
                    record.warnings.append(cat_info.notes)

        except Exception as e:
            logger.error(f"Discovery search failed for run {run_id}: {str(e)}", exc_info=True)
            record.status = DiscoveryRunStatus.FAILED
            record.error_message = str(e)
            record.completed_at = datetime.now(timezone.utc).isoformat()

        self._runs[run_id] = record
        return record

    def save_item_as_prospect(
        self,
        item: DiscoveryResultItem,
        db: Session
    ) -> ProspectModel:
        """
        Persists a single transient discovery result item into the SQLite database.
        Checks for duplicates before inserting.
        """
        dupe = check_single_duplicate(
            db=db,
            name=item.name,
            website_url=item.website_url,
            city=item.location.city,
            state=item.location.state,
            country=item.location.country,
            source_provider=item.source_provider,
            source_record_id=item.source_record_id
        )

        if dupe:
            existing = db.query(ProspectModel).filter(ProspectModel.id == dupe.existing_id).first()
            if existing:
                return existing

        new_id = f"pros_{uuid.uuid4().hex[:8]}"
        prospect = ProspectModel(
            id=new_id,
            name=item.name,
            category=item.category,
            city=item.location.city or "Mumbai",
            state=item.location.state or "Maharashtra",
            country=item.location.country or "India",
            website_url=item.website_url,
            website_status=item.website_status,
            opportunity_score=item.opportunity_score,
            score_urgency=item.score_urgency,
            score_intent=item.score_intent,
            score_ease=item.score_ease,
            status="new",
            last_activity="Discovered and saved",
            phone=item.phone,
            email=item.email,
            audit_count=0,
            latest_audit_id=None,
            tags=json.dumps(item.tags or ["Discovered"]),
            recommended_action=(
                "Execute website diagnostic audit." 
                if item.website_url 
                else "Verify business telephone and physical listing."
            ),
            notes=f"Discovered via {item.source_provider}. Attribution: {item.attribution}",
            source_provider=item.source_provider,
            source_record_id=item.source_record_id,
            source_url=item.source_url,
            discovered_at=datetime.now(timezone.utc),
            last_verified_at=None
        )

        db.add(prospect)
        try:
            db.commit()
            db.refresh(prospect)
        except Exception:
            db.rollback()
            raise
        return prospect

discovery_service = DiscoveryService()
