from datetime import datetime

import pytest

from pytask_service.registry import TaskRegistry, UnknownTaskError
from pytask_service.scheduling.definitions import (
    create_schedule,
    validate_schedule_name,
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
