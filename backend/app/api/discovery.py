from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.discovery.models import (
    DiscoverySearchParams,
    DiscoveryResultItem,
    ProviderConfigStatus,
    DiscoveryRunRecord
)
from backend.app.discovery.service import discovery_service
from backend.app.schemas.prospect import db_prospect_to_schema

router = APIRouter(prefix="/discovery", tags=["Discovery"])

@router.get("/providers", response_model=List[ProviderConfigStatus])
def list_providers():
    """
    Returns discovery provider statuses, configuration states, and supported capabilities.
    """
    return discovery_service.get_providers()

@router.get("/categories")
def get_categories():
    """
    Returns supported category mappings, hints, and guidance for unmapped categories.
    """
    return discovery_service.get_supported_categories()

@router.post("/search", response_model=DiscoveryRunRecord)
async def execute_search(
    params: DiscoverySearchParams,
    db: Session = Depends(get_db)
):
    """
    Executes business search against configured provider,
    annotates results with duplicate status against database prospects,
    and returns a discovery run record with normalized results.
    """
    try:
        record = await discovery_service.execute_search(params, db)
        return record
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery search failed: {str(e)}"
        )

@router.get("/runs/{run_id}", response_model=DiscoveryRunRecord)
def get_run(run_id: str):
    """
    Returns discovery run status and results for asynchronous or cached execution.
    """
    record = discovery_service.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discovery run with ID '{run_id}' not found."
        )
    return record

@router.post("/save", status_code=status.HTTP_201_CREATED)
def save_discovered_prospect(
    item: DiscoveryResultItem,
    db: Session = Depends(get_db)
):
    """
    Persists a transient discovery result item into the SQLite database as a prospect record.
    Preserves source metadata and attribution.
    """
    try:
        prospect = discovery_service.save_item_as_prospect(item, db)
        return db_prospect_to_schema(prospect)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save prospect: {str(e)}"
        )
