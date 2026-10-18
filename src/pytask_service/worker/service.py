from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.registry import load_registry
from pytask_service.worker.claim import ClaimedTask, claim_next
from pytask_service.worker.finish import finish_task
from pytask_service.worker.identity import new_worker_id
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.runner import run_in_process

TaskExecutor = Callable[[str, ClaimedTask], TaskOutcome]


@dataclass(frozen=True, slots=True)
class WorkedTask:
    id: UUID
    outcome: TaskOutcome


class Worker:
    def __init__(
        self,
        engine: Engine,
        registry_path: str,
        *,
        worker_id: str | None = None,
        executor: TaskExecutor = run_in_process,
    ) -> None:
        load_registry(registry_path)
        self.engine = engine
        self.registry_path = registry_path
        self.worker_id = worker_id or new_worker_id()
        self.executor = executor

    def run_once(self) -> WorkedTask | None:
        with Session(self.engine) as session, session.begin():
            claim = claim_next(session, self.worker_id)
        if claim is None:
            return None

        try:
            outcome = self.executor(self.registry_path, claim)
        except Exception as error:
            outcome = TaskOutcome.failure(error)

        with Session(self.engine) as session, session.begin():
            finish_task(session, claim, outcome)
        return WorkedTask(claim.id, outcome)
