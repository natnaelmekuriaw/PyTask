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
