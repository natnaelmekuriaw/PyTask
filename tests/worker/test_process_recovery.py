import multiprocessing
from datetime import timedelta
from time import monotonic, sleep

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.observability.service import read_snapshot
from pytask_service.policy import TaskPolicy
from pytask_service.tasks import list_attempts, submit_task
from pytask_service.worker.service import Worker
from pytask_service.worker.termination import stop_process
from pytask_service.worker.transactions import database_now
from tests.worker.crash_worker import claim_then_crash


@pytest.mark.integration
def test_new_worker_recovers_after_claiming_process_dies(
    isolated_engine: Engine,
) -> None:
    with Session(isolated_engine) as session, session.begin():
        schema = session.scalar(select(func.current_schema()))
        task_id = submit_task(
            session,
            registry,
            "math.add",
            {"left": 1, "right": 2},
            policy=TaskPolicy(retry_base_seconds=0.01, retry_max_seconds=0.01),
        )
    process = multiprocessing.get_context("spawn").Process(
        target=claim_then_crash, args=(schema,)
    )
    process.start()
    try:
        process.join(timeout=10)
        assert process.exitcode == 7
    finally:
        stop_process(process)
        process.close()

    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, task_id)
        assert task is not None and task.status == TaskStatus.RUNNING.value
        task.lease_expires_at = database_now(session) - timedelta(seconds=1)
    with Session(isolated_engine) as session:
        before = read_snapshot(session)
        assert before.queue.expired_running == 1
    worker = Worker(isolated_engine, "pytask_service.example_tasks:registry")
    deadline = monotonic() + 5
    worked = worker.run_once()
    while worked is None and monotonic() < deadline:
        sleep(0.02)
        worked = worker.run_once()

    assert worked is not None and worked.status == TaskStatus.SUCCEEDED
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None and task.result == 3
        attempts = list_attempts(session, task_id)
        assert [attempt.number for attempt in attempts] == [1, 2]
        assert [attempt.status for attempt in attempts] == ["abandoned", "succeeded"]
    with Session(isolated_engine) as session:
        after = read_snapshot(session)
        assert after.queue.expired_running == 0
        assert after.queue.succeeded == 1
        assert after.attempts.abandoned == after.attempts.succeeded == 1
        assert after.attempts.retries_started == 1
        assert after.attempts.execution.samples == 1
        assert after.attempts.queue_wait.samples == 2
