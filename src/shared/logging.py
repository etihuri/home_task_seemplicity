import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from shared.config import get_settings

# Context variables for request/task tracing
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
task_id_ctx: ContextVar[str | None] = ContextVar("task_id", default=None)


class JSONFormatter(logging.Formatter):
    """JSON log formatter with context variables."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables if present
        if request_id := request_id_ctx.get():
            log_data["request_id"] = request_id

        if task_id := task_id_ctx.get():
            log_data["task_id"] = task_id

        # Add extra fields from record
        if hasattr(record, "task_name"):
            log_data["task_name"] = record.task_name
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable log formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        request_id = request_id_ctx.get() or "-"
        task_id = task_id_ctx.get() or "-"

        base = (
            f"{timestamp} [{record.levelname}] [{request_id}] [{task_id}] "
            f"{record.name}: {record.getMessage()}"
        )

        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()

    # Determine log level
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Choose formatter based on environment
    formatter = JSONFormatter() if settings.log_format == "json" else TextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
