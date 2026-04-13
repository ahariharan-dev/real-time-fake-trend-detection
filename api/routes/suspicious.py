"""
suspicious.py — Suspicious users API route.
"""

from fastapi import APIRouter, Query
from db.mongo_client import get_suspicious_users

router = APIRouter(prefix="/api/v1", tags=["Suspicious Users"])


@router.get(
    "/suspicious-users",
    summary="Get suspicious users",
    description="Returns users with the highest average suspicion scores from flagged posts.",
)
def suspicious_users(
    limit: int = Query(default=10, ge=1, le=50, description="Max users to return"),
):
    """Fetch users ranked by average suspicion score."""
    results = get_suspicious_users(limit=limit)
    return {
        "count": len(results),
        "suspicious_users": results,
    }
