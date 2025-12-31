from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import Cache, DbSession
from api.schemas.task import RunTaskRequest, RunTaskResponse, TaskOutputResponse
from api.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(tags=["tasks"])


@router.post("/run-task", response_model=RunTaskResponse)
async def run_task(
    request: RunTaskRequest,
    db: DbSession,
    cache: Cache,
) -> RunTaskResponse:
    """
    Submit a task for async execution.

    Returns immediately with a task UUID.
    """
    service = TaskService(db, cache)
    task_uuid = service.create_task(request)
    return RunTaskResponse(task_uuid=task_uuid)


@router.get("/get-task-output", response_model=TaskOutputResponse)
async def get_task_output(
    taskuuid: Annotated[UUID, Query(description="UUID of the task")],
    db: DbSession,
    cache: Cache,
) -> TaskOutputResponse:
    """
    Get the output of a task by UUID.

    Returns task status, output (if completed), or error (if failed).
    """
    service = TaskService(db, cache)

    try:
        return service.get_task_output(taskuuid)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
