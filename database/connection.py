"""
Database Connection Manager
Provides singleton-like access to MongoDB client and collections.
Guarantees database isolation for Smart Job Application Intelligence Dashboard.
"""
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

logger = logging.getLogger(__name__)

# Cached client instance
_client = None


def get_client(uri: str = None) -> MongoClient:
    """
    Get or create a MongoClient instance with reasonable timeouts.
    """
    global _client
    if _client is None:
        mongo_uri = uri or Config.MONGO_URI
        _client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000
        )
    return _client


def get_db(db_name: str = None):
    """
    Get the MongoDB database instance.
    STRICT SAFETY: Only allows connecting to smartJobIntelligenceDB or test databases.
    If running within a Flask application context, honors current_app.config['DATABASE_NAME'].
    """
    if db_name:
        target_db_name = db_name
    else:
        try:
            from flask import current_app, has_app_context
            if has_app_context() and "DATABASE_NAME" in current_app.config:
                target_db_name = current_app.config["DATABASE_NAME"]
            else:
                target_db_name = Config.DATABASE_NAME
        except ImportError:
            target_db_name = Config.DATABASE_NAME
    
    # Isolation safeguard: refuse any connection to external databases
    if not (target_db_name.startswith("smartJobIntelligenceDB")):
        raise ValueError(
            f"Security Exception: Access denied to database '{target_db_name}'. "
            "This application is restricted solely to 'smartJobIntelligenceDB*'."
        )

    client = get_client()
    return client[target_db_name]


def check_connection() -> dict:
    """
    Ping MongoDB server and verify connection status.
    Returns status dict with server info or error message.
    """
    try:
        client = get_client()
        client.admin.command("ping")
        return {
            "status": "connected",
            "database": Config.DATABASE_NAME,
            "uri": Config.MONGO_URI.split("@")[-1]  # Mask credentials if any
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        logger.error("MongoDB connection failed: %s", err)
        return {
            "status": "disconnected",
            "database": Config.DATABASE_NAME,
            "error": "MongoDB server is not reachable on localhost:27017"
        }


def close_connection():
    """Close the active MongoDB client connection if open."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
