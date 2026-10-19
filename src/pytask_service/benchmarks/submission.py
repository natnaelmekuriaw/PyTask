from collections.abc import Callable
from uuid import UUID

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.benchmarks.catalog import WorkItem
from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.workloads import registry
from pytask_service.policy import TaskPolicy
from pytask_service.tasks import submit_task


def submit_batch(
    engine: Engine,
    items: tuple[WorkItem, ...],
    policy: TaskPolicy,
    *,
    check_deadline: Callable[[], None],
) -> tuple[UUID, ...]:
    identities = []
    for item in items:
        check_deadline()
        with Session(engine) as session, session.begin():
            identities.append(
                submit_task(
                    session,
                    registry,
                    item.name,
                    item.arguments,
                    policy=policy,
                )
            )
    if len(set(identities)) != len(identities):
        raise BenchmarkFailure("duplicate_submission_identity")
    return tuple(identities)
