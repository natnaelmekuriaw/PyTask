import logging
from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import worker
from pytask_service.config import Settings


def test_ready_signal_follows_schema_and_registry_checks(monkeypatch):
    events = []
    engine = MagicMock()
    stopped, ready = MagicMock(), MagicMock()
    stopped.is_set.side_effect = [False, True]
    ready.set.side_effect = lambda: events.append("ready")
    service = MagicMock()
    service.run_once.return_value = None
    logger = logging.getLogger("pytask_service")
    monkeypatch.setattr(logger, "setLevel", MagicMock())
    monkeypatch.setattr(worker.signal, "signal", MagicMock())
    monkeypatch.setattr(worker, "scoped_engine", lambda *_: engine)
    monkeypatch.setattr(worker, "check_scope", lambda *_: events.append("scope"))

    def build(*args, **kwargs):
        events.append("registry")
        return service

    monkeypatch.setattr(worker, "Worker", build)
    worker.worker_main(Settings("unused"), "schema", stopped, ready, "test")
    assert events == ["scope", "registry", "ready"]
    stopped.wait.assert_called_once_with(0.01)
    engine.dispose.assert_called_once()


def test_worker_errors_do_not_disclose_connection_details(monkeypatch, capsys):
    engine, ready = MagicMock(), MagicMock()
    monkeypatch.setattr(worker.signal, "signal", MagicMock())
    monkeypatch.setattr(logging.getLogger("pytask_service"), "setLevel", MagicMock())
    monkeypatch.setattr(worker, "scoped_engine", lambda *_: engine)

    def fail(*_):
        raise RuntimeError("private database credentials")

    monkeypatch.setattr(worker, "check_scope", fail)
    with pytest.raises(SystemExit) as caught:
        worker.worker_main(Settings("unused"), "schema", MagicMock(), ready, "test")
    assert caught.value.code == 1
    assert "private" not in capsys.readouterr().err
    ready.set.assert_not_called()
    engine.dispose.assert_called_once()
