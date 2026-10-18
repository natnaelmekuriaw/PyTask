import json
import sys
from uuid import uuid4

import pytest

from pytask_service import cli
from pytask_service.db.models import TaskStatus
from pytask_service.worker.command import report
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.service import WorkedTask


def test_submit_rejects_zero_attempts_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["pytask-service", "submit", "math.add", "--max-attempts", "0"]
    )
    assert cli.main() == 1
    assert "max_attempts" in capsys.readouterr().err


def test_worker_rejects_unsafe_heartbeat_interval(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pytask-service",
            "worker",
            "--lease-seconds",
            "3",
            "--heartbeat-seconds",
            "2",
        ],
    )
    assert cli.main() == 1
    assert "one third" in capsys.readouterr().err


def test_worker_reports_pending_when_an_attempt_will_retry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report(
        WorkedTask(
            uuid4(), TaskOutcome.failure(ValueError("retry")), TaskStatus.PENDING, 2
        )
    )
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "pending"
    assert output["attempt"] == 2
