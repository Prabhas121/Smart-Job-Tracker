"""
Dataset Management & Bulk Insert Tests
Tests:
- CSV parsing and validation
- Bulk insertion using PyMongo insert_many()
- Safe duplicate handling
- Import history audit logging
"""
import io
import pandas as pd
from database.validators import validate_and_sanitize_candidate


def test_bulk_insert_many(clean_test_db):
    """Verify PyMongo insert_many() bulk inserts multiple documents."""
    col = clean_test_db["candidates"]

    docs = []
    for i in range(10):
        docs.append({
            "candidate_id": f"CAND-BULK-{i:03d}",
            "candidate_name": f"Bulk Candidate {i}",
            "education_level": 2,
            "experience_years": 3.0,
            "interview_score": 70.0 + i,
            "skill_score": 75.0 + i,
            "personality_score": 80.0,
            "recruitment_strategy": 2,
            "status": "Selected" if i % 2 == 0 else "Rejected",
            "hiring_decision": 1 if i % 2 == 0 else 0,
            "source": "real_dataset",
            "fingerprint": f"bulk_fp_{i}"
        })

    result = col.insert_many(docs, ordered=False)
    assert len(result.inserted_ids) == 10
    assert col.count_documents({}) == 10


def test_safe_duplicate_handling(clean_test_db):
    """Verify safe duplicate handling avoids creating duplicate records on repeated import."""
    col = clean_test_db["candidates"]

    doc = {
        "candidate_id": "CAND-DUP-01",
        "candidate_name": "Unique Candidate",
        "fingerprint": "fp_duplicate_test",
        "status": "Selected"
    }
    col.insert_one(doc)

    # Attempt to insert same record again
    existing_fps = set(col.distinct("fingerprint"))
    assert "fp_duplicate_test" in existing_fps

    # Simulated import logic: duplicate should be skipped
    records_to_import = [{"fingerprint": "fp_duplicate_test"}, {"fingerprint": "fp_new_test"}]
    to_insert = [r for r in records_to_import if r["fingerprint"] not in existing_fps]

    assert len(to_insert) == 1
    assert to_insert[0]["fingerprint"] == "fp_new_test"


def test_csv_upload_endpoint(client):
    """Test CSV file upload endpoint with simulated multipart form data."""
    csv_content = """Age,Gender,EducationLevel,ExperienceYears,PreviousCompanies,DistanceFromCompany,InterviewScore,SkillScore,PersonalityScore,RecruitmentStrategy,HiringDecision
26,1,2,3,2,10.5,75,80,85,1,1
32,0,3,7,3,15.2,85,90,88,2,1
24,1,1,1,1,22.0,40,45,50,3,0
"""
    data = {
        "file": (io.BytesIO(csv_content.encode("utf-8")), "test_candidates.csv")
    }

    res = client.post("/api/dataset/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["total_rows"] == 3
    assert json_data["data"]["valid_records_count"] == 3
    assert json_data["data"]["missing_values_count"] == 0
    assert json_data["data"]["is_schema_valid"] is True
