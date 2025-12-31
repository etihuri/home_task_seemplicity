import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from api.routers import metrics, tasks
from shared.logging import get_logger, request_id_ctx, setup_logging
from shared.metrics import http_request_duration_seconds, http_requests_total

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    logger.info("Tasker API starting up")
    yield
    logger.info("Tasker API shutting down")


app = FastAPI(
    title="Tasker API",
    description="Async task execution service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log all requests with timing and correlation ID."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx.set(request_id)

    # Record start time
    start_time = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Record metrics
    endpoint = request.url.path
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code,
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration_ms / 1000)

    # Log request (skip /health and /metrics to reduce noise)
    if request.url.path not in ["/health", "/metrics"]:
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# Include routers
app.include_router(tasks.router)
app.include_router(metrics.router)


