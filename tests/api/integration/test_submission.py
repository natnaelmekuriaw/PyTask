from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task

pytestmark = pytest.mark.integration


def test_submission_is_committed_before_its_location_can_be_read(database_client: TestClient, isolated_engine: Engine) -> None:
    response = database_client.post("/api/v1/tasks", json={"name": "math.add", "arguments": {"left": 1, "right": 2}})
    assert response.status_code == 201
    created = response.json()
    assert database_client.get(response.headers["location"]).json()["id"] == created["id"]
    with Session(isolated_engine) as session:
        task = session.get(Task, UUID(created["id"]))
        assert task is not None and task.status == "pending" and task.attempt_count == 0
        assert task.result is None


@pytest.mark.parametrize("payload,code", [
    ({"name": "missing.task", "arguments": {}}, "unknown_task"),
    ({"name": "math.add", "arguments": {"left": 1}}, "invalid_arguments"),
])
def test_domain_submission_errors_leave_the_queue_unchanged(database_client: TestClient, isolated_engine: Engine, payload: dict[str, object], code: str) -> None:
    response = database_client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 422 and response.json()["error"]["code"] == code
    with Session(isolated_engine) as session:
        assert session.scalar(select(func.count()).select_from(Task)) == 0


def test_explicit_http_execution_policy_is_stored(submit: Callable[..., dict[str, Any]], isolated_engine: Engine) -> None:
    created = submit(max_attempts=7, timeout_seconds=12, retry_base_seconds=2, retry_max_seconds=20)
    with Session(isolated_engine) as session:
        task = session.get(Task, UUID(created["id"]))
        assert task is not None
        assert (task.max_attempts, task.timeout_seconds, task.retry_base_seconds, task.retry_max_seconds) == (7, 12, 2, 20)


def test_commit_failure_returns_an_error_and_rolls_back_submission(database_client: TestClient, isolated_engine: Engine) -> None:
    def fail_commit(connection: object) -> None:
        raise OperationalError("COMMIT", {}, RuntimeError("forced failure"))
    event.listen(isolated_engine, "commit", fail_commit)
    try:
        response = database_client.post("/api/v1/tasks", json={"name": "math.add", "arguments": {"left": 1, "right": 2}})
    finally:
        event.remove(isolated_engine, "commit", fail_commit)
    assert response.status_code == 503 and "location" not in response.headers
    with Session(isolated_engine) as session:
        assert session.scalar(select(func.count()).select_from(Task)) == 0
