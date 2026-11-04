"""
Configuration Module for Smart Job Application Intelligence Dashboard
Loads settings from environment variables with safe defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-job-intelligence-default-secret-key-2026")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "smartJobIntelligenceDB")
    PORT = int(os.getenv("PORT", 5001))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Uploads directory
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # Model storage directory
    MODEL_DIR = BASE_DIR / "models"
    MODEL_PATH = MODEL_DIR / "random_forest_hiring_model.joblib"
    MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"

    # Default dataset path
    DEFAULT_DATASET_PATH = BASE_DIR / "data" / "recruitment_data.csv"


class TestConfig(Config):
    """Configuration for automated test suite."""
    TESTING = True
    DEBUG = False
    DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "smartJobIntelligenceDB_test")
