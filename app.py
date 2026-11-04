"""
Smart Job Application Intelligence Dashboard
Main Flask Application Entry Point
"""
import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
import pandas as pd

from config import Config
from database.connection import get_db, check_connection
from database.indexes import init_indexes
from database.validators import validate_and_sanitize_candidate

# Import Blueprints
from routes.dashboard import dashboard_bp
from routes.candidates import candidates_bp
from routes.dataset import dataset_bp
from routes.analytics import analytics_bp
from routes.prediction import prediction_bp
from ml.train_model import train_hiring_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory for Flask app."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object(config_class)

    # Ensure required directories exist
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(prediction_bp)

    @app.route("/")
    def index():
        """Renders the main single-page dashboard application."""
        return render_template("index.html")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """System health and MongoDB connectivity endpoint."""
        conn_status = check_connection()
        return jsonify({
            "status": "healthy" if conn_status["status"] == "connected" else "degraded",
            "database": conn_status,
            "model_ready": Config.MODEL_PATH.exists()
        })

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


def initialize_app_data():
    """
    Ensures MongoDB indexes are created, initial recruitment data is safely imported
    into smartJobIntelligenceDB if empty, and the Random Forest model is trained.
    """
    logger.info("Initializing Smart Job Application Intelligence Dashboard...")
    try:
        db = get_db()
        init_indexes(db)

        candidates_col = db["candidates"]
        candidate_count = candidates_col.count_documents({})

        # If candidates collection is empty, populate from the official real dataset
        if candidate_count == 0 and Config.DEFAULT_DATASET_PATH.exists():
            logger.info("Database is empty. Seeding initial records from %s...", Config.DEFAULT_DATASET_PATH.name)
            df = pd.read_csv(Config.DEFAULT_DATASET_PATH)
            docs = []
            for idx, row in df.iterrows():
                record = row.to_dict()
                cleaned, err = validate_and_sanitize_candidate(record, source="real_dataset")
                if cleaned:
                    cleaned["candidate_id"] = f"CAND-{idx + 1:05d}"
                    docs.append(cleaned)

            if docs:
                candidates_col.insert_many(docs, ordered=False)
                logger.info("Successfully seeded %d initial candidates using insert_many() into %s.", len(docs), db.name)

                # Log initial import
                from datetime import datetime, timezone
                db["dataset_imports"].insert_one({
                    "source_file": "recruitment_data.csv (Initial Official Seed)",
                    "total_rows": len(df),
                    "valid_records": len(docs),
                    "invalid_records": 0,
                    "inserted_count": len(docs),
                    "skipped_duplicates": 0,
                    "imported_at": datetime.now(timezone.utc),
                    "status": "completed"
                })

        # Ensure model is trained
        if not Config.MODEL_PATH.exists():
            logger.info("Initial model not found. Training baseline Random Forest Classifier...")
            train_hiring_model()

    except Exception as exc:
        logger.warning("Auto-initialization notice: %s", exc)


app = create_app()

if __name__ == "__main__":
    initialize_app_data()
    port = int(os.environ.get("PORT", 5001))
    logger.info("Starting Smart Job Application Intelligence Dashboard on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=Config.DEBUG)
