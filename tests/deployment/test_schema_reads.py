from pathlib import Path
from types import SimpleNamespace

import pytest

from pytask_service.runtime import schema
from pytask_service.runtime.paths import RuntimePaths
from tests.deployment.fakes import Engine


def test_schema_validation_never_fetches_payload_rows_or_runs_ddl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = Engine()
    monkeypatch.setattr(schema, "expected_heads", lambda paths: frozenset({"current"}))
    monkeypatch.setattr(
        schema.MigrationContext,
        "configure",
        lambda connection: SimpleNamespace(get_current_heads=lambda: ("current",)),
    )
    schema.check_schema(engine, RuntimePaths(Path("unused")))
    statements = engine.connection.statements
    assert statements[:3] == [
        "SET TRANSACTION READ ONLY",
        "SET LOCAL lock_timeout = '2s'",
        "SET LOCAL statement_timeout = '5s'",
    ]
    reads = statements[3:]
    assert len(reads) == 3
    for statement in reads:
        assert statement.is_select
        compiled = statement.compile(compile_kwargs={"literal_binds": True})
        assert "LIMIT 0" in str(compiled)
