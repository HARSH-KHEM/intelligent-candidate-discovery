"""
mongo.py — MongoDB connection using Motor (async driver).

Provides a singleton MongoDB client and collection accessors for:
  - candidates
  - jobs
  - results (ranking job results)

Usage:
    from backend.db.mongo import get_db, get_candidates_collection
"""

import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/candidate_discovery")
DB_NAME = "candidate_discovery"

# ─── Singleton Client ────────────────────────────────────────
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB and return the database instance.
    Creates indexes on first connection.
    """
    global _client, _db

    if _db is not None:
        return _db

    logger.info(f"Connecting to MongoDB: {MONGODB_URI}")
    _client = AsyncIOMotorClient(MONGODB_URI)
    _db = _client[DB_NAME]

    # Create indexes
    await _db.candidates.create_index("candidate_id", unique=True)
    await _db.jobs.create_index("created_at")
    await _db.results.create_index("job_id", unique=True)

    # Verify connection
    await _client.admin.command("ping")
    logger.info("MongoDB connected successfully.")

    return _db


async def close_db():
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    """Get the current database instance."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db


def get_candidates_collection():
    """Get the candidates collection."""
    return get_db().candidates


def get_jobs_collection():
    """Get the jobs collection."""
    return get_db().jobs


def get_results_collection():
    """Get the results collection."""
    return get_db().results
