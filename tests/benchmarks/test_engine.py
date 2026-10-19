from unittest.mock import MagicMock

import pytest

from pytask_service.benchmarks import engine as module
from pytask_service.config import Settings

SCHEMA = "pytask_bench_" + "a" * 32


def test_every_connection_uses_one_schema_and_bounded_queries(monkeypatch):
    create = MagicMock()
    monkeypatch.setattr(module, "create_engine", create)
    module.scoped_engine(
        Settings("postgresql+psycopg://user:secret@localhost/db"), SCHEMA
    )
    options = create.call_args.kwargs
    assert options["hide_parameters"] is True
    assert options["pool_size"] == options["max_overflow"] == 1
    assert options["connect_args"]["connect_timeout"] == 5
    pg_options = options["connect_args"]["options"]
    assert f"search_path={SCHEMA}" in pg_options
    assert "public" not in pg_options
    assert "statement_timeout=5000" in pg_options
    assert "lock_timeout=2000" in pg_options


@pytest.mark.parametrize(
    "actual,path", [(SCHEMA, "public"), ("public", SCHEMA), (None, SCHEMA)]
)
def test_scope_check_rejects_missing_schema_or_fallback(actual, path):
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.scalar.side_effect = [
        actual,
        path,
    ]
    with pytest.raises(RuntimeError, match="schema_isolation_failed"):
        module.check_scope(engine, SCHEMA)


def test_scope_check_accepts_only_the_exact_schema():
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.scalar.side_effect = [
        SCHEMA,
        SCHEMA,
    ]
    module.check_scope(engine, SCHEMA)
