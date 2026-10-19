import json
from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import command
from pytask_service.config import Settings


@pytest.fixture
def configured(monkeypatch, report):
    monkeypatch.setattr(command.Settings, "from_env", lambda: Settings("unused"))
    run = MagicMock(return_value=report)
    monkeypatch.setattr(command, "run_suite", run)
    return run


def test_command_writes_reports_and_prints_a_small_summary(
    tmp_path, configured, capsys
):
    assert command.main(["--output", str(tmp_path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["completed_cases"] == 1
    assert len(list(tmp_path.rglob("results.json"))) == 1


@pytest.mark.parametrize("code,exit_code", [("case_failed", 1), ("interrupted", 130)])
def test_invalid_runs_are_saved_and_return_failure(
    tmp_path, configured, report, capsys, code, exit_code
):
    configured.return_value = replace(report, error_code=code)
    assert command.main(["--output", str(tmp_path)]) == exit_code
    assert json.loads(capsys.readouterr().out)["error_code"] == code
    assert len(list(tmp_path.rglob("results.json"))) == 1


def test_invalid_options_fail_before_creating_an_engine(configured, capsys):
    assert command.main(["--tasks", "0"]) == 2
    configured.assert_not_called()
    assert "configuration failed" in capsys.readouterr().err


def test_output_failure_returns_a_safe_message(monkeypatch, configured, capsys):
    def denied(*_):
        raise PermissionError("private filesystem path")

    monkeypatch.setattr(command, "write_reports", denied)
    assert command.main([]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "private filesystem path" not in output.err
