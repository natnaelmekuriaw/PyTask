from uuid import uuid4

from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.runner import run_in_process


def test_child_process_returns_task_result() -> None:
    task = ClaimedTask(
        id=uuid4(),
        name="math.add",
        arguments={"left": 2, "right": 3},
        worker_id="worker-one",
    )

    outcome = run_in_process("pytask_service.example_tasks:registry", task)

    assert outcome.succeeded
    assert outcome.result == 5
