import json
import sys
from collections.abc import Callable

import pytest
from sqlalchemy.engine import Engine

from pytask_service import cli, cli_schedule
from pytask_service.scheduling import command

pytestmark = pytest.mark.integration


@pytest.fixture
def invoke(isolated_engine: Engine, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> Callable[..., object]:
    monkeypatch.setenv("PYTASK_REGISTRY", "pytask_service.example_tasks:registry")
    monkeypatch.setattr(cli_schedule, "build_engine", lambda settings: isolated_engine)
    monkeypatch.setattr(command, "build_engine", lambda settings: isolated_engine)
    def run(*arguments: str) -> object:
        monkeypatch.setattr(sys, "argv", ["pytask-service", *arguments])
        assert cli.main() == 0
        output = capsys.readouterr().out
        return json.loads(output) if output else None
    return run


def test_schedule_cli_creates_inspects_pauses_and_resumes(invoke: Callable[..., object]) -> None:
    created = invoke("schedule", "create", "report", "math.add", "--every", "60", "--args", '{"left": 1, "right": 2}', "--paused")
    assert created["paused"] is True
    schedule_id = created["id"]
    assert invoke("schedule", "show", schedule_id)["name"] == "report"
    assert invoke("schedule", "list")[0]["id"] == schedule_id
    assert invoke("schedule", "resume", schedule_id)["paused"] is False
    assert invoke("schedule", "pause", schedule_id)["paused"] is True


def test_scheduler_cli_dispatches_without_loading_a_registry(invoke: Callable[..., object], monkeypatch: pytest.MonkeyPatch) -> None:
    created = invoke("schedule", "create", "report", "math.add", "--every", "60", "--args", '{"left": 1, "right": 2}')
    monkeypatch.delenv("PYTASK_REGISTRY")
    report = invoke("scheduler", "--once")
    assert report["created"] is True and report["schedule_id"] == created["id"]
    history = invoke("schedule", "history", created["id"])
    assert len(history) == 1 and history[0]["id"] == report["id"]
