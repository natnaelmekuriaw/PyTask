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
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.transactions import database_now


def make_claim(engine: Engine, max_attempts: int = 3) -> ClaimedTask:
    with Session(engine) as session, session.begin():
        submit_task(session, registry, "math.add", {"left": 1, "right": 2}, policy=TaskPolicy(max_attempts=max_attempts))
    with Session(engine) as session, session.begin():
        claim = claim_next(session, "worker-one")
    assert claim is not None
    return claim


@pytest.mark.integration
def test_failed_attempt_requeues_task_and_keeps_error(isolated_engine: Engine) -> None:
    claim = make_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        before = database_now(session)
        assert finish_task(session, claim, TaskOutcome.failure(ValueError("bad input"))) == TaskStatus.PENDING
    with Session(isolated_engine) as session:
        task = session.get(Task, claim.id)
        attempt = session.get(TaskAttempt, claim.token)
        assert task is not None and attempt is not None
        assert task.status == TaskStatus.PENDING.value
        assert task.attempt_count == 1
        assert task.available_at >= before
        assert task.claim_token is None and task.lease_expires_at is None
        assert attempt.status == AttemptStatus.FAILED.value
        assert attempt.error is not None and "bad input" in attempt.error


@pytest.mark.integration
def test_expired_worker_cannot_finish_even_before_recovery(isolated_engine: Engine) -> None:
    claim = make_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, claim.id)
        assert task is not None
        task.lease_expires_at = database_now(session) - timedelta(seconds=1)
    with Session(isolated_engine) as session, session.begin():
        with pytest.raises(LostClaimError):
            finish_task(session, claim, TaskOutcome.success(3))
