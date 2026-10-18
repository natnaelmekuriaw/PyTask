import sys

import pytest

from pytask_service import cli, cli_monitoring


def test_invalid_window_is_rejected_before_engine_creation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected(settings: object) -> None:
        raise AssertionError("must validate first")

    monkeypatch.setattr(cli_monitoring, "build_engine", unexpected)
    assert cli_monitoring.show_stats(59) == 1
    assert capsys.readouterr().out == ""


def test_stats_subcommand_routes_the_requested_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    windows: list[int] = []
    monkeypatch.setattr(sys, "argv", ["pytask-service", "stats", "--window-seconds", "60"])
    monkeypatch.setattr(cli, "show_stats", lambda seconds: windows.append(seconds) or 0)
    assert cli.main() == 0
    assert windows == [60]
