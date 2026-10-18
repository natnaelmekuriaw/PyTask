from datetime import timedelta

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import TaskAttempt
from pytask_service.worker.claim import claim_next
from tests.observability.database import MonitoringDatabase

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("previous_attempts", [0, 1])
def test_claim_copies_eligibility_before_task_state_changes(
    isolated_engine: Engine, previous_attempts: int,
) -> None:
    database = MonitoringDatabase(isolated_engine)
    eligible = database.now - timedelta(seconds=15)
    task_id = database.task(available_at=eligible, attempt_count=previous_attempts)
    with Session(isolated_engine) as session, session.begin():
        claim = claim_next(session, "worker")
        assert claim is not None and claim.id == task_id
        attempt = session.get(TaskAttempt, claim.token)
        assert attempt is not None and attempt.queued_at == eligible
        assert attempt.number == previous_attempts + 1
