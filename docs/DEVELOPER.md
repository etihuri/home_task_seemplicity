# Developer Guide

## Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Start Services

```bash
# Start everything (API, Worker, Redis, PostgreSQL)
docker compose up --build -d

# Check status
docker compose ps
```

### Run Locally (without Docker)

```bash
# Start only infrastructure
docker compose up -d postgres redis

# Install dependencies
uv sync --extra dev

# Run API (terminal 1)
PYTHONPATH=src uv run uvicorn api.main:app --reload

# Run Worker (terminal 2)
PYTHONPATH=src uv run celery -A worker.celery_app worker --loglevel=info
```

---

## API Examples

### Submit Tasks

**Sum:**
```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "sum", "a": 10, "b": 5}'
```

**File Hash:**
```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "file_hash", "content": "hello world", "algorithm": "sha256"}'
```

**Query LLM** (requires `ANTHROPIC_API_KEY` in `.env`):
```bash
curl -X POST http://localhost:8000/run-task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "query_llm", "prompt": "What is 2+2?", "max_tokens": 100}'
```

### Get Task Result

```bash
curl "http://localhost:8000/get-task-output?taskuuid=<UUID>"
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Debugging

### View Logs

```bash
# API logs
docker logs tasker-api -f

# Worker logs
docker logs tasker-worker -f

# All logs
docker compose logs -f
```

### Inspect Database

```bash
# Connect to PostgreSQL
docker exec -it tasker-postgres psql -U tasker -d tasker

# View all tasks
SELECT id, task_name, status, created_at FROM tasks ORDER BY created_at DESC;

# View pending tasks
SELECT * FROM tasks WHERE status = 'pending';

# View failed tasks with errors
SELECT id, task_name, error FROM tasks WHERE status = 'failed';
```

### Inspect Redis Cache

```bash
# Connect to Redis
docker exec -it tasker-redis redis-cli

# List cached tasks
KEYS task:*

# Get specific task cache
GET task:<UUID>

# Clear all cache
FLUSHALL
```

### View Metrics

```bash
curl http://localhost:8000/metrics | grep tasker_
```

---

## Testing

### Run Tests

```bash
# All tests
uv run pytest

# With coverage report
uv run pytest --cov-report=html
open htmlcov/index.html

# Specific test file
uv run pytest tests/api/test_tasks.py -v
```

### Linting & Type Checking

```bash
# Lint
uv run ruff check .

# Auto-fix
uv run ruff check --fix .

# Type check
uv run mypy --strict src/api src/worker src/shared
```

---

## Configuration

Create `.env` file (copy from `.env.example`):

```bash
# Required for LLM task
ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
DATABASE_URL=postgresql://tasker:tasker_secret@localhost:5432/tasker
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Task stuck in `pending` | Check worker logs: `docker logs tasker-worker` |
| Task stuck in `running` | Worker crashed. Restart: `docker compose restart worker` |
| LLM task fails | Check `ANTHROPIC_API_KEY` in `.env` |
| Connection refused | Ensure containers are healthy: `docker compose ps` |
| Import errors locally | Set `PYTHONPATH=src` before running |
