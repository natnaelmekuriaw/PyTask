import logging
from uuid import uuid4

from pytask_service.observability.context import bind_context
from pytask_service.observability.events import log_event


def test_events_inherit_context_without_losing_explicit_fields(
    event_records: list[logging.LogRecord],
) -> None:
    task_id = uuid4()
    with bind_context(request_id="request", task_id="outer"):
        log_event(logging.getLogger("pytask_service.test"), "task.claimed", task_id=task_id)
    assert len(event_records) == 1
    assert event_records[0].event_fields == {
        "request_id": "request", "task_id": str(task_id),
    }
