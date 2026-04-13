"""
data_generator.py — Synthetic social-media event generator.

Produces realistic post events with controlled anomalies:
  • Normal mode  — random user, random hashtag, unique text
  • Spike mode   — many posts share the same "trending" hashtag
  • Bot mode     — a single user posts duplicate content rapidly
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker
from utils.config import ANOMALY_PROBABILITY
from utils.logger import get_logger

logger = get_logger(__name__)
fake = Faker()

# ── Static pools ────────────────────────────────────────────────────

# 500 normal users
NORMAL_USERS = [f"user_{i:04d}" for i in range(1, 501)]

# 10 bot accounts (used during anomaly bursts)
BOT_USERS = [f"bot_{i:03d}" for i in range(1, 11)]

# 50 normal hashtags
HASHTAGS = [
    "#AI", "#ML", "#Python", "#DataScience", "#Cloud", "#DevOps",
    "#Blockchain", "#Crypto", "#NFT", "#Web3", "#React", "#Node",
    "#Flutter", "#Rust", "#Go", "#Docker", "#Kubernetes", "#AWS",
    "#Azure", "#GCP", "#Startup", "#Tech", "#Innovation", "#Code",
    "#OpenSource", "#Linux", "#Gaming", "#Esports", "#Music",
    "#Travel", "#Fitness", "#Health", "#Food", "#Fashion",
    "#Photography", "#Art", "#Design", "#UX", "#Mobile", "#IoT",
    "#5G", "#Robotics", "#SpaceX", "#Climate", "#EV", "#Fintech",
    "#EdTech", "#SaaS", "#API", "#BigData", "#CyberSecurity",
]

# 2-3 hashtags that will be used for fake-trend spikes
SPIKE_HASHTAGS = ["#SCAM_COIN", "#FAKE_NEWS_ALERT", "#BUY_NOW_777"]

# Pre-built corpus of normal-ish tweet texts
NORMAL_TEXTS = [
    "Just learned something amazing about {topic} today!",
    "Can't believe how fast {topic} is evolving 🚀",
    "Working on a new project with {topic}. Wish me luck!",
    "Hot take: {topic} is overrated. Change my mind.",
    "Great thread on {topic} — definitely worth reading.",
    "Anyone else excited about the future of {topic}?",
    "My {topic} setup is finally complete! 🎉",
    "Unpopular opinion: {topic} will dominate in 2026.",
    "Just deployed my first {topic} app. Feels good!",
    "The {topic} community is the best. So helpful!",
    "{topic} meetup was incredible tonight 🔥",
    "Started a blog series on {topic}. Link in bio.",
    "Debugging {topic} issues at 2am... again 😅",
    "New {topic} release just dropped. Let's gooo!",
    "Pair programming with {topic} is a game changer.",
]

# Duplicate text used by bots
BOT_TEXTS = [
    "🔥 Don't miss this opportunity! Click the link NOW! 🔥",
    "I made $5000 in one day! DM me to learn how!",
    "FREE giveaway! RT and follow to win! Limited time only!",
    "This is the next big thing! Invest before it's too late!",
    "Check out this AMAZING deal! You won't regret it! 💰💰💰",
]


def _generate_normal_post() -> dict:
    """Generate a single normal (non-anomalous) post."""
    topic = random.choice(HASHTAGS).replace("#", "")
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(NORMAL_USERS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashtag": random.choice(HASHTAGS),
        "text": random.choice(NORMAL_TEXTS).format(topic=topic),
        "likes": random.randint(0, 500),
        "retweets": random.randint(0, 200),
    }


def _generate_spike_post() -> dict:
    """Generate a post contributing to a fake-trend hashtag spike."""
    topic = random.choice(SPIKE_HASHTAGS).replace("#", "").replace("_", " ")
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(BOT_USERS + NORMAL_USERS[:20]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashtag": random.choice(SPIKE_HASHTAGS),  # forced spike hashtag
        "text": random.choice(NORMAL_TEXTS).format(topic=topic),
        "likes": random.randint(0, 10),   # bots get low engagement
        "retweets": random.randint(0, 5),
    }


def _generate_bot_post() -> dict:
    """Generate a bot post — single user, duplicate text, low engagement."""
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(BOT_USERS),        # concentrated users
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashtag": random.choice(SPIKE_HASHTAGS + HASHTAGS[:5]),
        "text": random.choice(BOT_TEXTS),            # duplicate content
        "likes": random.randint(0, 5),
        "retweets": random.randint(0, 3),
    }


def generate_event() -> dict:
    """
    Generate a single social-media event.

    With probability ANOMALY_PROBABILITY the event will be anomalous
    (either a hashtag spike or a bot post).  Otherwise it's normal.
    """
    roll = random.random()

    if roll < ANOMALY_PROBABILITY / 2:
        # ~7.5 % — hashtag spike
        return _generate_spike_post()
    elif roll < ANOMALY_PROBABILITY:
        # ~7.5 % — bot burst
        return _generate_bot_post()
    else:
        # ~85 % — normal traffic
        return _generate_normal_post()
