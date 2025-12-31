import hashlib
from typing import Any, Literal

from celery import Task as CeleryTask

from worker.celery_app import celery_app
from worker.tasks.base import (
    update_task_completed,
    update_task_failed,
    update_task_running,
)

TASK_NAME = "file_hash"


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    acks_late=True,
)
def hash_task(
    self: CeleryTask,
    task_id: str,
    content: str,
    algorithm: Literal["md5", "sha1", "sha256"] = "sha256",
) -> dict[str, Any]:
    """Calculate hash of content."""
    start_time = update_task_running(task_id, task_name=TASK_NAME)

    try:
        # Get the hash function
        hash_funcs = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
        }
        hash_func = hash_funcs[algorithm]

        # Calculate hash
        content_bytes = content.encode("utf-8")
        hash_value = hash_func(content_bytes).hexdigest()

        output = {
            "hash": hash_value,
            "algorithm": algorithm,
            "content_length": len(content_bytes),
        }

        update_task_completed(task_id, output, start_time=start_time, task_name=TASK_NAME)
        return output

    except Exception as e:
        update_task_failed(task_id, str(e), task_name=TASK_NAME)
        raise
