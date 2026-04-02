"""
Celery application for Codemail task queue management.
Handles distributed task processing and state tracking.
"""

import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis URL from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "codemail",
    broker=redis_url,
    backend=redis_url,
    include=["task_queue"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Process one task at a time
)
