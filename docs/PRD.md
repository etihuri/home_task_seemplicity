# Tasker - Product Requirements & Architecture

## Overview

Tasker is an asynchronous task execution service. Clients submit tasks via REST API and poll for results later (fire-and-forget pattern).

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│     API     │     │   (Queue)   │     │   Worker    │
└──────┬──────┘     └─────────────┘     └──────┬──────┘
       │                                       │
       └──────────▶ PostgreSQL ◀───────────────┘
                    (Storage)
```

### Request Flow

1. Client submits task via `POST /run-task`
2. API validates request, saves to PostgreSQL (status: `pending`), returns UUID
3. API dispatches task to Redis queue
4. Celery Worker picks up task, updates status to `running`
5. Worker executes task, saves result to DB + caches in Redis
6. Client polls `GET /get-task-output` to retrieve result

---

## Technology Choices

### Why FastAPI?

| Requirement | FastAPI Solution |
|-------------|------------------|
| Async I/O | Native async/await support |
| API Documentation | Auto-generated Swagger UI at `/docs` |
| Validation | Pydantic models with type hints |
| Performance | One of the fastest Python frameworks |

**Alternative considered:** Flask - simpler but lacks native async and auto-docs.

### Why Celery + Redis?

| Requirement | Solution |
|-------------|----------|
| Background tasks | Celery is Python's standard task queue |
| Message broker | Redis is fast and also serves as cache |
| Scaling | Easy to add workers: `--scale worker=3` |
| Reliability | Built-in retry with exponential backoff |

**Alternative considered:** RQ - simpler but fewer features. RabbitMQ - more robust but adds complexity.

### Why PostgreSQL?

| Requirement | Solution |
|-------------|----------|
| Data integrity | ACID compliance for task state |
| Flexible data | Native JSONB for task parameters/output |
| Query performance | Indexes on status, created_at |
| Production ready | Battle-tested, widely supported |

**Alternative considered:** MongoDB - good for JSON but overkill for this use case.

### Why Redis for Caching?

| Requirement | Solution |
|-------------|----------|
| Already present | Using as Celery broker |
| Speed | Sub-millisecond reads |
| Expiration | TTL support (default: 1 hour) |

**Cache strategy:** Cache-aside pattern - check cache first, fallback to DB.

---

## Code Architecture

### Clean Architecture

```
src/
├── api/
│   ├── routers/      → HTTP layer (endpoints)
│   ├── services/     → Business logic
│   ├── repositories/ → Database access
│   └── schemas/      → Request/Response models
├── worker/
│   └── tasks/        → Celery task implementations
└── shared/
    ├── models/       → SQLAlchemy ORM models
    ├── database.py   → DB connection
    └── cache.py      → Redis wrapper
```

**Benefits:**
- Testable: Mock any layer independently
- Maintainable: Clear separation of concerns
- Flexible: Swap DB without changing business logic

### Discriminated Unions for API

Swagger shows exact fields per task type:

```json
// Generic approach (bad UX)
{"task_name": "sum", "task_parameters": {"a": 1, "b": 2}}

// Discriminated union (good UX)
{"task_name": "sum", "a": 1, "b": 2}
```

---

## Database Schema

```sql
CREATE TABLE tasks (
    id              UUID PRIMARY KEY,
    task_name       VARCHAR(100) NOT NULL,
    task_parameters JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL,  -- pending/running/completed/failed
    task_output     JSONB,
    error           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE
);

-- Indexes for common queries
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

---

## Observability

### Structured Logging

JSON format with correlation IDs:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "task_id": "abc-123",
  "message": "Task completed",
  "duration_ms": 45
}
```

### Prometheus Metrics

- `tasker_tasks_submitted_total{task_name}` - Tasks submitted
- `tasker_tasks_completed_total{task_name, status}` - Tasks completed
- `tasker_task_duration_seconds{task_name}` - Execution time histogram

---

## Scaling

### Horizontal (more workers)

```bash
docker compose up -d --scale worker=3
```

### Vertical (more concurrency per worker)

```bash
CELERY_CONCURRENCY=8
```

### Database Connection Pool

```python
engine = create_engine(
    url,
    pool_size=10,      # Base connections
    max_overflow=20,   # Extra under load
)
```

---

## Quality Assurance

| Check | Tool | Threshold |
|-------|------|-----------|
| Linting | ruff | Zero errors |
| Type checking | mypy --strict | Zero errors |
| Test coverage | pytest-cov | 80% minimum |
| CI/CD | GitHub Actions | All checks pass |

---

## Out of Scope

- Authentication/Authorization
- Rate limiting
- Task cancellation/priortzation
- Database migrations (Alembic)
