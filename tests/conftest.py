from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.dependencies import get_cache, get_db
from api.main import app
from shared.database import Base

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock Redis cache."""
    cache = MagicMock()
    cache.get.return_value = None
    cache.get_raw.return_value = None
    cache.set.return_value = None
    cache.set_raw.return_value = None
    cache.ping.return_value = True
    return cache


@pytest.fixture
def mock_celery() -> Generator[MagicMock, None, None]:
    """Mock Celery task dispatch."""
    with patch("worker.tasks.sum_task.sum_task.delay") as mock_sum, \
         patch("worker.tasks.llm_task.llm_task.delay") as mock_llm, \
         patch("worker.tasks.hash_task.hash_task.delay") as mock_hash:
        yield {
            "sum": mock_sum,
            "llm": mock_llm,
            "hash": mock_hash,
        }


@pytest.fixture
def client(
    db_session: Session,
    mock_cache: MagicMock,
    mock_celery: dict[str, Any],
) -> Generator[TestClient, None, None]:
    """Create test client with mocked dependencies."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_cache() -> MagicMock:
        return mock_cache

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = override_get_cache

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
