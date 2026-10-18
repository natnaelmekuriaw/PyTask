from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import Task
from pytask_service.example_tasks import registry
from pytask_service.tasks import submit_task
from pytask_service.worker.claim import ClaimedTask, claim_next
from pytask_service.worker.lease import renew_claim
from pytask_service.worker.transactions import database_now


def make_claim(engine: Engine) -> ClaimedTask:
    with Session(engine) as session, session.begin():
        submit_task(session, registry, "math.add", {"left": 1, "right": 2})
    with Session(engine) as session, session.begin():
        claim = claim_next(session, "worker-one")
    assert claim is not None
    return claim


@pytest.mark.integration
def test_renewal_extends_live_lease(isolated_engine: Engine) -> None:
    claim = make_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        before = database_now(session)
        assert renew_claim(session, claim, 60)
    with Session(isolated_engine) as session:
        task = session.get(Task, claim.id)
        assert task is not None and task.lease_expires_at is not None
        assert task.lease_expires_at >= before + timedelta(seconds=60)


@pytest.mark.integration
def test_old_token_cannot_renew_current_claim(isolated_engine: Engine) -> None:
    claim = make_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        assert not renew_claim(session, replace(claim, token=uuid4()), 60)


@pytest.mark.integration
def test_expired_lease_cannot_be_renewed(isolated_engine: Engine) -> None:
    claim = make_claim(isolated_engine)
    with Session(isolated_engine) as session, session.begin():
        task = session.get(Task, claim.id)
        assert task is not None
        task.lease_expires_at = database_now(session) - timedelta(seconds=1)
    with Session(isolated_engine) as session, session.begin():
        assert not renew_claim(session, claim, 60)
