import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from api.repositories.task_repo import TaskRepository
from shared.cache import cache
from shared.database import SessionLocal
from shared.logging import get_logger, setup_logging, task_id_ctx
from shared.metrics import task_duration_seconds, tasks_completed_total
from shared.models.task import TaskStatus

# Initialize logging for worker
setup_logging()
logger = get_logger(__name__)


def update_task_running(task_id: str, task_name: str | None = None) -> float:
    """Mark task as running. Returns start time for duration calculation."""
    task_id_ctx.set(task_id)
    start_time = time.perf_counter()

    logger.info(
        "Task started",
        extra={"task_name": task_name or "unknown"},
    )

    db = SessionLocal()
    try:
        repo = TaskRepository(db)
        repo.update_status(
            task_id=UUID(task_id),
            status=TaskStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
    finally:
        db.close()

    return start_time


def update_task_completed(
    task_id: str,
    output: dict[str, Any],
    start_time: float | None = None,
    task_name: str | None = None,
) -> None:
    """Mark task as completed with output."""
    duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else None
    name = task_name or "unknown"

    # Record metrics
    tasks_completed_total.labels(task_name=name, status="completed").inc()
    if duration_ms:
        task_duration_seconds.labels(task_name=name).observe(duration_ms / 1000)

    logger.info(
        "Task completed",
        extra={
            "task_name": name,
            "duration_ms": round(duration_ms, 2) if duration_ms else None,
        },
    )

    db = SessionLocal()
    try:
        repo = TaskRepository(db)
        repo.set_result(task_id=UUID(task_id), output=output)
    finally:
        db.close()

    # Cache the result
    cache.set(task_id, output)


def update_task_failed(
    task_id: str,
    error: str,
    task_name: str | None = None,
) -> None:
    """Mark task as failed with error."""
    name = task_name or "unknown"

    # Record metrics
    tasks_completed_total.labels(task_name=name, status="failed").inc()

    logger.error(
        "Task failed",
        extra={
            "task_name": name,
        },
    )

    db = SessionLocal()
    try:
        repo = TaskRepository(db)
        repo.set_error(task_id=UUID(task_id), error=error)
    finally:
        db.close()
