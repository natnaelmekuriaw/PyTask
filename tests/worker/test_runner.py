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


def test_child_process_reports_handler_failure() -> None:
    task = ClaimedTask(
        id=uuid4(),
        name="demo.fail",
        arguments={"message": "expected failure"},
        worker_id="worker-one",
    )

    outcome = run_in_process("pytask_service.example_tasks:registry", task)

    assert not outcome.succeeded
    assert outcome.error is not None
    assert "RuntimeError: expected failure" in outcome.error


def test_child_exit_without_message_is_failure() -> None:
    task = ClaimedTask(
        id=uuid4(), name="test.crash", arguments={}, worker_id="worker-one"
    )

    outcome = run_in_process("tests.worker.sample_tasks:registry", task)

    assert not outcome.succeeded
    assert outcome.error is not None
    assert "exit code 7" in outcome.error
