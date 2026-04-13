"""
trends.py — Trending hashtags API route.
"""

from fastapi import APIRouter, Query
from db.mongo_client import get_trending_hashtags

router = APIRouter(prefix="/api/v1", tags=["Trends"])


@router.get(
    "/trends",
    summary="Get trending hashtags",
    description="Returns the top hashtags by post count within the last N minutes.",
)
def trending_hashtags(
    minutes: int = Query(default=5, ge=1, le=60, description="Lookback window in minutes"),
    limit: int = Query(default=10, ge=1, le=50, description="Max hashtags to return"),
):
    """Fetch the most-used hashtags in recent posts."""
    results = get_trending_hashtags(minutes=minutes, limit=limit)
    return {
        "window_minutes": minutes,
        "count": len(results),
        "trends": results,
    }
