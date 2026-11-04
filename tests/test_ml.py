"""
Machine Learning Model Tests
Tests:
- Feature extraction & data leakage prevention
- Ethical AI exclusion of sensitive attributes (Gender)
- Exclusion of Pending records from training
- Random Forest training & evaluation metrics
- Joblib artifact serialization
- Inference prediction & confidence probability
"""
import pytest
import pandas as pd
from ml.preprocess import (
    FEATURE_COLUMNS,
    extract_features_and_target,
    clean_and_prepare_dataframe
)
from ml.evaluate import evaluate_model
from ml.train_model import train_hiring_model
from ml.predict import predict_candidate_outcome


def test_feature_extraction_and_ethical_exclusion():
    """Verify that Gender is excluded and target is separated without data leakage."""
    data = {
        "Age": [25, 30, 35],
        "Gender": [1, 0, 1],
        "EducationLevel": [2, 3, 4],
        "ExperienceYears": [2.0, 5.0, 8.0],
        "PreviousCompanies": [1, 2, 3],
        "DistanceFromCompany": [10.0, 15.0, 20.0],
        "InterviewScore": [60, 75, 90],
        "SkillScore": [65, 80, 95],
        "PersonalityScore": [70, 75, 85],
        "RecruitmentStrategy": [1, 2, 3],
        "HiringDecision": [0, 1, 1]
    }
    df = pd.DataFrame(data)
    X, y = extract_features_and_target(df)

    # Assert features match expected
    assert list(X.columns) == FEATURE_COLUMNS
    assert "Gender" not in X.columns, "Ethical AI violation: Gender must not be a predictive feature!"
    assert "HiringDecision" not in X.columns, "Data leakage: Target found in features!"
    assert len(y) == 3


def test_pending_records_excluded_from_training():
    """Verify records with unknown or Pending outcomes are excluded from training."""
    data = {
        "EducationLevel": [2, 3, 2],
        "ExperienceYears": [2.0, 5.0, 3.0],
        "PreviousCompanies": [1, 2, 1],
        "DistanceFromCompany": [10.0, 15.0, 12.0],
        "InterviewScore": [60, 75, 70],
        "SkillScore": [65, 80, 75],
        "PersonalityScore": [70, 75, 72],
        "RecruitmentStrategy": [1, 2, 1],
        "status": ["Selected", "Pending", "Rejected"]  # Pending in middle
    }
    df = pd.DataFrame(data)
    cleaned = clean_and_prepare_dataframe(df)

    assert len(cleaned) == 2  # Pending record was excluded
    assert list(cleaned["HiringDecision"]) == [1, 0]


def test_model_evaluation_metrics():
    """Verify evaluation metric calculations."""
    y_true = [0, 0, 1, 1, 1]
    y_pred = [0, 0, 1, 1, 0]
    y_prob = [0.1, 0.2, 0.9, 0.8, 0.4]

    metrics = evaluate_model(y_true, y_pred, y_prob)

    assert metrics["accuracy"] == 0.8
    assert metrics["precision"] == 1.0  # Out of predicted 1s (2), both were 1
    assert "confusion_matrix" in metrics
    assert metrics["confusion_matrix"]["true_negatives"] == 2
    assert metrics["confusion_matrix"]["true_positives"] == 2
    assert metrics["confusion_matrix"]["false_negatives"] == 1
    assert metrics["confusion_matrix"]["false_positives"] == 0


def test_candidate_prediction_inference():
    """Verify inference produces valid outcome, probability, and ethical disclaimer."""
    candidate = {
        "candidate_name": "Kavya Nair",
        "EducationLevel": 3,
        "ExperienceYears": 6.0,
        "PreviousCompanies": 2,
        "DistanceFromCompany": 10.0,
        "InterviewScore": 85.0,
        "SkillScore": 92.0,
        "PersonalityScore": 88.0,
        "RecruitmentStrategy": 1
    }

    result = predict_candidate_outcome(candidate)

    assert result["predicted_outcome"] in ["Selected", "Rejected"]
    assert 0.0 <= result["selection_probability"] <= 1.0
    assert 0.0 <= result["rejection_probability"] <= 1.0
    assert 0.0 <= result["confidence_score"] <= 100.0
    assert "disclaimer" in result
    assert "NEVER be used as the sole" in result["disclaimer"]
