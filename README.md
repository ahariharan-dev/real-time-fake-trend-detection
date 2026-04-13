[README.md](https://github.com/user-attachments/files/26680303/README.md)
# 🚨 Real-Time Fake Trend Detection & Bot Activity Analysis System

A production-grade data engineering pipeline that ingests simulated social media data in real time, detects fake trends and bot activity using sliding-window algorithms, and exposes results through a REST API.

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐     ┌─────────────┐
│   Producer   │────▶│  Redpanda/Kafka   │────▶│     Consumer       │────▶│   MongoDB   │
│  (Generator) │     │  (social_stream)  │     │  (Stream Processor)│     │  (Storage)  │
└──────────────┘     └──────────────────┘     └────────────────────┘     └──────┬──────┘
                             │                         │                        │
                             ▼                         ▼                        ▼
                      Redpanda Console         Detection Pipeline         FastAPI (API)
                      (localhost:8080)         ┌─────────────────┐       (localhost:8000)
                                               │ FakeTrendDetect │
                                               │  BotDetector    │
                                               │  Scorer         │
                                               └─────────────────┘
```

### Data Flow

1. **Producer** generates synthetic social-media posts (with ~15% anomalies) and publishes them to the `social_stream` Kafka topic.
2. **Redpanda** (Kafka-compatible broker) buffers and distributes events.
3. **Consumer** reads events in real time and runs them through:
   - **FakeTrendDetector** — sliding-window hashtag spike detection using EMA
   - **BotDetector** — per-user posting frequency + text duplication analysis
   - **Scorer** — combines signals into a single `suspicion_score`
4. Enriched events are stored in **MongoDB**:
   - `raw_posts` — all events with their scores
   - `flagged_posts` — only events with `suspicion_score > 0.3`
5. **FastAPI** serves REST endpoints to query trends, suspicious users, and flagged posts.

---

## 📁 Project Structure

```
Faketrend-detection/
├── docker/
│   └── docker-compose.yml          # Redpanda + MongoDB
├── producer/
│   ├── data_generator.py           # Synthetic data with anomalies
│   └── kafka_producer.py           # Kafka producer + main loop
├── consumer/
│   ├── kafka_consumer.py           # Kafka consumer + main loop
│   ├── scorer.py                   # Score combiner
│   └── detectors/
│       ├── fake_trend_detector.py  # Hashtag spike detection
│       └── bot_detector.py         # Bot behavior detection
├── api/
│   ├── main.py                     # FastAPI entry point
│   ├── schemas.py                  # Pydantic response models
│   └── routes/
│       ├── trends.py               # GET /api/v1/trends
│       ├── suspicious.py           # GET /api/v1/suspicious-users
│       └── flagged.py              # GET /api/v1/flagged-posts
├── db/
│   └── mongo_client.py             # MongoDB connection + helpers
├── utils/
│   ├── config.py                   # .env loader
│   └── logger.py                   # Centralized logging
├── .env                            # Configuration
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

---

## 🚀 Setup & Run (Step by Step)

### Prerequisites

- **Docker Desktop** (running)
- **Python 3.10+**
- **pip**

### Step 1: Start Infrastructure (Redpanda + MongoDB)

```bash
cd Faketrend-detection
docker compose -f docker/docker-compose.yml up -d
```

Verify services are running:
```bash
docker ps
```

You should see 3 containers: `redpanda`, `redpanda-console`, `mongodb`.

- **Redpanda Console** (topic inspector): http://localhost:8080
- **MongoDB**: localhost:27017

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Start the Producer (Terminal 1)

```bash
cd Faketrend-detection
python -m producer.kafka_producer
```

You'll see output like:
```
[2026-04-11 22:00:01] [INFO   ] [producer.kafka_producer] Producer started → topic 'social_stream' @ localhost:19092 (interval 200ms)
[2026-04-11 22:00:11] [INFO   ] [producer.kafka_producer] Produced 50 events (latest: user=user_0234 hashtag=#Python)
```

### Step 4: Start the Consumer (Terminal 2)

```bash
cd Faketrend-detection
python -m consumer.kafka_consumer
```

You'll see output like:
```
[2026-04-11 22:00:15] [INFO   ] [consumer.kafka_consumer] Consumer started — group 'fake_trend_consumer_group' → topic 'social_stream' @ localhost:19092
[2026-04-11 22:00:20] [INFO   ] [consumer.scorer] 🚩 FLAGGED — spike=0.00 bot=0.85 → suspicion=0.425
[2026-04-11 22:00:25] [INFO   ] [consumer.kafka_consumer] Processed 50 events (6 flagged) — latest: user=bot_003 score=0.425
```

### Step 5: Start the API Server (Terminal 3)

```bash
cd Faketrend-detection
python -m api.main
```

API available at:
- **Swagger docs**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Step 6: Query the API

```bash
# Trending hashtags (last 5 minutes)
curl http://localhost:8000/api/v1/trends

# Suspicious users
curl http://localhost:8000/api/v1/suspicious-users

# Flagged posts (paginated)
curl http://localhost:8000/api/v1/flagged-posts?limit=5
```

---

## 📊 Sample API Responses

### GET /api/v1/trends
```json
{
  "window_minutes": 5,
  "count": 5,
  "trends": [
    {"hashtag": "#SCAM_COIN", "count": 34},
    {"hashtag": "#Python", "count": 12},
    {"hashtag": "#AI", "count": 9},
    {"hashtag": "#FAKE_NEWS_ALERT", "count": 8},
    {"hashtag": "#Cloud", "count": 6}
  ]
}
```

### GET /api/v1/suspicious-users
```json
{
  "count": 3,
  "suspicious_users": [
    {"user_id": "bot_003", "avg_score": 0.712, "flag_count": 28},
    {"user_id": "bot_007", "avg_score": 0.685, "flag_count": 15},
    {"user_id": "bot_001", "avg_score": 0.543, "flag_count": 9}
  ]
}
```

### GET /api/v1/flagged-posts?limit=2
```json
{
  "count": 2,
  "skip": 0,
  "limit": 2,
  "flagged_posts": [
    {
      "event_id": "a1b2c3d4-...",
      "user_id": "bot_003",
      "timestamp": "2026-04-11T16:30:01.123456+00:00",
      "hashtag": "#SCAM_COIN",
      "text": "🔥 Don't miss this opportunity! Click the link NOW! 🔥",
      "likes": 2,
      "retweets": 0,
      "spike_score": 0.65,
      "bot_score": 0.85,
      "suspicion_score": 0.75,
      "is_flagged": true
    }
  ]
}
```

---

## ⚙️ Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:19092` | Redpanda/Kafka broker address |
| `KAFKA_TOPIC` | `social_stream` | Topic name for events |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `PRODUCER_INTERVAL_MS` | `200` | Milliseconds between events |
| `ANOMALY_PROBABILITY` | `0.15` | Fraction of anomalous events (0–1) |
| `WINDOW_SIZE_SECONDS` | `60` | Sliding window length |
| `SPIKE_THRESHOLD` | `5.0` | Multiplier over EMA to flag spike |
| `BOT_POST_THRESHOLD` | `10` | Posts per window to flag bot |
| `DUPLICATE_SIMILARITY_THRESHOLD` | `0.85` | Text similarity to flag duplicate |

---

## 🛑 Teardown

```bash
# Stop Python services: Ctrl+C in each terminal

# Stop and remove Docker containers + volumes
docker compose -f docker/docker-compose.yml down -v
```

---

# team collaboration 
HARIHARAN A
RAMKUMAR R
FAISAR A

## 📄 License

MIT
