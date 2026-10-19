from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from pytask_service.benchmarks.catalog import WorkItem
from pytask_service.benchmarks.errors import BenchmarkFailure
from pytask_service.benchmarks.records import AttemptRecord, Observation, TaskRecord
from pytask_service.db.models import Task, TaskAttempt


def batch_complete(engine: Engine, identities: tuple[UUID, ...]) -> bool:
    with Session(engine) as session:
        states = list(
            session.scalars(select(Task.status).where(Task.id.in_(identities)))
        )
    if len(states) != len(identities):
        raise BenchmarkFailure("missing_tasks")
    if any(state == "failed" for state in states):
        raise BenchmarkFailure("task_failed")
    if any(state not in {"pending", "running", "succeeded"} for state in states):
        raise BenchmarkFailure("invalid_task_status")
    return all(state == "succeeded" for state in states)


def observe(engine: Engine, identities: tuple[UUID, ...]) -> Observation:
    with Session(engine) as session:
        tasks = (
            session.execute(
                select(
                    Task.id,
                    Task.status,
                    Task.created_at,
                    Task.finished_at,
                    Task.attempt_count,
                    Task.result,
                ).where(Task.id.in_(identities))
            )
            .tuples()
            .all()
        )
        attempts = (
            session.execute(
                select(
                    TaskAttempt.id,
                    TaskAttempt.task_id,
                    TaskAttempt.number,
                    TaskAttempt.status,
                    TaskAttempt.queued_at,
                    TaskAttempt.started_at,
                    TaskAttempt.finished_at,
                ).where(TaskAttempt.task_id.in_(identities))
            )
            .tuples()
            .all()
        )
    return Observation(
        tuple(TaskRecord(*row) for row in tasks),
        tuple(AttemptRecord(*row) for row in attempts),
    )


def validate_results(
    items: tuple[WorkItem, ...], identities: tuple[UUID, ...], observed: Observation
) -> None:
    actual = {task.id: task.result for task in observed.tasks}
    if (
        len(items) != len(identities)
        or len(set(identities)) != len(identities)
        or len(actual) != len(observed.tasks)
        or set(actual) != set(identities)
    ):
        raise BenchmarkFailure("invalid_result_population")
    for task_id, item in zip(identities, items, strict=True):
        value = actual[task_id]
        if type(value) is not type(item.expected) or value != item.expected:
            raise BenchmarkFailure("unexpected_task_result")
