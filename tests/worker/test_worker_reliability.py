from datetime import timedelta
from threading import Event

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.policy import WorkerPolicy
from pytask_service.worker.service import Worker
from pytask_service.worker.transactions import database_now


@pytest.mark.integration
def test_worker_renews_lease_during_long_execution(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})

    def long_execution(path: str, claim: ClaimedTask, cancel: Event) -> TaskOutcome:
        assert not cancel.wait(3.2)
        return TaskOutcome.success(3)

    worker = Worker(
        isolated_engine, "pytask_service.example_tasks:registry", executor=long_execution,
        policy=WorkerPolicy(lease_seconds=3, heartbeat_seconds=0.1),
    )
    worked = worker.run_once()

    assert worked is not None and worked.status == TaskStatus.SUCCEEDED
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None and task.result == 3
        assert task.lease_expires_at is None


@pytest.mark.integration
def test_worker_does_not_finalize_after_losing_lease(isolated_engine: Engine) -> None:
    with Session(isolated_engine) as session, session.begin():
        task_id = submit_task(session, registry, "math.add", {"left": 1, "right": 2})

    def lose_lease(path: str, claim: ClaimedTask, cancel: Event) -> TaskOutcome:
        with Session(isolated_engine) as session, session.begin():
            task = session.get(Task, claim.id)
            assert task is not None
            task.lease_expires_at = database_now(session) - timedelta(seconds=1)
        assert cancel.wait(2)
        raise LostClaimError("Lease expired during execution")

    worker = Worker(
        isolated_engine, "pytask_service.example_tasks:registry", executor=lose_lease,
        policy=WorkerPolicy(lease_seconds=3, heartbeat_seconds=0.05),
    )
    with pytest.raises(LostClaimError):
        worker.run_once()
    with Session(isolated_engine) as session:
        task = session.get(Task, task_id)
        assert task is not None
        assert task.status == TaskStatus.RUNNING.value
        assert task.finished_at is None
