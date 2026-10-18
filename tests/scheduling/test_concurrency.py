from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Schedule, Task
from pytask_service.scheduling.dispatch import dispatch_due

pytestmark = pytest.mark.integration


def test_dispatch_skips_a_schedule_locked_by_another_scheduler(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    locked_id, free_id = schedule_factory(), schedule_factory()
    with Session(isolated_engine) as holder, holder.begin():
        holder.scalar(select(Schedule).where(Schedule.id == locked_id).with_for_update())
        with Session(isolated_engine) as contender, contender.begin():
            tasks = dispatch_due(contender)
            assert [task.schedule_id for task in tasks] == [free_id]
    with Session(isolated_engine) as session, session.begin():
        assert [task.schedule_id for task in dispatch_due(session)] == [locked_id]
