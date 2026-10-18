from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Schedule

pytestmark = pytest.mark.integration


def test_schedule_pages_resolve_timestamp_ties(database_client: TestClient, isolated_engine: Engine, schedule: Callable[..., dict[str, Any]]) -> None:
    ids = [schedule()["id"] for _ in range(3)]
    with Session(isolated_engine) as session, session.begin():
        session.execute(update(Schedule).values(created_at=datetime(2026, 1, 1, tzinfo=UTC)))
    first = database_client.get("/api/v1/schedules", params={"limit": 2}).json()
    last = database_client.get("/api/v1/schedules", params={"cursor": first["next_cursor"]}).json()
    assert [item["id"] for item in first["items"] + last["items"]] == sorted(ids, reverse=True)
    assert last["next_cursor"] is None
