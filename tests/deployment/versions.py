from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from pytask_service.runtime.paths import RuntimePaths

PATHS = RuntimePaths(Path(__file__).resolve().parents[2] / "alembic.ini")


def record_version(engine: Engine, version: str) -> None:
    table = Table(
        "alembic_version",
        MetaData(),
        Column("version_num", String(32), primary_key=True),
    )
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert().values(version_num=version))
