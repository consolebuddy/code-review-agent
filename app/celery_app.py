from celery import Celery
from .config import get_settings

settings = get_settings()

celery = Celery(
    "code_review_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_hijack_root_logger=False,
)
