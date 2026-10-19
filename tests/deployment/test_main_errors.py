import sys

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

from pytask_service.runtime import main as runtime


def test_database_failures_never_print_queries_or_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(*args: object) -> None:
        raise OperationalError(
            "private SQL", {"password": "secret"}, RuntimeError("private")
        )

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.setattr(sys, "argv", ["runtime", "scheduler"])
    monkeypatch.setattr(runtime, "prepare_service", fail)
    assert runtime.main() == 1
    output = capsys.readouterr()
    assert output.out == "" and "Database preflight failed" in output.err
    assert "private" not in output.err and "secret" not in output.err


def test_failed_exec_has_a_safe_nonzero_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(command: object) -> None:
        raise OSError("private executable path")

    monkeypatch.setattr(sys, "argv", ["runtime", "cli", "--help"])
    monkeypatch.setattr(runtime, "replace_process", fail)
    assert runtime.main() == 1
    assert (
        capsys.readouterr().err
        == "Cannot start runtime process; check the image installation\n"
    )


@pytest.mark.parametrize(
    "state,suffix",
    [
        ("42703", " (SQLSTATE 42703)"),
        ("42501", " (SQLSTATE 42501)"),
        (None, ""),
        ("private-invalid-code", ""),
    ],
)
def test_database_error_codes_are_safe_and_actionable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str | None,
    suffix: str,
) -> None:
    class Failure(Exception):
        sqlstate = state

    def fail(*args: object) -> None:
        raise ProgrammingError(
            "private query", {"password": "secret"}, Failure("private")
        )

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@postgres/db")
    monkeypatch.setattr(sys, "argv", ["runtime", "scheduler"])
    monkeypatch.setattr(runtime, "prepare_service", fail)
    assert runtime.main() == 1
    assert capsys.readouterr().err == (
        f"Database preflight failed{suffix}; check connection, permissions, and migrations\n"
    )
