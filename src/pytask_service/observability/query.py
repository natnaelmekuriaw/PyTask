from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import DateTime, func, select, true
from sqlalchemy.sql import Select

from pytask_service.observability.attempts import outcome_aggregate, retry_aggregate
from pytask_service.observability.queue import queue_aggregate
from pytask_service.observability.schedules import schedule_aggregate
from pytask_service.observability.timings import execution_aggregate, wait_aggregate
from pytask_service.observability.window import ObservationWindow


def snapshot_statement(window: ObservationWindow) -> Select[Any]:
    now = func.statement_timestamp(type_=DateTime(timezone=True))
    since = now - timedelta(seconds=window.seconds)
    sections = [
        queue_aggregate(now),
        outcome_aggregate(since, now),
        retry_aggregate(since, now),
        execution_aggregate(since, now),
        wait_aggregate(since, now),
        schedule_aggregate(now),
    ]
    combined = sections[0]
    source = combined.join(sections[1], true())
    for section in sections[2:]:
        source = source.join(section, true())
    return select(
        now.label("observed_at"),
        *(column for section in sections for column in section.c),
    ).select_from(source)
