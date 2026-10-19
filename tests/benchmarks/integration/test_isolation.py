import pytest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from pytask_service.benchmarks.database import BenchmarkDatabase
from pytask_service.benchmarks.engine import check_scope
from pytask_service.benchmarks.workloads import registry
from pytask_service.config import Settings
from pytask_service.db.models import Task
from pytask_service.tasks import submit_task

pytestmark = pytest.mark.integration


def test_benchmark_schema_does_not_read_or_remove_application_tasks(isolated_engine):
    with Session(isolated_engine) as session, session.begin():
        sentinel = submit_task(session, registry, "benchmark.noop", {"index": 42})
    database = BenchmarkDatabase(isolated_engine, Settings.from_env())
    with database:
        engine = database.connected_engine()
        with Session(engine) as session, session.begin():
            assert session.scalar(select(func.count()).select_from(Task)) == 0
            own_task = submit_task(session, registry, "benchmark.noop", {"index": 1})
            assert own_task != sentinel
        engine.dispose()
        check_scope(engine, database.schema)
        with Session(engine) as session:
            assert session.get(Task, sentinel) is None
    with Session(isolated_engine) as session:
        task = session.get(Task, sentinel)
        assert task is not None
        assert task.status == "pending"
        assert session.get(Task, own_task) is None
    with isolated_engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT count(*) FROM pg_namespace WHERE nspname = :schema"),
                {"schema": database.schema},
            )
            == 0
        )
