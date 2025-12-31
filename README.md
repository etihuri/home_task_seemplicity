# Tasker

Async task execution service with FastAPI and Celery.

## Quick Start

```bash
# Start all services
docker compose up --build -d

# Swagger UI
open http://localhost:8000/docs
```

## API Endpoints

- `POST /run-task` - Submit a task
- `GET /get-task-output?taskuuid=<uuid>` - Get task result
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Supported Tasks

- `sum` - Sum two numbers
- `query_llm` - Query Claude API
- `file_hash` - Calculate file hash (MD5/SHA1/SHA256)

## Documentation

- [Developer Guide](docs/DEVELOPER.md) - Setup, testing, debugging
- [Architecture & PRD](docs/PRD.md) - Design decisions, tech choices

## Production TODO

This is a development/demo setup. For production deployment, we would consider:
- Use Lambda/ECS as a worker
- Use managed database service (e.g., AWS RDS, Google Cloud SQL)
- Use managed Redis service (e.g., AWS ElastiCache, Redis Cloud) with persistence
