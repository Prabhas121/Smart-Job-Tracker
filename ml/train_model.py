"""
Model Training Module
Trains a Random Forest Classifier on labelled recruitment candidate data.
Uses Stratified K-fold / Train-Test Split, serializes model via Joblib,
and tracks version metadata in MongoDB.
"""
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from config import Config
from ml.preprocess import (
    FEATURE_COLUMNS,
    clean_and_prepare_dataframe,
    extract_features_and_target
)
from ml.evaluate import evaluate_model
from database.connection import get_db

logger = logging.getLogger(__name__)


def train_hiring_model(
    df: Optional[pd.DataFrame] = None,
    db_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trains a Random Forest classifier using labelled candidate records.
    If df is None, loads labelled records directly from MongoDB 'candidates' collection.
    If MongoDB has no records yet, falls back to the default dataset.
    """
    db = get_db(db_name)
    candidates_col = db["candidates"]
    model_versions_col = db["model_versions"]

    # Load data
    if df is not None:
        data_source = "custom_dataframe"
        raw_df = df
    else:
        # Fetch labelled records from MongoDB candidates collection
        # Only candidates with verified status (Selected or Rejected) are eligible!
        cursor = candidates_col.find(
            {"status": {"$in": ["Selected", "Rejected"]}},
            {"_id": 0}
        )
        records = list(cursor)

        if len(records) >= 50:
            raw_df = pd.DataFrame(records)
            data_source = f"mongodb_candidates ({len(records)} records)"
        else:
            # Fall back to default recruitment dataset if MongoDB doesn't have sufficient records yet
            if Config.DEFAULT_DATASET_PATH.exists():
                raw_df = pd.read_csv(Config.DEFAULT_DATASET_PATH)
                data_source = f"default_dataset_file ({len(raw_df)} records)"
            else:
                raise FileNotFoundError(
                    f"Default recruitment dataset not found at {Config.DEFAULT_DATASET_PATH} "
                    "and insufficient MongoDB candidate records to train."
                )

    # Preprocess features & target (guarantees exclusion of sensitive attributes and data leakage)
    X, y = extract_features_and_target(raw_df)

    if len(y.unique()) < 2:
        raise ValueError("Training requires at least two distinct outcome classes (Selected and Rejected).")

    # Stratified train-test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    # Initialize and train Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)

    # Predict on test set
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1] if hasattr(rf, "predict_proba") else None

    # Evaluate
    metrics = evaluate_model(y_test, y_pred, y_prob)

    # Extract feature importances
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in sorted(
            zip(FEATURE_COLUMNS, rf.feature_importances_),
            key=lambda x: x[1],
            reverse=True
        )
    }

    # Versioning
    version_count = model_versions_col.count_documents({}) + 1
    version_str = f"v{version_count}.0.0"
    timestamp = datetime.now(timezone.utc)

    # Ensure model directory exists
    Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Save model artifact using Joblib
    joblib.dump(rf, Config.MODEL_PATH)

    # Prepare metadata document
    metadata = {
        "version": version_str,
        "algorithm": "RandomForestClassifier",
        "parameters": {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 4,
            "min_samples_leaf": 2,
            "class_weight": "balanced",
            "random_state": 42
        },
        "features": FEATURE_COLUMNS,
        "data_source": data_source,
        "total_dataset_size": int(len(X)),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "metrics": metrics,
        "feature_importances": feature_importances,
        "trained_at": timestamp.isoformat(),
        "model_file": str(Config.MODEL_PATH.name)
    }

    # Save metadata locally to JSON
    with open(Config.MODEL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Store version in MongoDB collection
    model_versions_col.insert_one({
        "version": version_str,
        "algorithm": "RandomForestClassifier",
        "features": FEATURE_COLUMNS,
        "data_source": data_source,
        "total_dataset_size": int(len(X)),
        "metrics": metrics,
        "feature_importances": feature_importances,
        "trained_at": timestamp
    })

    logger.info("Successfully trained and saved model version %s", version_str)
    return metadata
