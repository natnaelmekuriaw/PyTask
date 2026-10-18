from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.db.models import Task
from pytask_service.worker.claim import claim_next

pytestmark = pytest.mark.integration


def test_relative_http_delay_uses_database_time(
    submit: Callable[..., dict[str, Any]], isolated_engine: Engine
) -> None:
    with Session(isolated_engine) as session:
        before = database_now(session)
    created = submit(delay_seconds=30)
    with Session(isolated_engine) as session, session.begin():
        after = database_now(session)
        task = session.get(Task, UUID(created["id"]))
        assert task is not None
        assert (
            before + timedelta(seconds=30)
            <= task.available_at
            <= after + timedelta(seconds=30)
        )
        assert claim_next(session, "early-worker") is None


def test_absolute_http_timestamp_preserves_the_requested_instant(
    submit: Callable[..., dict[str, Any]], isolated_engine: Engine
) -> None:
    requested = "2099-01-01T12:00:00+03:00"
    created = submit(run_at=requested)
    with Session(isolated_engine) as session:
        task = session.get(Task, UUID(created["id"]))
        assert task is not None and task.available_at == datetime.fromisoformat(
            requested
        )
