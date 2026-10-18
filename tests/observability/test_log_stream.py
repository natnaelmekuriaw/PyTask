import io
import json
import logging

import pytest

from pytask_service.observability.formatter import EventFormatter
from pytask_service.observability.logging import StderrHandler


def test_console_handler_follows_stderr_redirection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_stream = io.StringIO()
    handler = StderrHandler(old_stream)
    handler.setFormatter(EventFormatter())
    old_stream.close()
    current_stream = io.StringIO()
    monkeypatch.setattr("sys.stderr", current_stream)
    record = logging.LogRecord("pytask_service", logging.INFO, "", 0, "worker.started", (), None)
    handler.handle(record)
    assert json.loads(current_stream.getvalue())["event"] == "worker.started"
