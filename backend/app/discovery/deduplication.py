from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from backend.app.models.prospect import ProspectModel
from backend.app.discovery.normalizer import (
    normalize_business_name,
    normalize_website_url,
    extract_registered_domain
)

class DuplicateMatch(BaseModel):
    is_duplicate: bool
    existing_id: str
    existing_name: str
    match_type: str  # 'record_id', 'domain', 'name_location'
    reason: str

def check_single_duplicate(
    db: Session,
    name: str,
    website_url: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    source_provider: Optional[str] = None,
    source_record_id: Optional[str] = None
) -> Optional[DuplicateMatch]:
    """
    Deterministic duplicate detection against existing database prospects.
    Uses:
    1. Provider source record ID (if both are present).
    2. Normalized website domain (ignoring www and protocols).
    3. Normalized business name combined with matching city/locality (does NOT merge branches in different cities).
    """
    # 1. Check by Provider Record ID
    if source_provider and source_record_id:
        existing_by_id = db.query(ProspectModel).filter(
            ProspectModel.source_provider == source_provider,
            ProspectModel.source_record_id == source_record_id
        ).first()
        if existing_by_id:
            return DuplicateMatch(
                is_duplicate=True,
                existing_id=existing_by_id.id,
                existing_name=existing_by_id.name,
                match_type="record_id",
                reason=f"Matches existing {source_provider} record identifier '{source_record_id}' ({existing_by_id.name})"
            )

    # 2. Check by Domain
    candidate_domain = extract_registered_domain(website_url)
    if candidate_domain:
        # Avoid matching generic public hosts
        generic_hosts = {"gmail.com", "yahoo.com", "outlook.com", "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com"}
        if candidate_domain not in generic_hosts:
            safe_domain = candidate_domain.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            # Query only prospects whose website_url contains the candidate domain (eliminates full-table scan)
            prospects_with_url = db.query(ProspectModel).filter(
                ProspectModel.website_url.ilike(f"%{safe_domain}%", escape="\\")
            ).all()
            for p in prospects_with_url:
                p_domain = extract_registered_domain(p.website_url)
                if p_domain and p_domain == candidate_domain:
                    return DuplicateMatch(
                        is_duplicate=True,
                        existing_id=p.id,
                        existing_name=p.name,
                        match_type="domain",
                        reason=f"Matches registered website domain '{candidate_domain}' (prospect '{p.name}')"
                    )

    # 3. Check by Business Name and Location
    norm_candidate_name = normalize_business_name(name)
    if norm_candidate_name and len(norm_candidate_name) >= 3:
        # Efficiently pre-filter candidates by significant name token instead of full-table scan
        tokens = [t for t in norm_candidate_name.split() if len(t) >= 2]
        best_token = max(tokens, key=len) if tokens else norm_candidate_name[:3]
        safe_token = best_token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        potential_matches = db.query(ProspectModel).filter(
            ProspectModel.name.ilike(f"%{safe_token}%", escape="\\")
        ).all()
        candidate_city = (city or "").strip().lower()

        for p in potential_matches:
            norm_existing_name = normalize_business_name(p.name)
            if norm_existing_name == norm_candidate_name:
                p_city = (p.city or "").strip().lower()
                # If city matches, or if either city is blank, consider it a duplicate
                if candidate_city and p_city:
                    if candidate_city == p_city:
                        return DuplicateMatch(
                            is_duplicate=True,
                            existing_id=p.id,
                            existing_name=p.name,
                            match_type="name_location",
                            reason=f"Matches business name and city '{p.name}' in {p.city}"
                        )
                elif candidate_city == p_city:  # both empty
                    return DuplicateMatch(
                        is_duplicate=True,
                        existing_id=p.id,
                        existing_name=p.name,
                        match_type="name_location",
                        reason=f"Matches business name '{p.name}'"
                    )

    return None

def annotate_discovery_results_with_duplicates(
    db: Session,
    results: List[Any]
) -> List[Any]:
    """
    Annotates a list of DiscoveryResultItem objects with is_saved,
    matched_existing_id, and duplicate_reason.
    """
    for item in results:
        match = check_single_duplicate(
            db=db,
            name=item.name,
            website_url=item.website_url,
            city=item.location.city if hasattr(item, "location") and item.location else None,
            state=item.location.state if hasattr(item, "location") and item.location else None,
            country=item.location.country if hasattr(item, "location") and item.location else None,
            source_provider=getattr(item, "source_provider", None),
            source_record_id=getattr(item, "source_record_id", None)
        )
        if match:
            item.is_saved = True
            item.matched_existing_id = match.existing_id
            item.duplicate_reason = match.reason
        else:
            item.is_saved = False
            item.matched_existing_id = None
            item.duplicate_reason = None
    return results
