"""
Machine Learning Preprocessing Pipeline
Handles feature extraction, data leakage prevention, ethical attribute filtering,
and imputation for the Random Forest hiring prediction model.
"""
import logging
from typing import Tuple, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Features used for model training and inference
# NOTE: Demographic/protected personal attributes (e.g., 'Gender') are EXCLUDED
# to uphold ethical AI hiring guidelines and avoid algorithmic bias.
# Target 'HiringDecision' is excluded from features to prevent data leakage.
FEATURE_COLUMNS = [
    "EducationLevel",
    "ExperienceYears",
    "PreviousCompanies",
    "DistanceFromCompany",
    "InterviewScore",
    "SkillScore",
    "PersonalityScore",
    "RecruitmentStrategy"
]

TARGET_COLUMN = "HiringDecision"


def clean_and_prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column names and data types from various sources (CSV or MongoDB).
    """
    cleaned = df.copy()

    # Column name mappings between MongoDB doc format and CSV format
    col_map = {
        "education_level": "EducationLevel",
        "experience_years": "ExperienceYears",
        "previous_companies": "PreviousCompanies",
        "distance_from_company": "DistanceFromCompany",
        "interview_score": "InterviewScore",
        "skill_score": "SkillScore",
        "personality_score": "PersonalityScore",
        "recruitment_strategy": "RecruitmentStrategy",
        "hiring_decision": "HiringDecision"
    }
    cleaned = cleaned.rename(columns=col_map)

    # If target is missing but 'status' exists, map status to target
    if TARGET_COLUMN not in cleaned.columns and "status" in cleaned.columns:
        status_map = {"Selected": 1, "Rejected": 0}
        cleaned[TARGET_COLUMN] = cleaned["status"].map(status_map)

    # Strictly exclude records with unknown or Pending outcomes from training
    if TARGET_COLUMN in cleaned.columns:
        cleaned = cleaned[cleaned[TARGET_COLUMN].isin([0, 1])].copy()
        cleaned[TARGET_COLUMN] = cleaned[TARGET_COLUMN].astype(int)

    # Impute missing values if any
    for col in FEATURE_COLUMNS:
        if col in cleaned.columns:
            if cleaned[col].isnull().any():
                median_val = cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(median_val)
        else:
            cleaned[col] = 0

    return cleaned


def extract_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts feature matrix X and target vector y.
    Guarantees no data leakage by explicitly validating columns.
    """
    prepared_df = clean_and_prepare_dataframe(df)

    if TARGET_COLUMN not in prepared_df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset.")

    if len(prepared_df) == 0:
        raise ValueError("No labelled records available for training (all records are Pending or missing).")

    X = prepared_df[FEATURE_COLUMNS].copy()
    y = prepared_df[TARGET_COLUMN].copy()

    # Data leakage assertion
    assert TARGET_COLUMN not in X.columns, "Data leakage detected: Target column found in feature matrix!"
    assert "status" not in X.columns, "Data leakage detected: Status field found in feature matrix!"
    assert "Gender" not in X.columns, "Ethical violation: Gender found in feature matrix!"

    return X, y


def format_candidate_for_prediction(data: dict) -> pd.DataFrame:
    """
    Formats a single candidate input dictionary into a one-row DataFrame
    matching FEATURE_COLUMNS.
    """
    row = {
        "EducationLevel": int(data.get("EducationLevel") or data.get("education_level", 2)),
        "ExperienceYears": float(data.get("ExperienceYears") or data.get("experience_years", 0.0)),
        "PreviousCompanies": int(data.get("PreviousCompanies") or data.get("previous_companies", 0)),
        "DistanceFromCompany": float(data.get("DistanceFromCompany") or data.get("distance_from_company", 10.0)),
        "InterviewScore": float(data.get("InterviewScore") or data.get("interview_score", 50.0)),
        "SkillScore": float(data.get("SkillScore") or data.get("skill_score", 50.0)),
        "PersonalityScore": float(data.get("PersonalityScore") or data.get("personality_score", 50.0)),
        "RecruitmentStrategy": int(data.get("RecruitmentStrategy") or data.get("recruitment_strategy", 2))
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
