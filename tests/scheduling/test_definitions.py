from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.policy import TaskPolicy
from pytask_service.scheduling.definitions import get_schedule, list_schedules, set_paused

pytestmark = pytest.mark.integration


def test_created_schedule_keeps_arguments_and_execution_policy(isolated_engine: Engine, schedule_factory: Callable[..., UUID]) -> None:
    schedule_id = schedule_factory(policy=TaskPolicy(5, 12, 2, 20))
    with Session(isolated_engine) as session:
        schedule = get_schedule(session, schedule_id)
        assert schedule is not None
        assert schedule.arguments == {"left": 1, "right": 2}
        assert (schedule.max_attempts, schedule.timeout_seconds, schedule.retry_base_seconds, schedule.retry_max_seconds) == (5, 12, 2, 20)
        assert schedule.last_scheduled_for is None
        assert not schedule.paused
