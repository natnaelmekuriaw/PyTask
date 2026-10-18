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


def test_concurrent_ticks_create_one_task_per_occurrence(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    for _ in range(4):
        schedule_factory()
    barrier = Barrier(2)
    def tick() -> list[UUID]:
        with Session(isolated_engine) as session, session.begin():
            barrier.wait(timeout=5)
            return [task.id for task in dispatch_due(session)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(tick) for _ in range(2)]
        ids = [task_id for future in futures for task_id in future.result(timeout=10)]
    assert len(ids) == len(set(ids)) == 4
    with Session(isolated_engine) as session:
        assert session.scalar(select(func.count()).select_from(Task)) == 4
