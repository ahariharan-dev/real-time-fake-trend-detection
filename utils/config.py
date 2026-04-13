"""
config.py — Centralized configuration loader.

Reads settings from the .env file at the project root and exposes them
as module-level constants so every other module can simply:

    from utils.config import KAFKA_BOOTSTRAP_SERVERS, MONGO_URI
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ─────────────────────────────────────
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# ── Kafka / Redpanda ────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "social_stream")
KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "fake_trend_consumer_group")

# ── MongoDB ─────────────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB: str = os.getenv("MONGO_DB", "fake_trend_db")
RAW_COLLECTION: str = os.getenv("RAW_COLLECTION", "raw_posts")
FLAGGED_COLLECTION: str = os.getenv("FLAGGED_COLLECTION", "flagged_posts")

# ── FastAPI ─────────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# ── Producer settings ───────────────────────────────────────────────
PRODUCER_INTERVAL_MS: int = int(os.getenv("PRODUCER_INTERVAL_MS", "200"))
ANOMALY_PROBABILITY: float = float(os.getenv("ANOMALY_PROBABILITY", "0.15"))

# ── Detection settings ─────────────────────────────────────────────
WINDOW_SIZE_SECONDS: int = int(os.getenv("WINDOW_SIZE_SECONDS", "60"))
SPIKE_THRESHOLD: float = float(os.getenv("SPIKE_THRESHOLD", "5.0"))
BOT_POST_THRESHOLD: int = int(os.getenv("BOT_POST_THRESHOLD", "10"))
DUPLICATE_SIMILARITY_THRESHOLD: float = float(
    os.getenv("DUPLICATE_SIMILARITY_THRESHOLD", "0.85")
)
