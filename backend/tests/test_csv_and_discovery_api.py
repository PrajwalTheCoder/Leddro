import pytest
from unittest.mock import patch, MagicMock

from backend.app.models.prospect import ProspectModel
from backend.app.discovery.providers.csv_import import (
    parse_csv_stream,
    auto_detect_column_mapping,
    preview_csv_import,
    commit_csv_import
)
from backend.app.discovery.deduplication import check_single_duplicate

def test_csv_parser_quoted_fields_and_commas():
    raw_csv = """Business Name,Category,City,State,Website URL,Opportunity Score
"Aura Spatial, Consultants",Architecture,"Navi Mumbai, West",Maharashtra,https://auraspatial.in,85
"Zenith Crafts, & Toolings",Manufacturing,Pune,Maharashtra,,90"""

    headers, rows = parse_csv_stream(raw_csv)
    assert headers == ["Business Name", "Category", "City", "State", "Website URL", "Opportunity Score"]
    assert len(rows) == 2
    assert rows[0]["Business Name"] == "Aura Spatial, Consultants"
    assert rows[0]["City"] == "Navi Mumbai, West"
    assert rows[1]["Business Name"] == "Zenith Crafts, & Toolings"
    assert rows[1]["Website URL"] == ""

def test_csv_unicode_support():
    raw_csv = """Business Name,Category,City,State,Country
नमः इंटीरियर्स,Interior Design,नई दिल्ली,Delhi,India
Atelier d'Architecture & Lumière,Design,Paris,Île-de-France,France
München Präzision,Manufacturing,München,Bayern,Germany"""

    headers, rows = parse_csv_stream(raw_csv)
    assert len(rows) == 3
    assert rows[0]["Business Name"] == "नमः इंटीरियर्स"
    assert rows[1]["Business Name"] == "Atelier d'Architecture & Lumière"
    assert rows[2]["Business Name"] == "München Präzision"

def test_csv_formula_injection_defense():
    raw_csv = """Business Name,Category,City,State,Website URL
=cmd|' /C calc'!A0,Consulting,Mumbai,Maharashtra,https://bad.in
+SUM(1,2),Consulting,Mumbai,Maharashtra,https://math.in
-2+5,Consulting,Mumbai,Maharashtra,https://neg.in
@HYPERLINK("http://evil.com"),Phishing,Mumbai,Maharashtra,https://evil.in"""

    headers, rows = parse_csv_stream(raw_csv)
    assert len(rows) == 4
    # All dangerous initial characters must be prepended with a quote to prevent DDE execution
    for row in rows:
        name = row["Business Name"]
        assert name.startswith("'")

def test_csv_import_preview_api_does_not_persist(client, db_session):
    initial_count = db_session.query(ProspectModel).count()

    csv_data = """Business Name,Category,City,State,Website URL,Opportunity Score
Transient Enterprise 1,Logistics,Panvel,Maharashtra,https://transient1.in,80
Transient Enterprise 2,Logistics,Panvel,Maharashtra,https://transient2.in,85"""

    preview_res = client.post("/api/prospects/import/preview", json={"csvContent": csv_data})
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["total_rows"] == 2
    assert data["valid_count"] == 2
    assert len(data["preview_records"]) == 2

    # Verify preview did NOT write records to database
    post_count = db_session.query(ProspectModel).count()
    assert post_count == initial_count

def test_csv_import_confirm_persists_records(client, db_session):
    records = [
        {
            "name": "Committed Metalworks",
            "category": "Industrial Manufacturing",
            "city": "Thane",
            "state": "Maharashtra",
            "country": "India",
            "website_url": "https://committedmetal.in",
            "phone": "+91 22 2534 8899",
            "email": "contact@committedmetal.in",
            "opportunity_score": 88
        }
    ]

    confirm_res = client.post("/api/prospects/import/confirm", json={"records": records})
    assert confirm_res.status_code == 200
    summary = confirm_res.json()
    assert summary["imported_count"] == 1
    assert summary["skipped_duplicates_count"] == 0

    # Verify present in database
    saved = db_session.query(ProspectModel).filter(ProspectModel.name == "Committed Metalworks").first()
    assert saved is not None
    assert saved.source_provider == "csv_import"
    assert saved.city == "Thane"
    assert saved.website_status == "verification_required"

def test_csv_duplicate_detection(client, db_session):
    # 1. Create initial prospect
    client.post("/api/prospects", json={
        "name": "Dupe Anchor Corp",
        "category": "Technology",
        "location": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
        "websiteUrl": "https://dupeanchor.com"
    })

    # 2. Preview CSV containing identical domain and identical name
    csv_data = """Business Name,Category,City,State,Website URL
Dupe Anchor Corp,Technology,Mumbai,Maharashtra,https://dupeanchor.com
Another Name Same Domain,Tech,Pune,Maharashtra,https://dupeanchor.com
Different Corp,Services,Mumbai,Maharashtra,https://diffcorp.com"""

    preview_res = client.post("/api/prospects/import/preview", json={"csvContent": csv_data})
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["duplicate_count"] == 2
    assert data["valid_count"] == 3

    p0 = data["preview_records"][0]
    assert p0["is_duplicate"] is True
    assert "Dupe Anchor Corp" in p0["duplicate_reason"]

    p1 = data["preview_records"][1]
    assert p1["is_duplicate"] is True
    assert "domain" in p1["duplicate_reason"].lower()

    p2 = data["preview_records"][2]
    assert p2["is_duplicate"] is False

def test_discovery_providers_endpoint(client):
    res = client.get("/api/discovery/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 2
    osm = next((p for p in providers if p["provider_id"] == "osm"), None)
    assert osm is not None
    assert osm["is_configured"] is True
    assert "OpenStreetMap" in osm["attribution"]

    gp = next((p for p in providers if p["provider_id"] == "google_places"), None)
    assert gp is not None
    assert gp["requires_api_key"] is True

def test_discovery_categories_endpoint(client):
    res = client.get("/api/discovery/categories")
    assert res.status_code == 200
    data = res.json()
    assert data["total_supported"] > 10
    assert any(c["category"] == "restaurant" for c in data["categories"])
    assert any(c["category"] == "interior design" for c in data["categories"])
    assert "unmapped_guidance" in data

def test_discovery_search_and_save_workflow(client, db_session):
    mock_osm_data = [
        {
            "place_id": 8888,
            "osm_type": "node",
            "osm_id": 8888,
            "lat": "19.011",
            "lon": "73.011",
            "name": "Live Search Cafe",
            "display_name": "Live Search Cafe, Sector 15, Navi Mumbai, Maharashtra, 400703, India",
            "address": {
                "amenity": "Live Search Cafe",
                "road": "Sector 15",
                "city": "Navi Mumbai",
                "state": "Maharashtra",
                "country": "India"
            },
            "extratags": {
                "website": "https://livesearchcafe.in",
                "phone": "+91 22 2788 1234"
            }
        }
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_osm_data

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        search_res = client.post("/api/discovery/search", json={
            "provider": "osm",
            "category": "cafe",
            "city": "Navi Mumbai",
            "limit": 10
        })
        assert search_res.status_code == 200
        run_record = search_res.json()
        assert run_record["status"] == "COMPLETED"
        assert run_record["results_count"] == 1

        discovered_item = run_record["results"][0]
        assert discovered_item["name"] == "Live Search Cafe"
        assert discovered_item["is_saved"] is False

        # Save this item to prospects via /api/discovery/save
        save_res = client.post("/api/discovery/save", json=discovered_item)
        assert save_res.status_code == 201
        saved_prospect = save_res.json()
        assert saved_prospect["name"] == "Live Search Cafe"
        assert saved_prospect["websiteUrl"] == "https://livesearchcafe.in"
        assert saved_prospect["sourceProvider"] == "osm"

        # Verify saved in SQLite database
        in_db = db_session.query(ProspectModel).filter(ProspectModel.name == "Live Search Cafe").first()
        assert in_db is not None
        assert in_db.source_record_id == "node/8888"

        # Re-executing search should now mark this item as duplicate / already saved
        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            search_res_2 = client.post("/api/discovery/search", json={
                "provider": "osm",
                "category": "cafe",
                "city": "Navi Mumbai",
                "limit": 10
            })
            run_2 = search_res_2.json()
            assert run_2["results"][0]["is_saved"] is True
            assert run_2["results"][0]["matched_existing_id"] == in_db.id

def test_deduplication_matching_semantics_and_edge_cases(db_session):
    """
    Regression test for Finding 3:
    Verifies that the optimized deduplication queries preserve 100% of matching semantics:
    - Provider record ID
    - Registered domain normalization
    - Generic host avoidance
    - Business name normalization (suffix removal, whitespace, punctuation)
    - Locality separation (different cities not merged)
    - Blank city edge-case matching
    """
    # 1. Seed base prospects
    p1 = ProspectModel(
        id="pros_seed_1",
        name="Apex Industrial Logistics Ltd.",
        city="Atlanta",
        state="Georgia",
        country="USA",
        website_url="https://www.apex-logistics.com/about",
        source_provider="osm",
        source_record_id="node/1001",
        opportunity_score=75
    )
    p2 = ProspectModel(
        id="pros_seed_2",
        name="Generic Freelancer",
        city="Seattle",
        website_url="https://gmail.com",
        opportunity_score=50
    )
    p3 = ProspectModel(
        id="pros_seed_3",
        name="Omni National Corp",
        city="",
        opportunity_score=60
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Case A: Provider ID match
    match_prov = check_single_duplicate(
        db=db_session,
        name="Completely Different Name",
        source_provider="osm",
        source_record_id="node/1001"
    )
    assert match_prov is not None
    assert match_prov.match_type == "record_id"
    assert match_prov.existing_id == "pros_seed_1"

    # Case B: Registered domain match (with different scheme & www)
    match_domain = check_single_duplicate(
        db=db_session,
        name="Apex Log",
        website_url="http://apex-logistics.com/contact-us"
    )
    assert match_domain is not None
    assert match_domain.match_type == "domain"
    assert match_domain.existing_id == "pros_seed_1"

    # Case C: Generic domain avoidance (gmail.com should NOT trigger domain match)
    match_generic = check_single_duplicate(
        db=db_session,
        name="Another Freelancer",
        website_url="https://gmail.com"
    )
    assert match_generic is None

    # Case D: Business name match with same city (suffix stripping: Inc. vs Ltd.)
    match_name_city = check_single_duplicate(
        db=db_session,
        name="Apex Industrial Logistics Inc.",
        city="Atlanta"
    )
    assert match_name_city is not None
    assert match_name_city.match_type == "name_location"
    assert match_name_city.existing_id == "pros_seed_1"

    # Case E: Business name match with DIFFERENT city (must NOT merge branches)
    match_diff_city = check_single_duplicate(
        db=db_session,
        name="Apex Industrial Logistics Inc.",
        city="Chicago"
    )
    assert match_diff_city is None

    # Case F: Both cities blank matches
    match_blank_cities = check_single_duplicate(
        db=db_session,
        name="Omni National LLC",
        city=""
    )
    assert match_blank_cities is not None
    assert match_blank_cities.match_type == "name_location"
    assert match_blank_cities.existing_id == "pros_seed_3"

    # Case G: Candidate city provided but database city blank does NOT match
    match_city_blank_db = check_single_duplicate(
        db=db_session,
        name="Omni National LLC",
        city="Denver"
    )
    assert match_city_blank_db is None

def test_deduplication_performance_benchmark(db_session):
    """
    Performance benchmark for Finding 3:
    Seeds 500 prospects in SQLite and runs 50 duplicate checks
    (20 expected duplicates, 30 unique).
    Measures duration and asserts 100% accuracy and high throughput.
    """
    import time

    # Seed 500 prospects
    bulk_prospects = []
    for i in range(500):
        bulk_prospects.append(
            ProspectModel(
                id=f"pros_perf_{i}",
                name=f"Enterprise Solutions {i} Inc",
                city=f"City_{i % 20}",
                state="State",
                country="Country",
                website_url=f"https://www.enterprise-solutions-{i}.io",
                source_provider="bulk_seed",
                source_record_id=f"seed_{i}",
                opportunity_score=60
            )
        )
    db_session.bulk_save_objects(bulk_prospects)
    db_session.commit()

    # Prepare 50 candidates: 20 duplicates, 30 non-duplicates
    candidates = []
    for i in range(20):
        # 10 duplicate by domain, 10 duplicate by name + city
        if i < 10:
            candidates.append({
                "name": f"Alt Name {i}",
                "website_url": f"http://enterprise-solutions-{i}.io/contact",
                "city": "Unknown",
                "expected_dupe": True,
                "expected_id": f"pros_perf_{i}"
            })
        else:
            candidates.append({
                "name": f"Enterprise Solutions {i} LLC",
                "website_url": "https://different-domain.org",
                "city": f"City_{i % 20}",
                "expected_dupe": True,
                "expected_id": f"pros_perf_{i}"
            })

    for i in range(30):
        candidates.append({
            "name": f"Completely Unique Company {i} Corp",
            "website_url": f"https://unique-firm-{i}.com",
            "city": f"NewCity_{i}",
            "expected_dupe": False,
            "expected_id": None
        })

    # Benchmark execution time
    start_time = time.perf_counter()
    dupe_count = 0
    for cand in candidates:
        match = check_single_duplicate(
            db=db_session,
            name=cand["name"],
            website_url=cand["website_url"],
            city=cand["city"]
        )
        if cand["expected_dupe"]:
            assert match is not None, f"Failed to detect duplicate for {cand['name']}"
            assert match.existing_id == cand["expected_id"]
            dupe_count += 1
        else:
            assert match is None, f"False duplicate detected for {cand['name']}"

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    ops_per_sec = len(candidates) / (elapsed_ms / 1000)

    assert dupe_count == 20
    # On modern CPU, 50 queries with indexed/targeted LIKE should execute in under 500ms
    assert elapsed_ms < 1000, f"Deduplication benchmark took too long: {elapsed_ms:.2f}ms"
    print(f"\n[DEDUPLICATION BENCHMARK] 50 candidates against 500 DB prospects took {elapsed_ms:.2f}ms ({ops_per_sec:.1f} checks/sec). 100% accuracy verified.")
