import sys

import pytest

from pytask_service import cli


@pytest.mark.parametrize(
    "options",
    [
        ["--run-at", "2026-10-18T12:00:00"],
        ["--run-at", "invalid"],
        ["--run-at", "2026-10-18T12:00:00Z", "--delay", "1"],
    ],
)
def test_cli_rejects_ambiguous_timing(
    monkeypatch: pytest.MonkeyPatch, options: list[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["pytask-service", "submit", "math.add", *options])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


@pytest.mark.parametrize("delay", ["-1", "nan", "inf", "31536001"])
def test_cli_rejects_invalid_delay_before_connecting(
    monkeypatch: pytest.MonkeyPatch, delay: str
) -> None:
    monkeypatch.delenv("PYTASK_DATABASE_URL", raising=False)
    monkeypatch.setattr(
        sys, "argv", ["pytask-service", "submit", "math.add", "--delay", delay]
    )
    assert cli.main() == 1


def test_cli_passes_normalized_timing_to_submission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def submit(*args: object, **kwargs: object) -> int:
        received.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "_submit", submit)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pytask-service",
            "submit",
            "math.add",
            "--run-at",
            "2026-10-18T12:00:00+03:00",
        ],
    )
    assert cli.main() == 0
    assert str(received["run_at"]) == "2026-10-18 09:00:00+00:00"
    assert received["delay"] is None
