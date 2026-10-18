from datetime import datetime

import pytest

from pytask_service.registry import TaskRegistry, UnknownTaskError
from pytask_service.scheduling.definitions import (
    create_schedule,
    validate_schedule_name,
    list_schedules,
    list_occurrences,
)


@pytest.mark.parametrize("name", ["", "Has spaces", "Upper", "../name", "a" * 129])
def test_schedule_names_reject_ambiguous_identifiers(name: str) -> None:
    with pytest.raises(ValueError, match="Schedule name"):
        validate_schedule_name(name)


def test_unknown_handlers_are_rejected_before_database_access() -> None:
    with pytest.raises(UnknownTaskError):
        create_schedule(
            None, TaskRegistry(), "example", "missing", {}, interval_seconds=60
        )


@pytest.mark.parametrize("limit", [0, -1, True, 1001])
def test_listing_rejects_unbounded_or_invalid_limits(limit: int) -> None:
    from uuid import uuid4
    with pytest.raises(ValueError, match="Limit"):
        list_schedules(None, limit=limit)
    with pytest.raises(ValueError, match="Limit"):
        list_occurrences(None, uuid4(), limit=limit)


def test_schedule_start_must_be_timezone_aware() -> None:
    registry = TaskRegistry()
    registry.register("noop", lambda: None)
    with pytest.raises(ValueError, match="UTC offset"):
        create_schedule(
            None,
            registry,
            "example",
            "noop",
            {},
            interval_seconds=60,
            start_at=datetime(2027, 1, 1),
        )
