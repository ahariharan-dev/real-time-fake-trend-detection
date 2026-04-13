"""
flagged.py — Flagged posts API route.
"""

from fastapi import APIRouter, Query
from db.mongo_client import get_flagged_posts

router = APIRouter(prefix="/api/v1", tags=["Flagged Posts"])


@router.get(
    "/flagged-posts",
    summary="Get flagged posts",
    description="Returns the most recent posts flagged as suspicious, with pagination.",
)
def flagged_posts(
    limit: int = Query(default=20, ge=1, le=100, description="Max posts to return"),
    skip: int = Query(default=0, ge=0, description="Number of posts to skip (pagination)"),
):
    """Fetch paginated list of flagged posts, newest first."""
    results = get_flagged_posts(limit=limit, skip=skip)
    return {
        "count": len(results),
        "skip": skip,
        "limit": limit,
        "flagged_posts": results,
    }
