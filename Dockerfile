# Multi-stage build for Tasker API and Worker
FROM python:3.11-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Set PYTHONPATH for src layout
ENV PYTHONPATH=/app/src

# API target
FROM base AS api
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker target
FROM base AS worker
CMD ["uv", "run", "celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
