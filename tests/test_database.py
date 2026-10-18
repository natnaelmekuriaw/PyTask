import os

import pytest

from pytask_service.config import Settings
from pytask_service.db.engine import build_engine, check_connection


@pytest.mark.integration
def test_database_connection() -> None:
    if not os.environ.get("PYTASK_DATABASE_URL"):
        pytest.skip("PYTASK_DATABASE_URL is not set")

    engine = build_engine(Settings.from_env())
    try:
        check_connection(engine)
    finally:
        engine.dispose()
