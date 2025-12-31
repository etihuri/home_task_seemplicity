from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from shared.models.task import Task, TaskStatus


class TestRunTask:
    """Tests for POST /run-task endpoint."""

    def test_run_sum_task_returns_uuid(self, client: TestClient) -> None:
        """Sum task submission returns a UUID."""
        response = client.post(
            "/run-task",
            json={
                "task_name": "sum",
                "a": 5,
                "b": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_uuid" in data
        assert len(data["task_uuid"]) == 36  # UUID format

    def test_run_query_llm_task_returns_uuid(self, client: TestClient) -> None:
        """LLM task submission returns a UUID."""
        response = client.post(
            "/run-task",
            json={
                "task_name": "query_llm",
                "prompt": "Hello",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_uuid" in data

    def test_run_file_hash_task_returns_uuid(self, client: TestClient) -> None:
        """File hash task submission returns a UUID."""
        response = client.post(
            "/run-task",
            json={
                "task_name": "file_hash",
                "content": "test",
                "algorithm": "sha256",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_uuid" in data

    def test_run_task_invalid_task_name_returns_422(self, client: TestClient) -> None:
        """Invalid task name returns 422."""
        response = client.post(
            "/run-task",
            json={
                "task_name": "invalid_task",
            },
        )

        assert response.status_code == 422

    def test_run_sum_task_missing_params_returns_422(self, client: TestClient) -> None:
        """Sum task with missing parameters returns 422."""
        response = client.post(
            "/run-task",
            json={
                "task_name": "sum",
                "a": 5,
                # missing "b"
            },
        )

        assert response.status_code == 422


class TestGetTaskOutput:
    """Tests for GET /get-task-output endpoint."""

    def test_get_task_output_pending(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Get output of pending task returns pending status."""
        # Create a pending task directly in DB
        task = Task(
            task_name="sum",
            task_parameters={"a": 1, "b": 2},
            status=TaskStatus.PENDING,
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(f"/get-task-output?taskuuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["task_output"] is None

    def test_get_task_output_completed(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Get output of completed task returns output."""
        task = Task(
            task_name="sum",
            task_parameters={"a": 1, "b": 2},
            status=TaskStatus.COMPLETED,
            task_output={"result": 3},
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(f"/get-task-output?taskuuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["task_output"] == {"result": 3}

    def test_get_task_output_failed(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Get output of failed task returns error."""
        task = Task(
            task_name="sum",
            task_parameters={"a": 1, "b": 2},
            status=TaskStatus.FAILED,
            error="Something went wrong",
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        response = client.get(f"/get-task-output?taskuuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    def test_get_task_output_not_found(self, client: TestClient) -> None:
        """Get output of non-existent task returns 404."""
        fake_uuid = uuid4()

        response = client.get(f"/get-task-output?taskuuid={fake_uuid}")

        assert response.status_code == 404


class TestHealthCheck:
    """Tests for GET /health endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Health check returns status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
