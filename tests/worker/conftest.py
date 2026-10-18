import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine
from pytask_service.db.models import Task


@pytest.fixture
def isolated_engine() -> Iterator[Engine]:
    if not os.environ.get("PYTASK_DATABASE_URL"):
        pytest.skip("PYTASK_DATABASE_URL is not set")

    schema = f"pytask_test_{uuid4().hex}"
    admin_engine = build_engine(Settings.from_env())
    with admin_engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')

    engine = build_engine(Settings.from_env())

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection: object, connection_record: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f'SET search_path TO "{schema}"')
        finally:
            cursor.close()
        dbapi_connection.commit()

    try:
        Task.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        admin_engine.dispose()
