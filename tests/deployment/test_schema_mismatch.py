from pathlib import Path
from types import SimpleNamespace

import pytest

from pytask_service.runtime import schema
from pytask_service.runtime.paths import RuntimePaths
from tests.deployment.fakes import Engine


@pytest.mark.parametrize("current", [(), ("old",), ("newer",), ("current", "extra")])
def test_schema_head_sets_must_match_exactly(
    monkeypatch: pytest.MonkeyPatch, current: tuple[str, ...]
) -> None:
    engine = Engine()
    monkeypatch.setattr(schema, "expected_heads", lambda paths: frozenset({"current"}))
    monkeypatch.setattr(
        schema.MigrationContext,
        "configure",
        lambda connection: SimpleNamespace(get_current_heads=lambda: current),
    )
    with pytest.raises(schema.RuntimeFailure, match="explicit migration"):
        schema.check_schema(engine, RuntimePaths(Path("unused")))
    assert engine.connected
    assert len(engine.connection.statements) == 3
    assert engine.connection.statements[0] == "SET TRANSACTION READ ONLY"
