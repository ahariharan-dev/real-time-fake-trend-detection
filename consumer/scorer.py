"""
scorer.py — Combines detector outputs into a single suspicion score.

Takes spike_score and bot_score, produces a weighted suspicion_score,
and determines whether the event should be flagged.
"""

from utils.logger import get_logger

logger = get_logger(__name__)

# Weight distribution for the final score
_SPIKE_WEIGHT = 0.5
_BOT_WEIGHT = 0.5

# Events with a suspicion score above this threshold get flagged
FLAG_THRESHOLD = 0.3


class Scorer:
    """
    Merges detection signals into a single suspicion score.

    Formula:
        suspicion_score = SPIKE_WEIGHT × spike_score + BOT_WEIGHT × bot_score

    An event is flagged if suspicion_score > FLAG_THRESHOLD.
    """

    def __init__(
        self,
        spike_weight: float = _SPIKE_WEIGHT,
        bot_weight: float = _BOT_WEIGHT,
        flag_threshold: float = FLAG_THRESHOLD,
    ):
        self.spike_weight = spike_weight
        self.bot_weight = bot_weight
        self.flag_threshold = flag_threshold

    def compute(self, spike_score: float, bot_score: float) -> dict:
        """
        Compute the final suspicion score and flag decision.

        Args:
            spike_score: Output from FakeTrendDetector (0.0 – 1.0).
            bot_score:   Output from BotDetector (0.0 – 1.0).

        Returns:
            Dict with:
              - spike_score      (float)
              - bot_score        (float)
              - suspicion_score  (float, rounded to 3 decimals)
              - is_flagged       (bool)
        """
        suspicion_score = (
            self.spike_weight * spike_score + self.bot_weight * bot_score
        )
        suspicion_score = round(min(suspicion_score, 1.0), 3)
        is_flagged = suspicion_score > self.flag_threshold

        if is_flagged:
            logger.info(
                "🚩 FLAGGED — spike=%.2f bot=%.2f → suspicion=%.3f",
                spike_score, bot_score, suspicion_score,
            )

        return {
            "spike_score": round(spike_score, 3),
            "bot_score": round(bot_score, 3),
            "suspicion_score": suspicion_score,
            "is_flagged": is_flagged,
        }
