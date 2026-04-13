"""
kafka_producer.py — Kafka/Redpanda producer that streams synthetic events.

Sends JSON-serialized social-media events to the configured Kafka topic
at a configurable interval.  Gracefully shuts down on Ctrl+C.

Run directly:
    python -m producer.kafka_producer
"""

import json
import signal
import sys
import time

from confluent_kafka import Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic

from producer.data_generator import generate_event
from utils.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    PRODUCER_INTERVAL_MS,
)
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Graceful shutdown flag ──────────────────────────────────────────
_running = True


def _shutdown_handler(signum, frame):
    """Handle SIGINT / SIGTERM for graceful shutdown."""
    global _running
    logger.info("Shutdown signal received. Flushing and exiting...")
    _running = False


signal.signal(signal.SIGINT, _shutdown_handler)
signal.signal(signal.SIGTERM, _shutdown_handler)


# ── Delivery callback ──────────────────────────────────────────────

def _delivery_callback(err, msg):
    """Called once per message to confirm delivery or log errors."""
    if err is not None:
        logger.error("Message delivery failed: %s", err)
    else:
        logger.debug(
            "Delivered to %s [partition %d] @ offset %d",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


# ── Topic creation helper ──────────────────────────────────────────

def _ensure_topic_exists():
    """Create the Kafka topic if it does not already exist."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

    # Check existing topics
    metadata = admin.list_topics(timeout=10)
    if KAFKA_TOPIC in metadata.topics:
        logger.info("Topic '%s' already exists", KAFKA_TOPIC)
        return

    logger.info("Creating topic '%s'...", KAFKA_TOPIC)
    new_topic = NewTopic(KAFKA_TOPIC, num_partitions=3, replication_factor=1)
    futures = admin.create_topics([new_topic])

    for topic, future in futures.items():
        try:
            future.result()  # block until done
            logger.info("Topic '%s' created successfully", topic)
        except Exception as e:
            logger.error("Failed to create topic '%s': %s", topic, e)


# ── Main producer loop ─────────────────────────────────────────────

def run():
    """Start producing events to Kafka in a continuous loop."""
    _ensure_topic_exists()

    producer_conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "fake-trend-producer",
        "acks": "all",
    }
    producer = Producer(producer_conf)
    logger.info(
        "Producer started → topic '%s' @ %s (interval %dms)",
        KAFKA_TOPIC,
        KAFKA_BOOTSTRAP_SERVERS,
        PRODUCER_INTERVAL_MS,
    )

    event_count = 0
    interval_sec = PRODUCER_INTERVAL_MS / 1000.0

    try:
        while _running:
            event = generate_event()
            payload = json.dumps(event)

            producer.produce(
                topic=KAFKA_TOPIC,
                key=event["user_id"],
                value=payload,
                callback=_delivery_callback,
            )

            event_count += 1
            if event_count % 50 == 0:
                logger.info(
                    "Produced %d events (latest: user=%s hashtag=%s)",
                    event_count,
                    event["user_id"],
                    event["hashtag"],
                )

            # Trigger delivery callbacks
            producer.poll(0)
            time.sleep(interval_sec)

    finally:
        remaining = producer.flush(timeout=5)
        logger.info(
            "Producer stopped. Total events: %d, unflushed: %d",
            event_count,
            remaining,
        )


# ── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    run()
