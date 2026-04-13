"""
main.py — FastAPI application entry point.

Exposes REST endpoints for querying trending hashtags, suspicious users,
and flagged posts stored in MongoDB.

Run directly:
    python -m api.main
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import trends, suspicious, flagged
from db.mongo_client import ensure_indexes, get_client
from utils.config import API_HOST, API_PORT
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Lifespan: startup / shutdown logic ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the app begins serving requests."""
    logger.info("Starting API server...")

    # Verify MongoDB is reachable
    try:
        get_client().admin.command("ping")
        logger.info("MongoDB is connected ✓")
    except Exception as e:
        logger.error("MongoDB is NOT reachable: %s", e)

    ensure_indexes()
    yield
    logger.info("API server shutting down.")


# ── FastAPI app ─────────────────────────────────────────────────────

app = FastAPI(
    title="Fake Trend Detection API",
    description=(
        "Real-time API for querying trending hashtags, suspicious users, "
        "and flagged social-media posts detected by the streaming pipeline."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow all origins for local development) ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────────────────
app.include_router(trends.router)
app.include_router(suspicious.router)
app.include_router(flagged.router)


# ── Health check ────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    """Quick health check for the API and database connectivity."""
    try:
        get_client().admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {"status": "ok", "database": db_status}


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
