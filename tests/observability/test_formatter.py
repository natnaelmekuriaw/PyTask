import json
import logging

from pytask_service.observability.formatter import EventFormatter


def test_exception_payloads_and_format_arguments_are_not_rendered() -> None:
    error = RuntimeError("password=private")
    record = logging.LogRecord(
        "pytask_service.test",
        logging.ERROR,
        "",
        1,
        "api.database_failed",
        ("secret SQL parameters",),
        (type(error), error, None),
    )
    record.event_fields = {"task_id": "task", "arguments": "private"}
    record.stack_info = "secret stack"
    payload = json.loads(EventFormatter().format(record))
    assert payload["event"] == "api.database_failed"
    assert payload["error_type"] == "RuntimeError"
    assert payload["task_id"] == "task"
    assert "private" not in json.dumps(payload)
    assert "secret" not in json.dumps(payload)
    assert payload["timestamp"].endswith("+00:00")
