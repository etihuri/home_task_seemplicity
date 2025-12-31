from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from api.repositories.task_repo import TaskRepository
from api.schemas.task import (
    FileHashTaskRequest,
    QueryLLMTaskRequest,
    SumTaskRequest,
    TaskOutputResponse,
)
from shared.cache import RedisCache
from shared.logging import get_logger
from shared.metrics import tasks_submitted_total
from shared.models.task import Task, TaskStatus

logger = get_logger(__name__)

# Valid task names
VALID_TASK_NAMES = {"sum", "query_llm", "file_hash"}


class TaskNotFoundError(Exception):
    """Raised when task is not found."""

    pass


class TaskService:
    """Business logic for task operations."""

    def __init__(self, db: Session, cache: RedisCache) -> None:
        self.repo = TaskRepository(db)
        self.cache = cache

    def create_task(
        self,
        request: SumTaskRequest | QueryLLMTaskRequest | FileHashTaskRequest,
    ) -> UUID:
        """Create a new task and dispatch to worker."""
        task_name = request.task_name

        # Validate task name before creating DB record
        if task_name not in VALID_TASK_NAMES:
            raise ValueError(f"Unknown task name: {task_name}. Valid tasks: {VALID_TASK_NAMES}")

        # Extract parameters based on task type
        task_parameters: dict[str, Any]
        if isinstance(request, SumTaskRequest):
            task_parameters = {"a": request.a, "b": request.b}
        elif isinstance(request, QueryLLMTaskRequest):
            task_parameters = {"prompt": request.prompt, "max_tokens": request.max_tokens}
        elif isinstance(request, FileHashTaskRequest):
            task_parameters = {"content": request.content, "algorithm": request.algorithm}
        else:
            raise ValueError(f"Unknown request type: {type(request)}")

        # Create task in DB
        task = self.repo.create(
            task_name=task_name,
            task_parameters=task_parameters,
        )

        # Record metric
        tasks_submitted_total.labels(task_name=task_name).inc()

        # Dispatch to Celery worker with error handling
        try:
            self._dispatch_task(task)
        except Exception as e:
            logger.error(
                f"Failed to dispatch task {task.id} to Celery: {e}",
                exc_info=True,
            )
            # Mark task as failed since it can't be processed
            self.repo.set_error(
                task_id=task.id,
                error=f"Failed to dispatch task to worker: {str(e)}",
            )
            raise

        return task.id

    def _dispatch_task(self, task: Task) -> None:
        """Send task to Celery worker."""
        # Import here to avoid circular imports
        from worker.tasks import dispatch_task

        dispatch_task(
            task_id=str(task.id),
            task_name=task.task_name,
            task_parameters=task.task_parameters,
        )

    def get_task_output(self, task_uuid: UUID) -> TaskOutputResponse:
        """Get task output, checking cache first."""
        # Check cache for completed tasks - cache stores full response
        cache_key = f"response:{task_uuid}"
        cached_response = self.cache.get_raw(cache_key)
        if cached_response:
            # Cache hit - return cached response directly without DB query
            # Convert ISO format strings back to datetime objects
            if isinstance(cached_response.get("created_at"), str):
                cached_response["created_at"] = datetime.fromisoformat(
                    cached_response["created_at"]
                )
            completed_at = cached_response.get("completed_at")
            if completed_at and isinstance(completed_at, str):
                cached_response["completed_at"] = datetime.fromisoformat(completed_at)
            if isinstance(cached_response.get("task_uuid"), str):
                cached_response["task_uuid"] = UUID(cached_response["task_uuid"])
            return TaskOutputResponse(**cached_response)

        # Fetch from database
        task = self.repo.get_by_id(task_uuid)
        if not task:
            raise TaskNotFoundError(f"Task {task_uuid} not found")

        # Build response
        response = TaskOutputResponse(
            task_uuid=task.id,
            status=task.status,
            task_output=task.task_output,
            error=task.error,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

        # Cache completed task output as full response for future requests
        if task.status == TaskStatus.COMPLETED and task.task_output:
            # Cache the full response dict for faster retrieval
            cache_data = {
                "task_uuid": str(task.id),
                "status": task.status,
                "task_output": task.task_output,
                "error": task.error,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
            self.cache.set_raw(cache_key, cache_data)

        return response
