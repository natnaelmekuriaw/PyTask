import logging
import math
from datetime import datetime
from uuid import UUID

from pytask_service.observability.context import current_context

EVENT_FIELDS = frozenset(
    {
        "task_id",
        "attempt_id",
        "attempt_number",
        "worker_id",
        "schedule_id",
        "request_id",
        "credential_id",
        "auth_reason",
        "status",
        "count",
        "duration_seconds",
        "error_type",
        "method",
        "route",
        "status_code",
        "created",
        "scheduled_for",
    }
)


def safe_fields(fields: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in fields.items():
        if key not in EVENT_FIELDS:
            continue
        if value is None or type(value) in (bool, int):
            safe[key] = value
        elif type(value) is float and math.isfinite(value):
            safe[key] = value
        elif type(value) is str:
            safe[key] = value[:256]
        elif isinstance(value, UUID):
            safe[key] = str(value)
        elif isinstance(value, datetime):
            safe[key] = value.isoformat()
    return safe


def log_event(
    logger: logging.Logger, event: str, *, level: int = logging.INFO, **fields: object
) -> None:
    if not logger.isEnabledFor(level):
        return
    try:
        logger.log(
            level,
            event,
            extra={"event_fields": safe_fields({**current_context(), **fields})},
        )
    except Exception:
        # A broken log destination must not change a committed task outcome.
        return
