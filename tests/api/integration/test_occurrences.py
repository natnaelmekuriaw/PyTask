from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from pytask_service.scheduling.service import Scheduler
from pytask_service.worker.service import Worker

pytestmark = pytest.mark.integration


def test_occurrence_lists_are_scoped_to_the_requested_schedule(database_client: TestClient, isolated_engine: Engine, schedule: Callable[..., dict[str, Any]]) -> None:
    first, second = schedule()["id"], schedule()["id"]
    assert len(Scheduler(isolated_engine).run_once()) == 2
    occurrences = database_client.get(f"/api/v1/schedules/{first}/tasks").json()
    assert len(occurrences["items"]) == 1 and occurrences["items"][0]["schedule_id"] == first
    filtered = database_client.get("/api/v1/tasks", params={"schedule_id": first}).json()
    assert filtered["items"] == occurrences["items"]
    assert database_client.get(f"/api/v1/schedules/{second}/tasks").json()["items"][0]["id"] != occurrences["items"][0]["id"]


def test_api_schedule_runs_through_scheduler_and_worker(database_client: TestClient, isolated_engine: Engine, schedule: Callable[..., dict[str, Any]]) -> None:
    definition = schedule()
    occurrence = Scheduler(isolated_engine).run_once()[0]
    worked = Worker(isolated_engine, "pytask_service.example_tasks:registry").run_once()
    assert worked is not None and worked.id == occurrence.id
    task = database_client.get(f"/api/v1/tasks/{worked.id}").json()
    assert task["status"] == "succeeded" and task["result"] == 3
    assert task["schedule_id"] == definition["id"]
    history = database_client.get(f"/api/v1/tasks/{worked.id}/attempts").json()
    assert [attempt["status"] for attempt in history["items"]] == ["succeeded"]
