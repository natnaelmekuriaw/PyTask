from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Task
from pytask_service.worker.claim import claim_next
from pytask_service.worker.finish import finish_task
from pytask_service.worker.outcome import TaskOutcome

pytestmark = pytest.mark.integration


def test_existing_tasks_have_an_empty_attempt_page_before_execution(database_client: TestClient, submit: Callable[..., dict[str, Any]]) -> None:
    task = submit()
    response = database_client.get(f"/api/v1/tasks/{task['id']}/attempts")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_after": None}


def test_attempt_history_paginates_failures_and_success_in_order(database_client: TestClient, isolated_engine: Engine, submit: Callable[..., dict[str, Any]]) -> None:
    task_id = UUID(submit()["id"])
    for outcome in [TaskOutcome.failure(ValueError("first")), TaskOutcome.success(3)]:
        with Session(isolated_engine) as session, session.begin():
            task = session.get(Task, task_id)
            assert task is not None
            task.available_at = database_now(session) - timedelta(seconds=1)
            claim = claim_next(session, "history-worker")
            assert claim is not None
        with Session(isolated_engine) as session, session.begin():
            finish_task(session, claim, outcome)
    first = database_client.get(f"/api/v1/tasks/{task_id}/attempts", params={"limit": 1}).json()
    second = database_client.get(f"/api/v1/tasks/{task_id}/attempts", params={"after": first["next_after"]}).json()
    assert [item["number"] for item in first["items"] + second["items"]] == [1, 2]
    assert [item["status"] for item in first["items"] + second["items"]] == ["failed", "succeeded"]
    assert second["next_after"] is None
