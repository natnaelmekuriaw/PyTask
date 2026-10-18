import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.db.models import TaskStatus
from pytask_service.observability.context import bind_context
from pytask_service.observability.events import log_event
from pytask_service.registry import load_registry
from pytask_service.worker.claim import ClaimedTask, claim_next
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.finish import finish_task
from pytask_service.worker.heartbeat import LeaseKeeper
from pytask_service.worker.identity import new_worker_id
from pytask_service.worker.lease import renew_claim
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.policy import WorkerPolicy
from pytask_service.worker.recovery import recover_expired
from pytask_service.worker.runner import run_in_process
from pytask_service.worker.transactions import bound_lease_transaction

TaskExecutor = Callable[[str, ClaimedTask, Event], TaskOutcome]
logger = logging.getLogger(__name__)


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
            recovered = recover_expired(session, self.policy.recovery_batch_size)
        if recovered:
            log_event(
                logger,
                "worker.leases_recovered",
                worker_id=self.worker_id,
                count=recovered,
            )
        with Session(self.engine) as session, session.begin():
            claim = claim_next(session, self.worker_id, self.policy.lease_seconds)
        if claim is None:
            return None

        with bind_context(
            task_id=claim.id,
            attempt_id=claim.token,
            attempt_number=claim.attempt_number,
            worker_id=claim.worker_id,
        ):
            try:
                return self._execute(claim)
            except LostClaimError:
                log_event(logger, "task.lease_lost", level=logging.WARNING)
                raise

    def _execute(self, claim: ClaimedTask) -> WorkedTask:
        keeper = LeaseKeeper(
            lambda: self._renew(claim),
            self.policy.heartbeat_seconds,
            lease_seconds=self.policy.lease_seconds,
            initial_deadline=claim.lease_deadline,
        )
        with keeper:
            log_event(logger, "task.claimed")
            keeper.raise_if_lost()
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
        event = "task.attempt_finished"
        if outcome.timed_out:
            event = "task.attempt_timed_out"
        log_event(logger, event, status=status.value)
        return WorkedTask(claim.id, outcome, status, claim.attempt_number)

    def _renew(self, claim: ClaimedTask) -> bool:
        with Session(self.engine) as session, session.begin():
            bound_lease_transaction(session)
            return renew_claim(session, claim, self.policy.lease_seconds)
