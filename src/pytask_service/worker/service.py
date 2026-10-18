from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import TaskStatus
from pytask_service.registry import load_registry
from pytask_service.worker.claim import ClaimedTask, claim_next
from pytask_service.worker.finish import finish_task
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.heartbeat import LeaseKeeper
from pytask_service.worker.identity import new_worker_id
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.policy import WorkerPolicy
from pytask_service.worker.lease import renew_claim
from pytask_service.worker.recovery import recover_expired
from pytask_service.worker.runner import run_in_process
from pytask_service.worker.transactions import bound_lease_transaction

TaskExecutor = Callable[[str, ClaimedTask, Event], TaskOutcome]


@dataclass(frozen=True, slots=True)
class WorkedTask:
    id: UUID
    outcome: TaskOutcome
    status: TaskStatus | None = None
    attempt_number: int = 1


class Worker:
    def __init__(
        self,
        engine: Engine,
        registry_path: str,
        *,
        worker_id: str | None = None,
        executor: TaskExecutor = run_in_process,
        policy: WorkerPolicy | None = None,
    ) -> None:
        load_registry(registry_path)
        self.engine = engine
        self.registry_path = registry_path
        self.worker_id = worker_id or new_worker_id()
        self.executor = executor
        self.policy = policy or WorkerPolicy()

    def run_once(self) -> WorkedTask | None:
        with Session(self.engine) as session, session.begin():
            recover_expired(session, self.policy.recovery_batch_size)
        with Session(self.engine) as session, session.begin():
            claim = claim_next(session, self.worker_id, self.policy.lease_seconds)
        if claim is None:
            return None

        keeper = LeaseKeeper(lambda: self._renew(claim), self.policy.heartbeat_seconds)
        with keeper:
            try:
                outcome = self.executor(self.registry_path, claim, keeper.cancel_event)
            except LostClaimError:
                keeper.raise_if_lost()
                raise
            except Exception as error:
                outcome = TaskOutcome.failure(error)
        keeper.raise_if_lost()

        with Session(self.engine) as session, session.begin():
            status = finish_task(session, claim, outcome)
        return WorkedTask(claim.id, outcome, status, claim.attempt_number)

    def _renew(self, claim: ClaimedTask) -> bool:
        with Session(self.engine) as session, session.begin():
            bound_lease_transaction(session)
            return renew_claim(session, claim, self.policy.lease_seconds)
