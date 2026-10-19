from time import sleep
from uuid import UUID

from sqlalchemy.engine import Engine

from pytask_service.benchmarks.deadline import Deadline
from pytask_service.benchmarks.observations import batch_complete
from pytask_service.benchmarks.workers import WorkerGroup


def wait_for_batch(
    engine: Engine, identities: tuple[UUID, ...], workers: WorkerGroup,
    deadline: Deadline, poll_interval: float,
) -> None:
    while True:
        deadline.check()
        workers.ensure_alive()
        if batch_complete(engine, identities):
            return
        sleep(min(poll_interval, deadline.remaining))

