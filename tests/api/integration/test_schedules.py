from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Schedule

pytestmark = pytest.mark.integration


def test_schedule_creation_uses_the_existing_definition_service(database_client: TestClient, isolated_engine: Engine) -> None:
    response = database_client.post("/api/v1/schedules", json={"name": "report", "task_name": "math.add", "arguments": {"left": 1, "right": 2}, "interval_seconds": 60, "paused": True, "max_attempts": 5})
    assert response.status_code == 201
    assert database_client.get(response.headers["location"]).json() == response.json()
    with Session(isolated_engine) as session:
        definition = session.get(Schedule, UUID(response.json()["id"]))
        assert definition is not None and definition.paused and definition.max_attempts == 5
