"""
MongoDB Indexes Manager
Creates essential indexes on MongoDB collections for optimal aggregation performance
and safe duplicate prevention.
"""
import logging
from pymongo import ASCENDING, DESCENDING
from database.connection import get_db

logger = logging.getLogger(__name__)


def init_indexes(db=None):
    """
    Initializes indexes on all smartJobIntelligenceDB collections.
    """
    database = db if db is not None else get_db()

    # Candidates collection
    candidates = database["candidates"]
    candidates.create_index([("fingerprint", ASCENDING)], unique=True, sparse=True, name="idx_fingerprint_unique")
    candidates.create_index([("status", ASCENDING)], name="idx_status")
    candidates.create_index([("created_at", DESCENDING)], name="idx_created_at")
    candidates.create_index([("source", ASCENDING)], name="idx_source")
    candidates.create_index([("education_level", ASCENDING)], name="idx_education_level")
    candidates.create_index([("recruitment_strategy", ASCENDING)], name="idx_recruitment_strategy")
    candidates.create_index([("experience_years", ASCENDING)], name="idx_experience_years")

    # Dataset imports collection
    dataset_imports = database["dataset_imports"]
    dataset_imports.create_index([("imported_at", DESCENDING)], name="idx_imported_at")

    # Model versions collection
    model_versions = database["model_versions"]
    model_versions.create_index([("version", DESCENDING)], name="idx_model_version")
    model_versions.create_index([("trained_at", DESCENDING)], name="idx_model_trained_at")

    logger.info("MongoDB indexes successfully created for %s", database.name)
    return True
