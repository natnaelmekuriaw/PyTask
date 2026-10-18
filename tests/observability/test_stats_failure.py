import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

from pytask_service import cli_monitoring
from tests.observability.test_stats_cli import FakeSession


def test_statistics_failures_do_not_expose_database_parameters(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Engine:
        disposed = False

        def dispose(self) -> None:
            self.disposed = True

    def fail(session: object, window: object) -> None:
        raise OperationalError("private SQL", {"password": "secret"}, RuntimeError())

    engine = Engine()
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setattr(cli_monitoring, "build_engine", lambda settings: engine)
    monkeypatch.setattr(cli_monitoring, "Session", lambda engine: FakeSession())
    monkeypatch.setattr(cli_monitoring, "read_snapshot", fail)
    assert cli_monitoring.show_stats(3600) == 1
    output = capsys.readouterr()
    assert output.out == "" and "Statistics unavailable" in output.err
    assert "private" not in output.err and "secret" not in output.err
    assert engine.disposed


@pytest.mark.parametrize(
    ("state", "hint"),
    [
        ("42P01", "apply migrations"),
        ("42703", "apply migrations"),
        ("28P01", "credentials"),
        ("28000", "credentials"),
        ("42501", "permissions"),
        ("57014", "timed out or was canceled"),
        ("55P03", "database lock"),
        ("42883", "SQLSTATE 42883"),
        (None, "Database operation failed"),
    ],
)
def test_database_failures_provide_safe_specific_guidance(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str | None,
    hint: str,
) -> None:
    class Failure(Exception):
        sqlstate = state

    def fail(settings: object) -> None:
        raise OperationalError(
            "private SQL", {"password": "secret"}, Failure("private connection URL")
        )

    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setattr(cli_monitoring, "build_engine", fail)
    assert cli_monitoring.show_stats(3600) == 1
    output = capsys.readouterr()
    assert output.out == "" and hint in output.err
    assert "private" not in output.err and "secret" not in output.err


@pytest.mark.parametrize("state", ["private text", "42P01\nsecret", 42703, None])
def test_unrecognized_error_metadata_is_not_rendered(state: object) -> None:
    class Failure(Exception):
        sqlstate = state

    error = ProgrammingError("private SQL", {}, Failure("secret"))
    hint = cli_monitoring._database_hint(error)
    assert hint == "The statistics query failed; check database access and migrations."
