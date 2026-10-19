from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.namespace import validate_schema_name
from pytask_service.config import Settings


def scoped_engine(settings: Settings, schema: str) -> Engine:
    validate_schema_name(schema)
    return create_engine(
        settings.database_url, pool_pre_ping=True, pool_size=1, max_overflow=1,
        pool_timeout=5, hide_parameters=True,
        connect_args={
            "connect_timeout": 5,
            "options": f"-csearch_path={schema} -cstatement_timeout=5000 -clock_timeout=2000",
        },
    )


def check_scope(engine: Engine, schema: str) -> None:
    validate_schema_name(schema)
    with engine.connect() as connection:
        actual = connection.scalar(text("SELECT current_schema()"))
        path = connection.scalar(text("SHOW search_path"))
    if actual != schema or path != schema:
        raise BenchmarkFailure("schema_isolation_failed")

