"""
Candidate Hiring Outcome Inference Module
Loads serialized Random Forest model from disk and produces prediction
with probability score, confidence level, and ethical advisory disclaimers.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import joblib
import pandas as pd

from config import Config
from ml.preprocess import FEATURE_COLUMNS, format_candidate_for_prediction
from ml.train_model import train_hiring_model

logger = logging.getLogger(__name__)

# Cached model instance
_cached_model = None
_cached_metadata = None


def load_model():
    """
    Loads the trained Joblib model and metadata.
    Auto-trains initial baseline model if no model artifact is present yet.
    """
    global _cached_model, _cached_metadata

    if _cached_model is not None and Config.MODEL_PATH.exists():
        return _cached_model, _cached_metadata

    if not Config.MODEL_PATH.exists():
        logger.info("No saved model found at %s. Triggering initial training...", Config.MODEL_PATH)
        train_hiring_model()

    _cached_model = joblib.load(Config.MODEL_PATH)

    if Config.MODEL_METADATA_PATH.exists():
        with open(Config.MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
            _cached_metadata = json.load(f)
    else:
        _cached_metadata = {}

    return _cached_model, _cached_metadata


def predict_candidate_outcome(candidate_data: dict) -> Dict[str, Any]:
    """
    Predicts the hiring outcome for a given candidate data dictionary.
    
    Returns:
    - predicted_outcome: "Selected" or "Rejected"
    - predicted_code: 1 or 0
    - selection_probability: float (0.0 to 1.0)
    - rejection_probability: float (0.0 to 1.0)
    - confidence_score: float percentage (e.g. 84.5)
    - model_version: str
    - key_factors: list of notable indicators
    - disclaimer: ethical disclaimer notice
    """
    model, metadata = load_model()

    # Format input into single-row DataFrame
    X_input = format_candidate_for_prediction(candidate_data)

    # Predict class
    prediction = int(model.predict(X_input)[0])

    # Predict probabilities
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_input)[0]
        # Class 0: Rejected, Class 1: Selected
        prob_rejected = float(probs[0])
        prob_selected = float(probs[1]) if len(probs) > 1 else 1.0 - prob_rejected
    else:
        prob_selected = 1.0 if prediction == 1 else 0.0
        prob_rejected = 1.0 - prob_selected

    confidence = round(max(prob_selected, prob_rejected) * 100, 1)
    outcome_label = "Selected" if prediction == 1 else "Rejected"

    # Identify key contributing assessment scores
    factors = []
    interview = float(candidate_data.get("InterviewScore") or candidate_data.get("interview_score", 50))
    skill = float(candidate_data.get("SkillScore") or candidate_data.get("skill_score", 50))
    personality = float(candidate_data.get("PersonalityScore") or candidate_data.get("personality_score", 50))
    exp = float(candidate_data.get("ExperienceYears") or candidate_data.get("experience_years", 0))

    if interview >= 70:
        factors.append("Strong interview evaluation performance (>= 70)")
    elif interview < 40:
        factors.append("Low interview score (< 40)")

    if skill >= 70:
        factors.append("High technical/skill assessment score (>= 70)")
    elif skill < 40:
        factors.append("Below-threshold technical skill assessment (< 40)")

    if personality >= 75:
        factors.append("High cultural & behavioral alignment score (>= 75)")

    if exp >= 5:
        factors.append(f"Substantial relevant experience ({exp} years)")
    elif exp <= 1:
        factors.append("Early-career experience profile")

    disclaimer = (
        "AI Advisory Notice: This predictive outcome is an automated statistical estimate "
        "derived from historical recruitment patterns. It is intended solely to augment recruiter "
        "insights and must NEVER be used as the sole or automated basis for actual employment decisions."
    )

    return {
        "candidate_id": candidate_data.get("candidate_id", ""),
        "candidate_name": candidate_data.get("candidate_name", "Applicant"),
        "predicted_outcome": outcome_label,
        "predicted_code": prediction,
        "selection_probability": round(prob_selected, 4),
        "rejection_probability": round(prob_rejected, 4),
        "selection_probability_pct": round(prob_selected * 100, 1),
        "rejection_probability_pct": round(prob_rejected * 100, 1),
        "confidence_score": confidence,
        "model_version": metadata.get("version", "v1.0.0"),
        "model_algorithm": metadata.get("algorithm", "RandomForestClassifier"),
        "key_factors": factors,
        "disclaimer": disclaimer
    }
