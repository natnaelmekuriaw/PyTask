import sys

import pytest

from pytask_service import cli


class FakeEngine:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


def test_check_db_reports_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = FakeEngine()
    monkeypatch.setenv(
        "PYTASK_DATABASE_URL", "postgresql+psycopg://user:pass@localhost/pytask"
    )
    monkeypatch.setattr(sys, "argv", ["pytask-service", "check-db"])
    monkeypatch.setattr(cli, "build_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "check_connection", lambda engine: None)

    assert cli.main() == 0
    assert capsys.readouterr().out == "Database connection OK\n"
    assert engine.disposed


def test_check_db_reports_missing_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "check-db"])

    assert cli.main() == 1
    assert "PYTASK_DATABASE_URL is required" in capsys.readouterr().err


def test_submit_requires_a_registry(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "submit", "math.add"])

    assert cli.main() == 1
    assert "PYTASK_REGISTRY is required" in capsys.readouterr().err


def test_submit_rejects_malformed_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setenv("PYTASK_REGISTRY", "pytask_service.example_tasks:registry")
    monkeypatch.setattr(
        sys, "argv", ["pytask-service", "submit", "math.add", "--args", "{"]
    )

    assert cli.main() == 1
    assert "--args must contain valid JSON" in capsys.readouterr().err
