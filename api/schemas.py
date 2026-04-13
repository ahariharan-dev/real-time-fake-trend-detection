"""
schemas.py — Pydantic response models for the FastAPI endpoints.
"""

from pydantic import BaseModel


class TrendingHashtag(BaseModel):
    """A single trending hashtag with its post count."""
    hashtag: str
    count: int


class SuspiciousUser(BaseModel):
    """A user flagged for suspicious behavior."""
    user_id: str
    avg_score: float
    flag_count: int


class FlaggedPost(BaseModel):
    """A social-media event that was flagged by the detection pipeline."""
    event_id: str
    user_id: str
    timestamp: str
    hashtag: str
    text: str
    likes: int
    retweets: int
    spike_score: float
    bot_score: float
    suspicion_score: float
    is_flagged: bool


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    database: str
