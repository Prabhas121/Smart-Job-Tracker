"""
Candidate Operations & Validation Tests
Tests:
- Individual candidate insertion via insert_one()
- Field validation and constraints
- Outcome status updates via update_one()
"""
import pytest
from database.validators import validate_and_sanitize_candidate


def test_candidate_validation_success():
    """Verify valid candidate dictionary parses properly."""
    raw = {
        "candidate_name": "Aarav Gupta",
        "Age": 29,
        "Gender": 0,
        "EducationLevel": 2,
        "ExperienceYears": 4.5,
        "PreviousCompanies": 2,
        "DistanceFromCompany": 14.2,
        "InterviewScore": 82,
        "SkillScore": 88,
        "PersonalityScore": 76,
        "RecruitmentStrategy": 1,
        "status": "Pending"
    }
    cleaned, err = validate_and_sanitize_candidate(raw, source="manual_entry")
    assert err is None
    assert cleaned is not None
    assert cleaned["candidate_name"] == "Aarav Gupta"
    assert cleaned["status"] == "Pending"
    assert cleaned["hiring_decision"] is None
    assert cleaned["source"] == "manual_entry"


def test_candidate_validation_invalid_scores():
    """Verify out-of-bound scores are rejected."""
    raw = {
        "candidate_name": "Invalid Candidate",
        "Age": 25,
        "EducationLevel": 2,
        "ExperienceYears": 2,
        "PreviousCompanies": 1,
        "DistanceFromCompany": 5,
        "InterviewScore": 150,  # Invalid: > 100
        "SkillScore": 80,
        "PersonalityScore": 70,
        "RecruitmentStrategy": 2
    }
    cleaned, err = validate_and_sanitize_candidate(raw)
    assert cleaned is None
    assert "InterviewScore must be between 0 and 100" in err


def test_candidate_insert_one_and_find(clean_test_db):
    """Test individual candidate insertion into MongoDB using insert_one()."""
    col = clean_test_db["candidates"]

    candidate_doc = {
        "candidate_id": "CAND-TEST-01",
        "candidate_name": "Test Applicant",
        "education_level": 3,
        "experience_years": 5.0,
        "interview_score": 85.0,
        "skill_score": 90.0,
        "personality_score": 80.0,
        "recruitment_strategy": 1,
        "status": "Pending",
        "hiring_decision": None,
        "source": "manual_entry",
        "fingerprint": "test_fp_01"
    }

    res = col.insert_one(candidate_doc)
    assert res.inserted_id is not None

    found = col.find_one({"candidate_id": "CAND-TEST-01"})
    assert found is not None
    assert found["candidate_name"] == "Test Applicant"
    assert found["status"] == "Pending"


def test_candidate_update_one_status(clean_test_db):
    """Test updating candidate outcome from Pending to Selected via update_one()."""
    col = clean_test_db["candidates"]

    candidate_doc = {
        "candidate_id": "CAND-TEST-02",
        "candidate_name": "Pending Candidate",
        "status": "Pending",
        "hiring_decision": None,
        "source": "manual_entry",
        "fingerprint": "test_fp_02"
    }
    col.insert_one(candidate_doc)

    # Perform update_one()
    update_res = col.update_one(
        {"candidate_id": "CAND-TEST-02"},
        {"$set": {"status": "Selected", "hiring_decision": 1}}
    )
    assert update_res.matched_count == 1
    assert update_res.modified_count == 1

    # Verify updated state
    updated = col.find_one({"candidate_id": "CAND-TEST-02"})
    assert updated["status"] == "Selected"
    assert updated["hiring_decision"] == 1
