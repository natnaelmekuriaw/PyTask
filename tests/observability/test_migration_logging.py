import logging
import logging.config
import runpy
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic import context
from alembic.config import Config
from sqlalchemy.engine import Connection

from pytask_service.db import engine

ROOT = Path(__file__).resolve().parents[2]


def test_embedded_migrations_leave_host_logging_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(str(ROOT / "alembic.ini"))
    connection = Mock(spec=Connection)
    config.attributes["connection"] = connection
    configure = Mock()
    migrate = Mock()
    reconfigure_logging = Mock(
        side_effect=AssertionError("embedded migrations must preserve host logging")
    )
    root_handlers = list(logging.getLogger().handlers)
    service_logger = logging.getLogger("pytask_service")
    service_handlers = list(service_logger.handlers)
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(context, "configure", configure)
    monkeypatch.setattr(context, "begin_transaction", nullcontext)
    monkeypatch.setattr(context, "run_migrations", migrate)
    monkeypatch.setattr(logging.config, "fileConfig", reconfigure_logging)

    runpy.run_path(str(ROOT / "migrations" / "env.py"))

    reconfigure_logging.assert_not_called()
    assert configure.call_args.kwargs["connection"] is connection
    migrate.assert_called_once_with()
    assert logging.getLogger().handlers == root_handlers
    assert service_logger.handlers == service_handlers


def test_standalone_migration_logging_preserves_existing_loggers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopBeforeDatabase(Exception):
        pass

    def stop(settings: object) -> None:
        raise StopBeforeDatabase

    config = Config(str(ROOT / "alembic.ini"))
    configure = Mock()
    monkeypatch.setenv("PYTASK_DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: False)
    monkeypatch.setattr(logging.config, "fileConfig", configure)
    monkeypatch.setattr(engine, "build_engine", stop)

    with pytest.raises(StopBeforeDatabase):
        runpy.run_path(str(ROOT / "migrations" / "env.py"))

    configure.assert_called_once_with(
        config.config_file_name, disable_existing_loggers=False
    )
