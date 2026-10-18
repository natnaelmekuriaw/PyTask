import pytest
from sqlalchemy.exc import OperationalError

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
