import pytest

from pytask_service.observability import service
from pytask_service.observability.window import ObservationWindow


def test_read_only_mode_precedes_aggregate_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    sentinel = object()

    class Result:
        def mappings(self) -> "Result":
            return self

        def one(self) -> object:
            return sentinel

    class Session:
        def execute(self, statement: object) -> Result:
            calls.append(str(statement))
            return Result()

    monkeypatch.setattr(service, "build_snapshot", lambda row, window: row)
    assert service.read_snapshot(Session(), ObservationWindow()) is sentinel
    assert calls[0] == "SET TRANSACTION READ ONLY"
    assert calls[1] == "SET LOCAL lock_timeout = '2s'"
    assert calls[2] == "SET LOCAL statement_timeout = '5s'"
    assert calls[3].startswith("SELECT ")
