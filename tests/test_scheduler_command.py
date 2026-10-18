import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from pytask_service.config import Settings
from pytask_service.scheduling import command
from pytask_service.scheduling.enqueue import ScheduledTask


@pytest.mark.parametrize("fails", [False, True])
def test_scheduler_disposes_its_engine_after_dispatch(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], fails: bool) -> None:
    class Engine:
        disposed = False
        def dispose(self) -> None:
            self.disposed = True
    class Scheduler:
        def __init__(self, engine: object, policy: object) -> None:
            pass
        def run_once(self) -> list[ScheduledTask]:
            if fails:
                raise RuntimeError("dispatch failed")
            return []
    engine = Engine()
    monkeypatch.setattr(command, "build_engine", lambda settings: engine)
    monkeypatch.setattr(command, "Scheduler", Scheduler)
    settings = Settings("postgresql+psycopg://u:p@localhost/db")
    if fails:
        with pytest.raises(RuntimeError, match="dispatch failed"):
            command.run_scheduler(settings, once=True)
    else:
        assert command.run_scheduler(settings, once=True) == 0
        assert capsys.readouterr().out == ""
    assert engine.disposed
