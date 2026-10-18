import json
from contextlib import nullcontext

import pytest

from pytask_service import cli_monitoring
from tests.observability.factories import empty_snapshot


class FakeSession:
    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def begin(self) -> object:
        return nullcontext()


def test_statistics_need_only_database_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    class Engine:
        disposed = False

        def dispose(self) -> None:
            self.disposed = True

    engine = Engine()
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.delenv("PYTASK_REGISTRY", raising=False)
    monkeypatch.setattr(cli_monitoring, "build_engine", lambda settings: engine)
    monkeypatch.setattr(cli_monitoring, "Session", lambda engine: FakeSession())
    monkeypatch.setattr(cli_monitoring, "read_snapshot", lambda session, window: empty_snapshot())
    assert cli_monitoring.show_stats(3600) == 0
    output = capsys.readouterr()
    assert json.loads(output.out)["queue"]["ready"] == 0
    assert output.err == "" and engine.disposed
