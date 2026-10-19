import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from pytask_service.runtime.schema import RuntimeFailure, check_schema
from tests.deployment.versions import PATHS

pytestmark = pytest.mark.integration


def test_preflight_never_stamps_an_unmigrated_database(isolated_engine: Engine) -> None:
    with pytest.raises(RuntimeFailure, match="explicit migration"):
        check_schema(isolated_engine, PATHS)
    assert not inspect(isolated_engine).has_table("alembic_version")
