"""
bot_detector.py — Bot behavior detection via posting frequency and content duplication.

Tracks per-user posting rates and checks for duplicate / near-duplicate
text content — both strong signals of automated bot behavior.
"""

import time
from collections import defaultdict, deque
from difflib import SequenceMatcher

from utils.config import (
    WINDOW_SIZE_SECONDS,
    BOT_POST_THRESHOLD,
    DUPLICATE_SIMILARITY_THRESHOLD,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum number of recent texts to keep per user for duplication checks
_MAX_RECENT_TEXTS = 20


class BotDetector:
    """
    Detects bot-like behavior per user.

    Algorithm
    ---------
    1. Track per-user post timestamps in a sliding window.
    2. If a user's post count exceeds BOT_POST_THRESHOLD → high freq score.
    3. Compare each post's text against the user's recent texts.
    4. If similarity > DUPLICATE_SIMILARITY_THRESHOLD → duplication score.
    5. Final bot_score = max(freq_score, dup_score).
    """

    def __init__(
        self,
        window_seconds: int = WINDOW_SIZE_SECONDS,
        post_threshold: int = BOT_POST_THRESHOLD,
        similarity_threshold: float = DUPLICATE_SIMILARITY_THRESHOLD,
    ):
        self.window_seconds = window_seconds
        self.post_threshold = post_threshold
        self.similarity_threshold = similarity_threshold

        # user_id → deque of timestamps
        self._post_windows: dict[str, deque] = defaultdict(deque)

        # user_id → deque of recent text strings
        self._recent_texts: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=_MAX_RECENT_TEXTS)
        )

    def _evict_old_posts(self, user_id: str, now: float) -> None:
        """Remove timestamps older than the sliding window for a user."""
        window = self._post_windows[user_id]
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()

    def _check_frequency(self, user_id: str, now: float) -> float:
        """
        Return a frequency score [0.0 – 1.0] based on how many posts
        the user has made within the sliding window.
        """
        self._post_windows[user_id].append(now)
        self._evict_old_posts(user_id, now)

        post_count = len(self._post_windows[user_id])

        if post_count >= self.post_threshold:
            # Scale linearly: threshold → 0.5, 2×threshold → 1.0
            score = min(post_count / (2 * self.post_threshold), 1.0)
            return max(score, 0.5)  # floor at 0.5 once threshold is hit

        return 0.0

    def _check_duplicate(self, user_id: str, text: str) -> float:
        """
        Compare the incoming text against the user's recent posts.
        Returns the highest similarity score found (0.0 – 1.0).
        """
        max_similarity = 0.0

        for prev_text in self._recent_texts[user_id]:
            ratio = SequenceMatcher(None, text, prev_text).ratio()
            if ratio > max_similarity:
                max_similarity = ratio

        # Store this text for future comparisons
        self._recent_texts[user_id].append(text)

        if max_similarity >= self.similarity_threshold:
            return max_similarity

        return 0.0

    def analyze(self, event: dict) -> float:
        """
        Analyze an incoming event for bot-like behavior.

        Args:
            event: Dict with at least 'user_id' and 'text' fields.

        Returns:
            bot_score between 0.0 (human-like) and 1.0 (definite bot).
        """
        user_id = event.get("user_id", "unknown")
        text = event.get("text", "")
        now = time.time()

        freq_score = self._check_frequency(user_id, now)
        dup_score = self._check_duplicate(user_id, text)

        bot_score = max(freq_score, dup_score)

        if bot_score > 0:
            logger.debug(
                "BOT SIGNAL: user=%s freq=%.2f dup=%.2f final=%.2f",
                user_id, freq_score, dup_score, bot_score,
            )

        return bot_score
