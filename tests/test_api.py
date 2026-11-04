"""
Flask REST API Endpoints Tests
Tests all backend routes and status codes.
"""
import json


def test_health_check_api(client):
    """Test /api/health endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data


def test_index_page(client):
    """Test GET / returns HTML dashboard."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"Smart Job Application Intelligence Dashboard" in res.data


def test_dashboard_summary_api(client):
    """Test /api/dashboard/summary endpoint."""
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "total_candidates" in data["data"]
    assert "selection_rate" in data["data"]


def test_add_candidate_api(client):
    """Test POST /api/candidates endpoint with insert_one()."""
    payload = {
        "candidate_name": "API Test Candidate",
        "Age": 28,
        "Gender": 0,
        "EducationLevel": 2,
        "ExperienceYears": 4.0,
        "PreviousCompanies": 2,
        "DistanceFromCompany": 10.0,
        "InterviewScore": 80.0,
        "SkillScore": 85.0,
        "PersonalityScore": 75.0,
        "RecruitmentStrategy": 2,
        "status": "Pending"
    }

    res = client.post("/api/candidates", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert "candidate" in data
    assert data["candidate"]["candidate_name"] == "API Test Candidate"
    assert data["candidate"]["status"] == "Pending"

    candidate_id = data["candidate"]["candidate_id"]

    # Test updating status via update_one()
    update_res = client.patch(
        f"/api/candidates/{candidate_id}/status",
        data=json.dumps({"status": "Selected"}),
        content_type="application/json"
    )
    assert update_res.status_code == 200
    update_data = update_res.get_json()
    assert update_data["success"] is True
    assert update_data["new_status"] == "Selected"


def test_prediction_api(client):
    """Test POST /api/prediction/predict endpoint."""
    payload = {
        "candidate_name": "Inference Candidate",
        "EducationLevel": 2,
        "ExperienceYears": 5.0,
        "PreviousCompanies": 2,
        "DistanceFromCompany": 8.0,
        "InterviewScore": 85.0,
        "SkillScore": 90.0,
        "PersonalityScore": 80.0,
        "RecruitmentStrategy": 1
    }

    res = client.post("/api/prediction/predict", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["data"]["predicted_outcome"] in ["Selected", "Rejected"]
    assert "confidence_score" in data["data"]
    assert "disclaimer" in data["data"]


def test_analytics_endpoints(client):
    """Test analytics aggregation endpoints."""
    res1 = client.get("/api/analytics/outcome-distribution")
    assert res1.status_code == 200
    assert res1.get_json()["success"] is True

    res2 = client.get("/api/analytics/strategy-efficiency")
    assert res2.status_code == 200
    assert res2.get_json()["success"] is True

    res3 = client.get("/api/analytics/experience-tiers")
    assert res3.status_code == 200
    assert res3.get_json()["success"] is True
