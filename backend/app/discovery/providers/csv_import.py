import io
import csv
import re
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.models.prospect import ProspectModel
from backend.app.discovery.normalizer import (
    normalize_website_url,
    classify_website_status,
    sanitize_csv_cell,
    calculate_discovery_score,
    normalize_business_name,
    extract_registered_domain
)
from backend.app.discovery.deduplication import check_single_duplicate

STANDARD_FIELDS = {
    "name": ["business name", "company name", "name", "company", "business", "entity", "title"],
    "category": ["category", "industry", "type", "business type", "sector"],
    "city": ["city", "locality", "town", "location"],
    "state": ["state", "province", "region"],
    "country": ["country", "nation"],
    "website_url": ["website url", "website", "url", "web", "site", "domain"],
    "email": ["email", "public business email", "mail", "contact email", "e-mail"],
    "phone": ["telephone number", "phone", "telephone", "tel", "mobile", "contact number"],
    "opportunity_score": ["opportunity score", "score", "priority"]
}

class CsvPreviewRecord(BaseModel):
    row_number: int
    name: str
    category: str
    city: str
    state: str
    country: str
    website_url: Optional[str] = None
    website_status: str
    phone: Optional[str] = None
    email: Optional[str] = None
    opportunity_score: int
    is_duplicate: bool = False
    duplicate_reason: Optional[str] = None
    existing_id: Optional[str] = None

class CsvInvalidRecord(BaseModel):
    row_number: int
    error: str
    raw_data: Dict[str, Any]

class CsvImportPreviewResponse(BaseModel):
    headers: List[str]
    column_mapping: Dict[str, str]
    total_rows: int
    valid_count: int
    duplicate_count: int
    invalid_count: int
    preview_records: List[CsvPreviewRecord]
    invalid_records: List[CsvInvalidRecord]

class CsvImportConfirmRequest(BaseModel):
    records: List[Dict[str, Any]]
    skip_duplicates: bool = True

class CsvImportSummaryResponse(BaseModel):
    imported_count: int
    skipped_duplicates_count: int
    total_processed: int
    created_prospect_ids: List[str]

def auto_detect_column_mapping(headers: List[str]) -> Dict[str, str]:
    """
    Intelligently maps CSV column headers to Leddro standard fields based on aliases.
    """
    mapping: Dict[str, str] = {}
    normalized_headers = {h.strip().lower(): h for h in headers if h}

    for standard_field, aliases in STANDARD_FIELDS.items():
        matched = False
        for alias in aliases:
            if alias in normalized_headers:
                mapping[standard_field] = normalized_headers[alias]
                matched = True
                break
        if not matched:
            # Fallback substring matching
            for norm_h, orig_h in normalized_headers.items():
                if any(alias in norm_h for alias in aliases):
                    mapping[standard_field] = orig_h
                    break

    return mapping

def parse_csv_stream(csv_content: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Parses raw CSV content supporting standard RFC 4180 formatting:
    - Quoted fields containing commas
    - Multi-line quoted values
    - UTF-8 and unicode characters
    """
    # Clean BOM if present
    cleaned_content = csv_content.lstrip("\ufeff").strip()
    if not cleaned_content:
        return [], []

    stream = io.StringIO(cleaned_content)
    reader = csv.reader(stream)

    try:
        raw_headers = next(reader, None)
    except Exception as e:
        raise ValueError(f"Failed to read CSV headers: {str(e)}")

    if not raw_headers:
        return [], []

    headers = [h.strip() for h in raw_headers]
    rows: List[Dict[str, str]] = []

    for row_idx, row in enumerate(reader, start=2):
        if not row or all(not cell.strip() for cell in row):
            continue  # skip completely blank lines
        row_dict: Dict[str, str] = {}
        for i, header in enumerate(headers):
            val = row[i] if i < len(row) else ""
            # Apply formula injection sanitization
            row_dict[header] = sanitize_csv_cell(val)
        rows.append(row_dict)

    return headers, rows

def preview_csv_import(
    db: Session,
    csv_content: str,
    custom_mapping: Optional[Dict[str, str]] = None
) -> CsvImportPreviewResponse:
    """
    Validates CSV records, detects duplicates against the database,
    and returns a preview without writing to SQLite.
    """
    headers, rows = parse_csv_stream(csv_content)
    if not headers:
        raise ValueError("CSV contains no valid header row.")

    mapping = custom_mapping or auto_detect_column_mapping(headers)

    preview_records: List[CsvPreviewRecord] = []
    invalid_records: List[CsvInvalidRecord] = []
    duplicate_count = 0

    name_col = mapping.get("name")
    category_col = mapping.get("category")
    city_col = mapping.get("city")
    state_col = mapping.get("state")
    country_col = mapping.get("country")
    website_col = mapping.get("website_url")
    email_col = mapping.get("email")
    phone_col = mapping.get("phone")
    score_col = mapping.get("opportunity_score")

    seen_batch_urls = set()
    seen_batch_names = set()

    for idx, row in enumerate(rows, start=2):
        raw_name = row.get(name_col, "").strip() if name_col else ""
        if not raw_name:
            invalid_records.append(
                CsvInvalidRecord(
                    row_number=idx,
                    error="Missing required business name.",
                    raw_data=row
                )
            )
            continue

        raw_category = row.get(category_col, "Commercial Services").strip() if category_col else "Commercial Services"
        raw_city = row.get(city_col, "").strip() if city_col else "Mumbai"
        raw_state = row.get(state_col, "").strip() if state_col else "Maharashtra"
        raw_country = row.get(country_col, "India").strip() if country_col else "India"

        raw_website = row.get(website_col, "").strip() if website_col else None
        canonical_website = normalize_website_url(raw_website)
        condition = classify_website_status(bool(canonical_website))

        raw_email = row.get(email_col, "").strip() if email_col else None
        if raw_email and "@" not in raw_email:
            raw_email = None  # discard obviously malformed emails

        raw_phone = row.get(phone_col, "").strip() if phone_col else None

        # Parse opportunity score
        opp_score = 70
        if score_col and row.get(score_col):
            try:
                opp_score = int(re.sub(r"[^\d]", "", row[score_col]))
                opp_score = max(10, min(100, opp_score))
            except Exception:
                opp_score = 70
        else:
            opp_score, _, _, _ = calculate_discovery_score(condition, raw_category, bool(raw_phone), bool(raw_email))

        # Check duplicate against database and within current batch
        dupe_match = check_single_duplicate(
            db=db,
            name=raw_name,
            website_url=canonical_website,
            city=raw_city,
            state=raw_state,
            country=raw_country,
            source_provider="csv_import"
        )

        is_dupe = bool(dupe_match)
        dupe_reason = dupe_match.reason if dupe_match else None
        dupe_existing_id = dupe_match.existing_id if dupe_match else None

        # Check for intra-batch duplicates
        candidate_domain = extract_registered_domain(canonical_website)
        generic_hosts = {"gmail.com", "yahoo.com", "outlook.com", "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com"}
        if candidate_domain in generic_hosts:
            candidate_domain = None

        norm_name = normalize_business_name(raw_name)
        candidate_city = (raw_city or "").strip().lower()
        norm_nc = (norm_name, candidate_city) if norm_name else None

        if not is_dupe:
            if candidate_domain and candidate_domain in seen_batch_urls:
                is_dupe = True
                dupe_reason = f"Duplicate within CSV batch (identical website domain: {candidate_domain})"
            elif norm_nc and norm_nc in seen_batch_names:
                is_dupe = True
                dupe_reason = f"Duplicate within CSV batch (identical business name & city: {raw_name})"

        if candidate_domain:
            seen_batch_urls.add(candidate_domain)
        if norm_nc:
            seen_batch_names.add(norm_nc)

        if is_dupe:
            duplicate_count += 1

        preview_records.append(
            CsvPreviewRecord(
                row_number=idx,
                name=raw_name,
                category=raw_category or "Commercial Services",
                city=raw_city or "Mumbai",
                state=raw_state or "Maharashtra",
                country=raw_country or "India",
                website_url=canonical_website,
                website_status=condition,
                phone=raw_phone,
                email=raw_email,
                opportunity_score=opp_score,
                is_duplicate=is_dupe,
                duplicate_reason=dupe_reason,
                existing_id=dupe_existing_id
            )
        )

    return CsvImportPreviewResponse(
        headers=headers,
        column_mapping=mapping,
        total_rows=len(rows),
        valid_count=len(preview_records),
        duplicate_count=duplicate_count,
        invalid_count=len(invalid_records),
        preview_records=preview_records,
        invalid_records=invalid_records
    )

def commit_csv_import(
    db: Session,
    records: List[Dict[str, Any]],
    skip_duplicates: bool = True
) -> CsvImportSummaryResponse:
    """
    Saves validated CSV records into the existing SQLite prospects table.
    Ensures safe, atomic database insertion and intra-batch duplicate prevention.
    """
    imported_ids: List[str] = []
    skipped_count = 0
    seen_batch_urls = set()
    seen_batch_names = set()
    generic_hosts = {"gmail.com", "yahoo.com", "outlook.com", "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com"}

    for rec in records:
        name = rec.get("name", "").strip()
        if not name:
            continue

        website_url = normalize_website_url(rec.get("website_url") or rec.get("websiteUrl"))
        city = rec.get("city") or "Mumbai"
        state = rec.get("state") or "Maharashtra"
        country = rec.get("country") or "India"

        # Check intra-batch duplication
        candidate_domain = extract_registered_domain(website_url)
        if candidate_domain in generic_hosts:
            candidate_domain = None

        norm_name = normalize_business_name(name)
        candidate_city = (city or "").strip().lower()
        norm_nc = (norm_name, candidate_city) if norm_name else None

        if skip_duplicates:
            if candidate_domain and candidate_domain in seen_batch_urls:
                skipped_count += 1
                continue
            if norm_nc and norm_nc in seen_batch_names:
                skipped_count += 1
                continue

        # Check for duplicate in database
        dupe = check_single_duplicate(
            db=db,
            name=name,
            website_url=website_url,
            city=city,
            state=state,
            country=country,
            source_provider="csv_import"
        )

        if dupe and skip_duplicates:
            skipped_count += 1
            continue

        if candidate_domain:
            seen_batch_urls.add(candidate_domain)
        if norm_nc:
            seen_batch_names.add(norm_nc)

        new_id = f"pros_{uuid.uuid4().hex[:8]}"
        opp_score = int(rec.get("opportunity_score") or rec.get("opportunityScore") or 70)
        condition = rec.get("website_status") or rec.get("websiteStatus") or classify_website_status(bool(website_url))

        total_score, urgency, intent, ease = calculate_discovery_score(
            condition,
            rec.get("category", "Commercial Services"),
            bool(rec.get("phone")),
            bool(rec.get("email"))
        )

        prospect = ProspectModel(
            id=new_id,
            name=name,
            category=rec.get("category", "Commercial Services"),
            city=city,
            state=state,
            country=country,
            website_url=website_url,
            website_status=condition,
            opportunity_score=opp_score or total_score,
            score_urgency=urgency,
            score_intent=intent,
            score_ease=ease,
            status="new",
            last_activity="Imported via CSV",
            phone=rec.get("phone"),
            email=rec.get("email"),
            audit_count=0,
            latest_audit_id=None,
            tags=json.dumps(["CSV Import", rec.get("category", "Commercial Services")]),
            recommended_action="Execute initial website audit." if website_url else "Verify contact details.",
            notes=rec.get("notes") or "Imported from CSV batch.",
            source_provider="csv_import",
            source_record_id=f"row_{len(imported_ids) + 1}",
            source_url=None,
            discovered_at=datetime.now(timezone.utc),
            last_verified_at=None
        )

        db.add(prospect)
        imported_ids.append(new_id)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return CsvImportSummaryResponse(
        imported_count=len(imported_ids),
        skipped_duplicates_count=skipped_count,
        total_processed=len(records),
        created_prospect_ids=imported_ids
    )
