import pytest

def test_list_empty_prospects(client):
    response = client.get("/api/prospects")
    assert response.status_code == 200
    assert response.json() == []

def test_create_and_get_prospect(client):
    payload = {
        "name": "Zenith Metalworks",
        "category": "Industrial Manufacturing",
        "location": {
            "city": "Coimbatore",
            "state": "Tamil Nadu",
            "country": "India"
        },
        "websiteUrl": "https://zenithmetalworks.in",
        "websiteStatus": "active",
        "opportunityScore": 85,
        "scoreBreakdown": {
            "technicalUrgency": 35,
            "commercialIntent": 30,
            "resolutionEase": 20
        },
        "status": "new",
        "phone": "+91 422 9876543",
        "email": "contact@zenithmetalworks.in",
        "tags": ["Sheet Metal", "Export Ready"],
        "recommendedAction": "Conduct website audit.",
        "notes": "CNC manufacturer in Coimbatore."
    }

    create_res = client.post("/api/prospects", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"].startswith("pros_")
    assert created_data["name"] == "Zenith Metalworks"
    assert created_data["location"]["city"] == "Coimbatore"
    assert created_data["opportunityScore"] == 85
    assert created_data["tags"] == ["Sheet Metal", "Export Ready"]

    # Retrieve by ID
    get_res = client.get(f"/api/prospects/{created_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Zenith Metalworks"

def test_duplicate_prospect_rejection(client):
    payload = {
        "name": "Dupe Test Corp",
        "category": "Services",
        "websiteUrl": "https://dupetest.com",
        "opportunityScore": 75
    }

    # First creation should succeed
    res1 = client.post("/api/prospects", json=payload)
    assert res1.status_code == 201

    # Second creation with same name should fail with 409 Conflict
    res2 = client.post("/api/prospects", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()

    # Third creation with different name but identical website URL should also fail with 409 Conflict
    payload_diff_name = {
        "name": "Another Name Same URL",
        "category": "Services",
        "websiteUrl": "https://dupetest.com",
        "opportunityScore": 75
    }
    res3 = client.post("/api/prospects", json=payload_diff_name)
    assert res3.status_code == 409
    assert "already exists" in res3.json()["detail"].lower()

def test_update_prospect(client):
    # Create prospect
    res = client.post("/api/prospects", json={"name": "Update Target", "opportunityScore": 60})
    p_id = res.json()["id"]

    # Patch fields
    patch_res = client.patch(f"/api/prospects/{p_id}", json={
        "opportunityScore": 95,
        "status": "approved",
        "notes": "Verified critical security finding."
    })
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["opportunityScore"] == 95
    assert updated["status"] == "approved"
    assert updated["notes"] == "Verified critical security finding."

def test_delete_prospect(client):
    res = client.post("/api/prospects", json={"name": "Delete Target", "opportunityScore": 50})
    p_id = res.json()["id"]

    del_res = client.delete(f"/api/prospects/{p_id}")
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/api/prospects/{p_id}")
    assert get_res.status_code == 404
