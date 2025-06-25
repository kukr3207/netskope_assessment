# app/config.py
import os

# PostgreSQL URL for SQLAlchemy
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@db:5432/triage_service"
)

# Directory where your JSON docs live
DATA_DIR = os.getenv("DATA_DIR", "data")

# (Optional) add more settings here, e.g. SLACK_WEBHOOK_URL, METRICS_NAMESPACE, etc.
