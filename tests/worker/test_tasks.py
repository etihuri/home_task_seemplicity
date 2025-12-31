import hashlib
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_worker_deps():
    """Mock database and cache for worker tasks."""
    with patch("worker.tasks.base.SessionLocal") as mock_session_local, \
         patch("worker.tasks.base.cache") as mock_cache:
        # Setup mock session as context manager
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_local.return_value.__exit__ = MagicMock(return_value=False)

        yield {
            "session_local": mock_session_local,
            "session": mock_session,
            "cache": mock_cache,
        }


class TestSumTask:
    """Tests for sum_task worker."""

    def test_sum_task_integers(self, mock_worker_deps: dict) -> None:
        """Sum task correctly adds two integers."""
        from worker.tasks.sum_task import sum_task

        # Use keyword args only - Celery injects self for bound tasks
        result = sum_task(task_id="task-123", a=5, b=3)

        assert result == {"result": 8}

    def test_sum_task_floats(self, mock_worker_deps: dict) -> None:
        """Sum task correctly adds two floats."""
        from worker.tasks.sum_task import sum_task

        result = sum_task(task_id="task-456", a=2.5, b=3.5)

        assert result == {"result": 6.0}

    def test_sum_task_negative_numbers(self, mock_worker_deps: dict) -> None:
        """Sum task correctly handles negative numbers."""
        from worker.tasks.sum_task import sum_task

        result = sum_task(task_id="task-789", a=-10, b=5)

        assert result == {"result": -5}

    def test_sum_task_updates_db_status(self, mock_worker_deps: dict) -> None:
        """Sum task updates database status to completed."""
        from worker.tasks.sum_task import sum_task

        sum_task(task_id="task-123", a=1, b=2)

        # Verify session.query was called (status updates)
        mock_worker_deps["session"].query.assert_called()


class TestHashTask:
    """Tests for hash_task worker."""

    def test_hash_task_sha256(self, mock_worker_deps: dict) -> None:
        """Hash task correctly calculates SHA256."""
        from worker.tasks.hash_task import hash_task

        content = "hello world"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        result = hash_task(task_id="task-123", content=content, algorithm="sha256")

        assert result["hash"] == expected_hash
        assert result["algorithm"] == "sha256"
        assert result["content_length"] == len(content.encode())

    def test_hash_task_md5(self, mock_worker_deps: dict) -> None:
        """Hash task correctly calculates MD5."""
        from worker.tasks.hash_task import hash_task

        content = "test content"
        expected_hash = hashlib.md5(content.encode()).hexdigest()

        result = hash_task(task_id="task-456", content=content, algorithm="md5")

        assert result["hash"] == expected_hash
        assert result["algorithm"] == "md5"

    def test_hash_task_sha1(self, mock_worker_deps: dict) -> None:
        """Hash task correctly calculates SHA1."""
        from worker.tasks.hash_task import hash_task

        content = "sha1 test"
        expected_hash = hashlib.sha1(content.encode()).hexdigest()

        result = hash_task(task_id="task-789", content=content, algorithm="sha1")

        assert result["hash"] == expected_hash
        assert result["algorithm"] == "sha1"

    def test_hash_task_empty_content(self, mock_worker_deps: dict) -> None:
        """Hash task handles empty content."""
        from worker.tasks.hash_task import hash_task

        content = ""
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        result = hash_task(task_id="task-empty", content=content, algorithm="sha256")

        assert result["hash"] == expected_hash
        assert result["content_length"] == 0

    def test_hash_task_caches_result(self, mock_worker_deps: dict) -> None:
        """Hash task caches result after completion."""
        from worker.tasks.hash_task import hash_task

        hash_task(task_id="task-123", content="test", algorithm="sha256")

        # Verify cache.set was called
        mock_worker_deps["cache"].set.assert_called()
