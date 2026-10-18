from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.db.models import Task

config = context.config
if config.config_file_name is not None and config.attributes.get("connection") is None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Task.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=Settings.from_env().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        if not isinstance(supplied_connection, Connection):
            raise TypeError("Migration connection must be a SQLAlchemy Connection")
        migrate_connection(supplied_connection)
        return
    engine = build_engine(Settings.from_env())
    try:
        with engine.connect() as connection:
            migrate_connection(connection)
    finally:
        engine.dispose()


def migrate_connection(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
