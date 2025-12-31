from celery import Task as CeleryTask

from worker.celery_app import celery_app
from worker.tasks.base import (
    update_task_completed,
    update_task_failed,
    update_task_running,
)

TASK_NAME = "sum"


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    acks_late=True,
)
def sum_task(
    self: CeleryTask,
    task_id: str,
    a: int | float,
    b: int | float,
) -> dict[str, int | float]:
    """Sum two numbers."""
    start_time = update_task_running(task_id, task_name=TASK_NAME)

    try:
        result = a + b
        output = {"result": result}
        update_task_completed(task_id, output, start_time=start_time, task_name=TASK_NAME)
        return output
    except Exception as e:
        update_task_failed(task_id, str(e), task_name=TASK_NAME)
        raise
