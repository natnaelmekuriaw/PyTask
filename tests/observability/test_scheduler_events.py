import logging

import pytest
from sqlalchemy.engine import Engine

from pytask_service.scheduling.service import Scheduler
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_dispatch_events_reference_the_occurrence_without_arguments(
    isolated_engine: Engine, event_records: list[logging.LogRecord],
) -> None:
    database = MonitoringDatabase(isolated_engine)
    schedule_id = database.schedule(arguments={"secret": "payload"})
    tasks = Scheduler(isolated_engine).run_once()
    assert len(tasks) == 1
    events = [r for r in event_records if r.msg == "schedule.dispatched"]
    assert len(events) == 1
    assert events[0].event_fields["schedule_id"] == str(schedule_id)
    assert events[0].event_fields["task_id"] == str(tasks[0].id)
    assert events[0].event_fields["created"] is True
    assert "secret" not in repr(events[0].event_fields)
