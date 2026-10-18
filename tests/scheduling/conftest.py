from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.clock import database_now
from pytask_service.example_tasks import registry
from pytask_service.policy import TaskPolicy
from pytask_service.scheduling.definitions import create_schedule
from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.fixture
def schedule_factory(isolated_engine: Engine) -> Callable[..., UUID]:
    def create(
        *,
        name: str | None = None,
        start_at: datetime | None = None,
        interval_seconds: int = 60,
        policy: TaskPolicy | None = None,
        paused: bool = False,
    ) -> UUID:
        with Session(isolated_engine) as session, session.begin():
            schedule = create_schedule(
                session,
                registry,
                name or f"schedule-{uuid4().hex}",
                "math.add",
                {"left": 1, "right": 2},
                interval_seconds=interval_seconds,
                start_at=start_at or database_now(session) - timedelta(seconds=1),
                policy=policy,
                paused=paused,
            )
            schedule_id = schedule.id
        return schedule_id

    return create
