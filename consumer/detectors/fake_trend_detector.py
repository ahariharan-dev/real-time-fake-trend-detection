"""
fake_trend_detector.py — Sliding-window hashtag spike detection.

Tracks hashtag frequency over a configurable time window and flags
sudden spikes that exceed a threshold relative to the historical
moving average.
"""

import time
from collections import defaultdict, deque

from utils.config import WINDOW_SIZE_SECONDS, SPIKE_THRESHOLD
from utils.logger import get_logger

logger = get_logger(__name__)


class FakeTrendDetector:
    """
    Detects fake trends by measuring hashtag velocity spikes.

    Algorithm
    ---------
    1. Keep a per-hashtag deque of event timestamps (sliding window).
    2. On each event, compute the current posting rate for that hashtag.
    3. Compare against an exponential moving average of past rates.
    4. If current_rate > SPIKE_THRESHOLD × ema_rate → spike detected.
    """

    def __init__(
        self,
        window_seconds: int = WINDOW_SIZE_SECONDS,
        spike_threshold: float = SPIKE_THRESHOLD,
        ema_alpha: float = 0.1,
    ):
        self.window_seconds = window_seconds
        self.spike_threshold = spike_threshold
        self.ema_alpha = ema_alpha

        # hashtag → deque of timestamps (float epoch)
        self._windows: dict[str, deque] = defaultdict(deque)

        # hashtag → exponential moving average of rate
        self._ema_rates: dict[str, float] = defaultdict(lambda: 1.0)

    def _evict_old_entries(self, hashtag: str, now: float) -> None:
        """Remove timestamps older than the sliding window."""
        window = self._windows[hashtag]
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()

    def analyze(self, event: dict) -> float:
        """
        Analyze an incoming event for hashtag spike behavior.

        Args:
            event: Dict with at least 'hashtag' and 'timestamp' fields.

        Returns:
            spike_score between 0.0 (normal) and 1.0 (definite spike).
        """
        hashtag = event.get("hashtag", "")
        now = time.time()

        # Update the sliding window
        self._windows[hashtag].append(now)
        self._evict_old_entries(hashtag, now)

        # Current rate: events per second in the window
        window_count = len(self._windows[hashtag])
        current_rate = window_count / max(self.window_seconds, 1)

        # Update EMA
        ema = self._ema_rates[hashtag]
        new_ema = self.ema_alpha * current_rate + (1 - self.ema_alpha) * ema
        self._ema_rates[hashtag] = new_ema

        # Detect spike: current rate significantly above expected
        if ema > 0 and current_rate > self.spike_threshold * ema:
            # Normalize the spike score between 0 and 1
            ratio = current_rate / (self.spike_threshold * ema)
            spike_score = min(ratio, 1.0)

            logger.debug(
                "SPIKE: %s rate=%.4f ema=%.4f ratio=%.2f score=%.2f",
                hashtag, current_rate, ema, ratio, spike_score,
            )
            return spike_score

        return 0.0
