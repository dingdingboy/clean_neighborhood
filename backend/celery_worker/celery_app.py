from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "violation_reporter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "celery_worker.tasks.media_pipeline",
        "celery_worker.tasks.analysis",
        "celery_worker.tasks.submission",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Task routing (optional - for scaling)
celery_app.conf.task_routes = {
    "celery_worker.tasks.media_pipeline.*": {"queue": "media"},
    "celery_worker.tasks.analysis.*": {"queue": "analysis"},
    "celery_worker.tasks.submission.*": {"queue": "submission"},
}
