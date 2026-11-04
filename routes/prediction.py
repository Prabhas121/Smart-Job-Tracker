"""
Machine Learning Hiring Prediction Routes
Provides REST endpoints for:
- Predicting candidate hiring outcome and confidence score
- Retrieving model evaluation metrics and feature importances
- Triggering model training / retraining on labelled MongoDB candidate data
"""
import json
import logging
from flask import Blueprint, request, jsonify
from config import Config
from ml.predict import predict_candidate_outcome, load_model
from ml.train_model import train_hiring_model
from database.connection import get_db

prediction_bp = Blueprint("prediction", __name__)
logger = logging.getLogger(__name__)


@prediction_bp.route("/api/prediction/predict", methods=["POST"])
def predict():
    """
    Accepts candidate attributes, evaluates through Random Forest Classifier,
    and returns predicted outcome, selection probability, confidence score,
    and ethical advisory disclaimer.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "Missing JSON request body."
            }), 400

        result = predict_candidate_outcome(data)
        return jsonify({
            "success": True,
            "data": result
        }), 200

    except Exception as exc:
        logger.error("Prediction error: %s", exc)
        return jsonify({
            "success": False,
            "error": "Failed to generate hiring prediction",
            "message": str(exc)
        }), 500


@prediction_bp.route("/api/prediction/model-info", methods=["GET"])
def get_model_info():
    """
    Returns metadata and evaluation metrics for the active Random Forest model:
    Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix,
    and Feature Importances.
    """
    try:
        _, metadata = load_model()

        # If metadata is empty, read directly from file or DB
        if not metadata and Config.MODEL_METADATA_PATH.exists():
            with open(Config.MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        db = get_db()
        history = list(db["model_versions"].find({}, {"_id": 0}).sort("trained_at", -1).limit(5))

        return jsonify({
            "success": True,
            "active_model": metadata,
            "version_history": history
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Failed to fetch model information",
            "message": str(exc)
        }), 500


@prediction_bp.route("/api/prediction/train", methods=["POST"])
def retrain_model():
    """
    Trains / retrains the Random Forest Classifier on current labelled candidates
    stored in MongoDB candidates collection (status: Selected or Rejected).
    Saves artifact via Joblib and updates model_versions collection.
    """
    try:
        metadata = train_hiring_model()
        return jsonify({
            "success": True,
            "message": f"Random Forest model {metadata['version']} successfully trained and saved.",
            "data": metadata
        }), 200

    except Exception as exc:
        logger.error("Training error: %s", exc)
        return jsonify({
            "success": False,
            "error": "Model training failed",
            "message": str(exc)
        }), 500
