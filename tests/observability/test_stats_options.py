import sys

import pytest

from pytask_service import cli, cli_monitoring


def test_invalid_window_is_rejected_before_engine_creation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected(settings: object) -> None:
        raise AssertionError("must validate first")

    monkeypatch.setattr(cli_monitoring, "build_engine", unexpected)
    assert cli_monitoring.show_stats(59) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "window_seconds must be an integer from 60 to 604800" in output.err


def test_missing_database_configuration_explains_the_required_variable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def unexpected(settings: object) -> None:
        raise AssertionError("must validate configuration before creating an engine")

    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(cli_monitoring, "build_engine", unexpected)
    assert cli_monitoring.show_stats(3600) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Statistics unavailable: PYTASK_DATABASE_URL is required\n"


def test_invalid_database_urls_are_not_echoed_in_configuration_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PYTASK_DATABASE_URL", "private invalid URL")
    assert cli_monitoring.show_stats(3600) == 1
    output = capsys.readouterr()
    assert "PYTASK_DATABASE_URL is not a valid database URL" in output.err
    assert "private" not in output.err


def test_stats_subcommand_routes_the_requested_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    windows: list[int] = []
    monkeypatch.setattr(
        sys, "argv", ["pytask-service", "stats", "--window-seconds", "60"]
    )
    monkeypatch.setattr(cli, "show_stats", lambda seconds: windows.append(seconds) or 0)
    assert cli.main() == 0
    assert windows == [60]
