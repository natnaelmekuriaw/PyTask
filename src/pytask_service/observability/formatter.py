import json
import logging
from datetime import UTC, datetime

from pytask_service.observability.events import safe_fields


class EventFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = getattr(record, "event_fields", {})
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": str(record.msg)[:256],
        }
        if isinstance(fields, dict):
            payload.update(safe_fields(fields))
        if record.exc_info and record.exc_info[0] is not None:
            payload["error_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=True, allow_nan=False)
