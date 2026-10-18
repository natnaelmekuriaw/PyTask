import sys

import pytest

from pytask_service import cli


@pytest.mark.parametrize(
    "options",
    [["--batch-size", "0"], ["--poll-interval", "nan"], ["--batch-size", "1001"]],
)
def test_scheduler_rejects_bad_policy_without_database_access(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    options: list[str],
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytask-service", "scheduler", *options])
    assert cli.main() == 1
    assert "PYTASK_DATABASE_URL" not in capsys.readouterr().err


def test_schedule_creation_requires_a_registry(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["pytask-service", "schedule", "create", "report", "math.add", "--every", "60"],
    )
    assert cli.main() == 1
    assert "PYTASK_REGISTRY" in capsys.readouterr().err


@pytest.mark.parametrize(
    "options", [["--args", "{"], ["--args-file", "missing-schedule-arguments.json"]]
)
def test_schedule_argument_errors_fail_before_connecting(
    monkeypatch: pytest.MonkeyPatch, options: list[str]
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setenv("PYTASK_REGISTRY", "pytask_service.example_tasks:registry")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pytask-service",
            "schedule",
            "create",
            "report",
            "math.add",
            "--every",
            "60",
            *options,
        ],
    )
    assert cli.main() == 1


@pytest.mark.parametrize(
    "arguments",
    [
        ["schedule", "show", "bad-id"],
        [
            "schedule",
            "create",
            "report",
            "math.add",
            "--every",
            "60",
            "--start-at",
            "2026-10-18T00:00:00",
        ],
    ],
)
def test_schedule_parser_rejects_bad_ids_and_naive_start_times(
    monkeypatch: pytest.MonkeyPatch, arguments: list[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["pytask-service", *arguments])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
