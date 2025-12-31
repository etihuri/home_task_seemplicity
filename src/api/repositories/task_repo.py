from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from shared.models.task import Task, TaskStatus


class TaskRepository:
    """Repository for Task database operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        task_name: str,
        task_parameters: dict[str, Any],
    ) -> Task:
        """Create a new task in pending status."""
        task = Task(
            task_name=task_name,
            task_parameters=task_parameters,
            status=TaskStatus.PENDING,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: UUID) -> Task | None:
        """Get task by UUID."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_status(
        self,
        task_id: UUID,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Update task status and timestamps."""
        update_data: dict[str, Any] = {"status": status}
        if started_at:
            update_data["started_at"] = started_at
        if completed_at:
            update_data["completed_at"] = completed_at

        self.db.query(Task).filter(Task.id == task_id).update(
            update_data  # type: ignore[arg-type]
        )
        self.db.commit()

    def set_result(
        self,
        task_id: UUID,
        output: dict[str, Any],
    ) -> None:
        """Set task output and mark as completed."""
        self.db.query(Task).filter(Task.id == task_id).update(
            {
                "task_output": output,
                "status": TaskStatus.COMPLETED,
                "completed_at": datetime.now(UTC),
            }
        )
        self.db.commit()

    def set_error(
        self,
        task_id: UUID,
        error: str,
    ) -> None:
        """Set task error and mark as failed."""
        self.db.query(Task).filter(Task.id == task_id).update(
            {
                "error": error,
                "status": TaskStatus.FAILED,
                "completed_at": datetime.now(UTC),
            }
        )
        self.db.commit()
