import pytest
from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from pytask_service.db.models import Task
from pytask_service.observability.service import read_snapshot
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


def test_reading_statistics_never_claims_work_or_allows_writes(
    isolated_engine: Engine,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    task_id = database.task()
    database.read()
    with Session(isolated_engine) as session:
        assert (
            session.scalar(select(Task.status).where(Task.id == task_id)) == "pending"
        )
    with Session(isolated_engine) as session:
        read_snapshot(session)
        with pytest.raises(DBAPIError) as failure:
            session.execute(insert(Task).values(name="forbidden", arguments={}))
        assert getattr(failure.value.orig, "sqlstate", None) == "25006"
        session.rollback()
