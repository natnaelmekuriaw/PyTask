from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import AttemptStatus, Task, TaskAttempt, TaskStatus
from pytask_service.example_tasks import registry
from pytask_service.policy import TaskPolicy
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import ClaimedTask, claim_next
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.finish import finish_task
from pytask_service.worker.lease import renew_claim
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.recovery import recover_expired
from pytask_service.worker.transactions import database_now


def expired_claim(engine: Engine, max_attempts: int = 3) -> ClaimedTask:
    with Session(engine) as session, session.begin():
        submit_task(session, registry, "math.add", {"left": 1, "right": 2}, policy=TaskPolicy(max_attempts=max_attempts))
    with Session(engine) as session, session.begin():
        claim = claim_next(session, "crashed-worker")
    assert claim is not None
    with Session(engine) as session, session.begin():
        task = session.get(Task, claim.id)
        assert task is not None
        task.lease_expires_at = database_now(session) - timedelta(seconds=1)
    return claim


@pytest.mark.integration
def test_expired_claim_is_requeued_once(isolated_engine: Engine) -> None:
    claim = expired_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        assert recover_expired(session) == 1
    with Session(isolated_engine) as session, session.begin():
        assert recover_expired(session) == 0
        task = session.get(Task, claim.id)
        attempt = session.get(TaskAttempt, claim.token)
        assert task is not None and attempt is not None
        assert task.status == TaskStatus.PENDING.value
        assert task.attempt_count == 1
        assert task.claim_token is None
        assert attempt.status == AttemptStatus.ABANDONED.value
        assert attempt.error == "Worker lease expired"


@pytest.mark.integration
def test_expired_final_attempt_is_terminal(isolated_engine: Engine) -> None:
    claim = expired_claim(isolated_engine, max_attempts=1)
    with Session(isolated_engine) as session, session.begin():
        assert recover_expired(session) == 1
    with Session(isolated_engine) as session:
        task = session.get(Task, claim.id)
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
        assert task.finished_at is not None


@pytest.mark.integration
def test_recovery_workers_skip_each_others_locked_batch(isolated_engine: Engine) -> None:
    expired_claim(isolated_engine)
    expired_claim(isolated_engine)

    with Session(isolated_engine) as first, first.begin():
        assert recover_expired(first, batch_size=1) == 1
        with Session(isolated_engine) as second, second.begin():
            assert recover_expired(second, batch_size=1) == 1
    with Session(isolated_engine) as session, session.begin():
        assert recover_expired(session) == 0


@pytest.mark.integration
def test_old_token_cannot_finish_reclaimed_task_with_same_worker_id(isolated_engine: Engine) -> None:
    old = expired_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        recover_expired(session)
        task = session.get(Task, old.id)
        assert task is not None
        task.available_at = database_now(session)
    with Session(isolated_engine) as session, session.begin():
        new = claim_next(session, old.worker_id)
    assert new is not None and new.token != old.token
    assert new.attempt_number == 2
    with Session(isolated_engine) as session, session.begin():
        assert not renew_claim(session, old, 30)
        with pytest.raises(LostClaimError):
            finish_task(session, old, TaskOutcome.success("stale"))
    with Session(isolated_engine) as session, session.begin():
        assert finish_task(session, new, TaskOutcome.success(3)) == TaskStatus.SUCCEEDED
