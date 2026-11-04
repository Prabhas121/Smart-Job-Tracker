"""
MongoDB Aggregation Pipelines Tests
Tests:
- Pipeline 1: Candidate outcome distribution analysis
- Pipeline 2: Recruitment strategy efficiency
- Pipeline 3: Experience tier recruitment conversion
Verifies $match, $group, $project, $sort execution on MongoDB.
"""
from aggregations.pipelines import (
    get_candidate_outcome_pipeline,
    get_recruitment_strategy_pipeline,
    get_experience_tier_pipeline,
    run_pipeline
)


def populate_test_candidates(collection):
    """Inserts sample candidates with known values into collection."""
    sample_records = [
        # Strategy 1 (Aggressive)
        {"candidate_id": "C-1", "status": "Selected", "recruitment_strategy": 1, "strategy_label": "Aggressive", "interview_score": 80.0, "skill_score": 85.0, "personality_score": 75.0, "experience_years": 4.0, "distance_from_company": 10.0},
        {"candidate_id": "C-2", "status": "Selected", "recruitment_strategy": 1, "strategy_label": "Aggressive", "interview_score": 90.0, "skill_score": 95.0, "personality_score": 85.0, "experience_years": 8.0, "distance_from_company": 15.0},
        {"candidate_id": "C-3", "status": "Rejected", "recruitment_strategy": 1, "strategy_label": "Aggressive", "interview_score": 40.0, "skill_score": 45.0, "personality_score": 50.0, "experience_years": 1.0, "distance_from_company": 20.0},
        # Strategy 2 (Moderate)
        {"candidate_id": "C-4", "status": "Selected", "recruitment_strategy": 2, "strategy_label": "Moderate", "interview_score": 75.0, "skill_score": 70.0, "personality_score": 70.0, "experience_years": 2.0, "distance_from_company": 5.0},
        {"candidate_id": "C-5", "status": "Rejected", "recruitment_strategy": 2, "strategy_label": "Moderate", "interview_score": 50.0, "skill_score": 55.0, "personality_score": 60.0, "experience_years": 3.0, "distance_from_company": 12.0},
        {"candidate_id": "C-6", "status": "Rejected", "recruitment_strategy": 2, "strategy_label": "Moderate", "interview_score": 45.0, "skill_score": 50.0, "personality_score": 40.0, "experience_years": 11.0, "distance_from_company": 25.0},
        # Pending
        {"candidate_id": "C-7", "status": "Pending", "recruitment_strategy": 2, "strategy_label": "Moderate", "interview_score": 65.0, "skill_score": 65.0, "personality_score": 65.0, "experience_years": 6.0, "distance_from_company": 8.0}
    ]
    collection.insert_many(sample_records, ordered=False)


def test_pipeline_1_candidate_outcomes(clean_test_db):
    """Test Aggregation Pipeline 1 groups outcomes properly."""
    col = clean_test_db["candidates"]
    populate_test_candidates(col)

    pipeline = get_candidate_outcome_pipeline()
    results = run_pipeline(col, pipeline)

    assert len(results) == 3  # Selected, Rejected, Pending
    result_map = {r["status"]: r for r in results}

    assert result_map["Selected"]["count"] == 3
    assert result_map["Rejected"]["count"] == 3
    assert result_map["Pending"]["count"] == 1

    # Average interview score for Selected: (80 + 90 + 75) / 3 = 81.666... -> rounded to 81.7
    assert result_map["Selected"]["avg_interview_score"] == 81.7


def test_pipeline_2_strategy_efficiency(clean_test_db):
    """Test Aggregation Pipeline 2 aggregates per recruitment strategy."""
    col = clean_test_db["candidates"]
    populate_test_candidates(col)

    pipeline = get_recruitment_strategy_pipeline()
    results = run_pipeline(col, pipeline)

    assert len(results) == 2  # Strategy 1 and Strategy 2
    strat_map = {r["strategy_id"]: r for r in results}

    # Strategy 1: 2 Selected, 1 Rejected -> Selection Rate = (2 / 3) * 100 = 66.7%
    assert strat_map[1]["total_candidates"] == 3
    assert strat_map[1]["selected_count"] == 2
    assert strat_map[1]["rejected_count"] == 1
    assert strat_map[1]["selection_rate"] == 66.7

    # Strategy 2: 1 Selected, 2 Rejected, 1 Pending -> Decided = 3 -> Rate = (1 / 3) * 100 = 33.3%
    assert strat_map[2]["total_candidates"] == 4
    assert strat_map[2]["selected_count"] == 1
    assert strat_map[2]["rejected_count"] == 2
    assert strat_map[2]["pending_count"] == 1
    assert strat_map[2]["selection_rate"] == 33.3


def test_pipeline_3_experience_tiers(clean_test_db):
    """Test Aggregation Pipeline 3 categorizes experience bands."""
    col = clean_test_db["candidates"]
    populate_test_candidates(col)

    pipeline = get_experience_tier_pipeline()
    results = run_pipeline(col, pipeline)

    assert len(results) > 0
    tier_names = [r["tier"] for r in results]
    assert "Entry-Level (0-2 yrs)" in tier_names
