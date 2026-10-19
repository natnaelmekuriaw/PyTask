import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from pytask_service.runtime.schema import check_schema, expected_heads
from tests.deployment.versions import PATHS, record_version

pytestmark = pytest.mark.integration


def test_missing_columns_fail_the_startup_schema_probe(isolated_engine: Engine) -> None:
    record_version(isolated_engine, next(iter(expected_heads(PATHS))))
    with isolated_engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE task_attempts DROP COLUMN queued_at")
    with pytest.raises(ProgrammingError) as failure:
        check_schema(isolated_engine, PATHS)
    assert failure.value.orig.sqlstate == "42703"
