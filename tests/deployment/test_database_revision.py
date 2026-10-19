from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from pytask_service.db.models import Task
from pytask_service.runtime.schema import RuntimeFailure, check_schema, expected_heads
from tests.deployment.versions import PATHS, record_version

pytestmark = pytest.mark.integration


def test_matching_schema_is_readable_and_does_not_leave_the_pool_read_only(
    isolated_engine: Engine,
) -> None:
    record_version(isolated_engine, next(iter(expected_heads(PATHS))))
    check_schema(isolated_engine, PATHS)
    with isolated_engine.begin() as connection:
        connection.execute(
            Task.__table__.insert().values(id=uuid4(), name="math.add", arguments={})
        )


def test_outdated_schema_revision_is_not_automatically_upgraded(
    isolated_engine: Engine,
) -> None:
    record_version(isolated_engine, "20261018_06")
    with pytest.raises(RuntimeFailure, match="explicit migration"):
        check_schema(isolated_engine, PATHS)
    with isolated_engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "20261018_06"
        )
