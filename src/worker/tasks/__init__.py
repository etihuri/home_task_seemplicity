from typing import Any


def dispatch_task(
    task_id: str,
    task_name: str,
    task_parameters: dict[str, Any],
) -> None:
    """Dispatch task to appropriate Celery worker."""
    if task_name == "sum":
        from worker.tasks.sum_task import sum_task

        sum_task.delay(task_id, **task_parameters)
    elif task_name == "query_llm":
        from worker.tasks.llm_task import llm_task

        llm_task.delay(task_id, **task_parameters)
    elif task_name == "file_hash":
        from worker.tasks.hash_task import hash_task

        hash_task.delay(task_id, **task_parameters)
    else:
        raise ValueError(f"Unknown task: {task_name}")
