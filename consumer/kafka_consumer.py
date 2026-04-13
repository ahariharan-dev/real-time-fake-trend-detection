"""
kafka_consumer.py — Real-time stream processor.

Consumes events from the Kafka/Redpanda topic, runs them through the
detection pipeline (FakeTrendDetector → BotDetector → Scorer), and
writes results to MongoDB.

Run directly:
    python -m consumer.kafka_consumer
"""

import json
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException

from consumer.detectors.fake_trend_detector import FakeTrendDetector
from consumer.detectors.bot_detector import BotDetector
from consumer.scorer import Scorer

from db.mongo_client import (
    ensure_indexes,
    insert_raw_post,
    insert_flagged_post,
)
from utils.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    KAFKA_GROUP_ID,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Graceful shutdown ───────────────────────────────────────────────
_running = True


def _shutdown_handler(signum, frame):
    global _running
    logger.info("Shutdown signal received. Closing consumer...")
    _running = False


signal.signal(signal.SIGINT, _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)


# ── Main consumer loop ─────────────────────────────────────────────

def run():
    """Start consuming and processing events from Kafka."""

    # Initialize detectors
    trend_detector = FakeTrendDetector()
    bot_detector = BotDetector()
    scorer = Scorer()

    # Ensure MongoDB indexes exist
    ensure_indexes()

    # Configure consumer
    consumer_conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "latest",     # start from newest messages
        "enable.auto.commit": False,        # manual commit after processing
        "session.timeout.ms": 10000,
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    logger.info(
        "Consumer started — group '%s' → topic '%s' @ %s",
        KAFKA_GROUP_ID,
        KAFKA_TOPIC,
        KAFKA_BOOTSTRAP_SERVERS,
    )

    processed = 0
    flagged = 0

    try:
        while _running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition — not an error, just no more messages
                    continue
                else:
                    logger.error("Consumer error: %s", msg.error())
                    continue

            # ── Deserialize ──────────────────────────────────────────
            try:
                event = json.loads(msg.value().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning("Skipping malformed message: %s", e)
                consumer.commit(asynchronous=False)
                continue

            # ── Run detection pipeline ───────────────────────────────
            spike_score = trend_detector.analyze(event)
            bot_score = bot_detector.analyze(event)
            result = scorer.compute(spike_score, bot_score)

            # Enrich the event with detection results
            event.update(result)

            # ── Store in MongoDB ─────────────────────────────────────
            insert_raw_post(event)

            if result["is_flagged"]:
                insert_flagged_post(event)
                flagged += 1

            processed += 1

            if processed % 50 == 0:
                logger.info(
                    "Processed %d events (%d flagged) — latest: user=%s score=%.3f",
                    processed,
                    flagged,
                    event.get("user_id", "?"),
                    result["suspicion_score"],
                )

            # Commit offset after successful processing
            consumer.commit(asynchronous=False)

    except KafkaException as e:
        logger.error("Kafka exception: %s", e)

    finally:
        consumer.close()
        logger.info(
            "Consumer stopped. Total processed: %d, flagged: %d",
            processed,
            flagged,
        )


# ── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run()
