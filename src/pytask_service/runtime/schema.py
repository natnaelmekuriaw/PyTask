from configparser import Error as ConfigError

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import select
from sqlalchemy.engine import Engine

from pytask_service.db.models import Schedule, Task, TaskAttempt
from pytask_service.runtime.paths import RuntimePaths


class RuntimeFailure(RuntimeError):
    pass


def expected_heads(paths: RuntimePaths) -> frozenset[str]:
    try:
        config = Config(str(paths.alembic_config))
        heads = frozenset(ScriptDirectory.from_config(config).get_heads())
    except (OSError, UnicodeError, ConfigError, CommandError):
        raise RuntimeFailure(
            "Migration scripts are unavailable; check the image and configuration"
        ) from None
    if not heads:
        raise RuntimeFailure("The image contains no migration heads")
    return heads


def check_schema(engine: Engine, paths: RuntimePaths) -> None:
    expected = expected_heads(paths)
    with engine.connect() as connection, connection.begin():
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")
        connection.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
        current = frozenset(MigrationContext.configure(connection).get_current_heads())
        if current != expected:
            raise RuntimeFailure(
                "Database schema does not match this image; "
                "run the explicit migration command"
            )
        for model in (Task, TaskAttempt, Schedule):
            connection.execute(select(model).limit(0))
