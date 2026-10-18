from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task

pytestmark = pytest.mark.integration


def test_task_pages_handle_equal_creation_timestamps(database_client: TestClient, isolated_engine: Engine, submit: Callable[..., dict[str, Any]]) -> None:
    ids = [submit()["id"] for _ in range(3)]
    with Session(isolated_engine) as session, session.begin():
        session.execute(update(Task).values(created_at=datetime(2026, 1, 1, tzinfo=UTC)))
    first = database_client.get("/api/v1/tasks", params={"limit": 2}).json()
    second = database_client.get("/api/v1/tasks", params={"limit": 2, "cursor": first["next_cursor"]}).json()
    assert [item["id"] for item in first["items"] + second["items"]] == sorted(ids, reverse=True)
    assert second["next_cursor"] is None


def test_newer_insertions_do_not_repeat_or_shift_older_pages(database_client: TestClient, submit: Callable[..., dict[str, Any]]) -> None:
    original = {submit()["id"] for _ in range(3)}
    first = database_client.get("/api/v1/tasks", params={"limit": 1}).json()
    newest = submit()["id"]
    remaining = database_client.get("/api/v1/tasks", params={"limit": 100, "cursor": first["next_cursor"]}).json()
    seen = [item["id"] for item in first["items"] + remaining["items"]]
    assert set(seen) == original and len(seen) == 3 and newest not in seen


def test_task_filters_combine_status_and_registered_name(database_client: TestClient, isolated_engine: Engine, submit: Callable[..., dict[str, Any]]) -> None:
    succeeded = submit()["id"]
    pending = submit()["id"]
    submit(name="demo.greet", arguments={"name": "reader"})
    with Session(isolated_engine) as session, session.begin():
        session.execute(update(Task).where(Task.id == UUID(succeeded)).values(status="succeeded", result=3))
    page = database_client.get("/api/v1/tasks", params={"status": "pending", "name": "math.add"}).json()
    assert [item["id"] for item in page["items"]] == [pending]
