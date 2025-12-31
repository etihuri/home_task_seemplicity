from celery import Celery
from celery.signals import setup_logging

from shared.config import get_settings
from shared.logging import setup_logging as setup_app_logging

settings = get_settings()


@setup_logging.connect  # type: ignore[untyped-decorator]
def configure_celery_logging(*args: object, **kwargs: object) -> None:
    """Configure Celery to use our structured logging."""
    setup_app_logging()

celery_app = Celery(
    "tasker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "worker.tasks.sum_task",
        "worker.tasks.llm_task",
        "worker.tasks.hash_task",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings
    worker_concurrency=settings.celery_concurrency,
    worker_prefetch_multiplier=1,
    # Task acknowledgment
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result backend
    result_expires=3600,
)
