from unittest.mock import MagicMock

import pytest
from sqlalchemy.schema import CreateSchema, DropSchema

from pytask_service.benchmarks import database as module
from pytask_service.config import Settings


def test_setup_creates_models_only_after_confirming_scope(monkeypatch):
    admin, engine, metadata = MagicMock(), MagicMock(), MagicMock()
    scope = MagicMock()
    monkeypatch.setattr(module, "scoped_engine", lambda *_: engine)
    monkeypatch.setattr(module, "check_scope", scope)
    monkeypatch.setattr(module.Task, "metadata", metadata)
    with module.BenchmarkDatabase(admin, Settings("unused")) as database:
        assert database.connected_engine() is engine
        scope.assert_called_once_with(engine, database.schema)
        metadata.create_all.assert_called_once_with(engine)
    connection = admin.begin.return_value.__enter__.return_value
    statements = [call.args[0] for call in connection.execute.call_args_list]
    assert sum(isinstance(statement, CreateSchema) for statement in statements) == 1
    assert sum(isinstance(statement, DropSchema) for statement in statements) == 1
    assert "lock_timeout" in str(statements[0])
    engine.dispose.assert_called_once()


def test_lost_create_commit_still_attempts_safe_cleanup():
    admin = MagicMock()
    transaction = admin.begin.return_value
    transaction.__exit__.side_effect = [RuntimeError("commit lost"), None]
    database = module.BenchmarkDatabase(admin, Settings("unused"))
    with pytest.raises(RuntimeError, match="commit lost"):
        database.__enter__()
    statements = [
        call.args[0]
        for call in transaction.__enter__.return_value.execute.call_args_list
    ]
    drop = next(
        statement for statement in statements if isinstance(statement, DropSchema)
    )
    assert drop.if_exists is True
    assert drop.element == database.schema


def test_failed_scope_check_prevents_table_creation_and_drops_owned_schema(monkeypatch):
    admin, engine, metadata = MagicMock(), MagicMock(), MagicMock()
    monkeypatch.setattr(module, "scoped_engine", lambda *_: engine)
    monkeypatch.setattr(
        module, "check_scope", MagicMock(side_effect=RuntimeError("scope"))
    )
    monkeypatch.setattr(module.Task, "metadata", metadata)
    database = module.BenchmarkDatabase(admin, Settings("unused"))
    with pytest.raises(RuntimeError, match="scope"):
        database.__enter__()
    metadata.create_all.assert_not_called()
    engine.dispose.assert_called_once()
    connection = admin.begin.return_value.__enter__.return_value
    drops = [
        call.args[0]
        for call in connection.execute.call_args_list
        if isinstance(call.args[0], DropSchema)
    ]
    assert len(drops) == 1
    assert drops[0].element == database.schema
