import sys

import pytest

from pytask_service import cli


@pytest.mark.parametrize("options", [["--batch-size", "0"], ["--poll-interval", "nan"], ["--batch-size", "1001"]])
def test_scheduler_rejects_bad_policy_without_database_access(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], options: list[str]) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "scheduler", *options])
    assert cli.main() == 1
    assert "PYTASK_DATABASE_URL" not in capsys.readouterr().err


def test_schedule_creation_requires_a_registry(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "schedule", "create", "report", "math.add", "--every", "60"])
    assert cli.main() == 1
    assert "PYTASK_REGISTRY" in capsys.readouterr().err
