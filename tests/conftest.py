"""
Pytest Fixtures for Smart Job Application Intelligence Dashboard
Guarantees isolated execution using 'smartJobIntelligenceDB_test'.
Never interacts with production or external databases.
"""
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import TestConfig
from app import create_app
from database.connection import get_client, get_db
from database.indexes import init_indexes


@pytest.fixture(scope="session")
def app():
    """Create Flask application with TestConfig."""
    app_instance = create_app(TestConfig)
    return app_instance


@pytest.fixture(scope="session")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def clean_test_db():
    """
    Provides clean test database instance 'smartJobIntelligenceDB_test'.
    Strictly isolated and cleaned before each test.
    """
    client = get_client()
    db = client[TestConfig.DATABASE_NAME]
    assert db.name == "smartJobIntelligenceDB_test", f"Safety error: attempted clean on {db.name}"

    # Drop collections in test database only
    db["candidates"].drop()
    db["dataset_imports"].drop()
    db["model_versions"].drop()

    init_indexes(db)
    yield db

    # Teardown: clean up test database
    db["candidates"].drop()
    db["dataset_imports"].drop()
    db["model_versions"].drop()
