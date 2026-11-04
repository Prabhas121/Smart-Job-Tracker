"""
Database Connection & Safety Tests
Verifies MongoDB connectivity, index generation, and strict database isolation.
"""
import pytest
from database.connection import check_connection, get_db
from database.indexes import init_indexes
from database.validators import compute_record_fingerprint, validate_and_sanitize_candidate


def test_mongodb_connection():
    """Verify that MongoDB server responds to ping."""
    status = check_connection()
    assert status["status"] == "connected", f"MongoDB connection failed: {status}"
    assert "smartJobIntelligenceDB" in status["database"]


def test_database_isolation_safety():
    """Verify that attempting to connect to an unauthorized database raises ValueError."""
    with pytest.raises(ValueError, match="Security Exception"):
        get_db("smartJobTrackerDB")  # Unauthorized external database!

    with pytest.raises(ValueError, match="Security Exception"):
        get_db("random_unauthorized_db")


def test_index_initialization(clean_test_db):
    """Verify indexes are created on smartJobIntelligenceDB_test collections."""
    init_indexes(clean_test_db)
    cand_indexes = clean_test_db["candidates"].index_information()
    assert "idx_fingerprint_unique" in cand_indexes
    assert "idx_status" in cand_indexes
    assert "idx_created_at" in cand_indexes


def test_record_fingerprint_consistency():
    """Verify applicant fingerprint calculation is deterministic."""
    rec1 = {
        "age": 28, "gender": 0, "education_level": 2, "experience_years": 3.5,
        "previous_companies": 2, "distance_from_company": 12.0, "interview_score": 75,
        "skill_score": 82, "personality_score": 78, "recruitment_strategy": 2
    }
    rec2 = rec1.copy()
    fp1 = compute_record_fingerprint(rec1)
    fp2 = compute_record_fingerprint(rec2)
    assert fp1 == fp2
    assert len(fp1) == 16
