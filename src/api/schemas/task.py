from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# Task-specific request schemas
class SumTaskRequest(BaseModel):
    """Request for sum task."""

    task_name: Literal["sum"] = Field(default="sum", description="Task type")
    a: int | float = Field(..., description="First number", examples=[5])
    b: int | float = Field(..., description="Second number", examples=[3])


class QueryLLMTaskRequest(BaseModel):
    """Request for query_llm task."""

    task_name: Literal["query_llm"] = Field(default="query_llm", description="Task type")
    prompt: str = Field(
        ..., min_length=1, description="Prompt to send to Claude", examples=["What is 2+2?"]
    )
    max_tokens: int = Field(default=1024, ge=1, le=4096, description="Maximum tokens in response")


class FileHashTaskRequest(BaseModel):
    """Request for file_hash task."""

    task_name: Literal["file_hash"] = Field(default="file_hash", description="Task type")
    content: str = Field(..., min_length=1, description="Content to hash", examples=["hello world"])
    algorithm: Literal["md5", "sha1", "sha256"] = Field(
        default="sha256",
        description="Hash algorithm to use",
    )


# Discriminated union - Swagger will show different fields per task_name
RunTaskRequest = Annotated[
    SumTaskRequest | QueryLLMTaskRequest | FileHashTaskRequest,
    Field(discriminator="task_name"),
]


class RunTaskResponse(BaseModel):
    """Response for POST /run-task."""

    task_uuid: UUID = Field(..., description="Unique identifier for the task")


class TaskOutputResponse(BaseModel):
    """Response for GET /get-task-output."""

    task_uuid: UUID
    status: Literal["pending", "running", "completed", "failed"]
    task_output: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
