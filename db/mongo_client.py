"""
mongo_client.py — MongoDB connection manager and helper functions.

Provides a singleton client, collection accessors, and query helpers
used by both the consumer (writes) and the API (reads).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from utils.config import (
    MONGO_URI,
    MONGO_DB,
    RAW_COLLECTION,
    FLAGGED_COLLECTION,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Singleton client ────────────────────────────────────────────────
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return (and lazily create) the singleton MongoClient."""
    global _client
    if _client is None:
        logger.info("Connecting to MongoDB at %s", MONGO_URI)
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Force a connection attempt so errors surface early
        _client.admin.command("ping")
        logger.info("MongoDB connection established")
    return _client


def get_database() -> Database:
    """Return the project database."""
    return get_client()[MONGO_DB]


def get_raw_collection() -> Collection:
    """Return the raw_posts collection."""
    return get_database()[RAW_COLLECTION]


def get_flagged_collection() -> Collection:
    """Return the flagged_posts collection."""
    return get_database()[FLAGGED_COLLECTION]


# ── Index setup (call once at startup) ──────────────────────────────

def ensure_indexes() -> None:
    """Create indexes for efficient querying."""
    raw = get_raw_collection()
    raw.create_index([("timestamp", DESCENDING)])
    raw.create_index("hashtag")
    raw.create_index("user_id")

    flagged = get_flagged_collection()
    flagged.create_index([("timestamp", DESCENDING)])
    flagged.create_index("user_id")
    flagged.create_index("hashtag")
    flagged.create_index([("suspicion_score", DESCENDING)])

    logger.info("MongoDB indexes ensured")


# ── Write helpers ───────────────────────────────────────────────────

def insert_raw_post(doc: dict[str, Any]) -> None:
    """Insert a single document into raw_posts."""
    get_raw_collection().insert_one(doc)


def insert_flagged_post(doc: dict[str, Any]) -> None:
    """Insert a single document into flagged_posts."""
    get_flagged_collection().insert_one(doc)


# ── Read helpers (used by API) ──────────────────────────────────────

def get_trending_hashtags(minutes: int = 5, limit: int = 10) -> list[dict]:
    """
    Aggregate the most-used hashtags in the last `minutes` minutes
    from raw_posts.  Returns list of {hashtag, count}.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    pipeline = [
        {"$match": {"timestamp": {"$gte": cutoff.isoformat()}}},
        {"$group": {"_id": "$hashtag", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "hashtag": "$_id", "count": 1}},
    ]
    return list(get_raw_collection().aggregate(pipeline))


def get_suspicious_users(limit: int = 10) -> list[dict]:
    """
    Aggregate users from flagged_posts with the highest average
    suspicion score.  Returns list of {user_id, avg_score, flag_count}.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$user_id",
                "avg_score": {"$avg": "$suspicion_score"},
                "flag_count": {"$sum": 1},
            }
        },
        {"$sort": {"avg_score": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "user_id": "$_id",
                "avg_score": {"$round": ["$avg_score", 3]},
                "flag_count": 1,
            }
        },
    ]
    return list(get_flagged_collection().aggregate(pipeline))


def get_flagged_posts(limit: int = 20, skip: int = 0) -> list[dict]:
    """
    Return the most recent flagged posts, paginated.
    Excludes the MongoDB _id field for clean JSON responses.
    """
    cursor = (
        get_flagged_collection()
        .find({}, {"_id": 0})
        .sort("timestamp", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)
