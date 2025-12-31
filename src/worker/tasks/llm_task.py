from typing import Any

import anthropic
from celery import Task as CeleryTask

from shared.config import get_settings
from worker.celery_app import celery_app
from worker.tasks.base import (
    update_task_completed,
    update_task_failed,
    update_task_running,
)

settings = get_settings()
TASK_NAME = "query_llm"


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(anthropic.APIConnectionError, anthropic.RateLimitError),
    max_retries=3,
    retry_backoff=True,
    acks_late=True,
)
def llm_task(
    self: CeleryTask,
    task_id: str,
    prompt: str,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """Query Claude API with a prompt."""
    start_time = update_task_running(task_id, task_name=TASK_NAME)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        # Extract response text
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        output = {
            "response": response_text,
            "model": message.model,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
        }

        update_task_completed(task_id, output, start_time=start_time, task_name=TASK_NAME)
        return output

    except Exception as e:
        update_task_failed(task_id, str(e), task_name=TASK_NAME)
        raise
