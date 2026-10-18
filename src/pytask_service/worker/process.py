import signal
from multiprocessing.connection import Connection

from pytask_service.registry import load_registry
from pytask_service.worker.outcome import TaskOutcome


def execute_child(
    registry_path: str,
    task_name: str,
    arguments: dict[str, object],
    sender: Connection,
) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        registry = load_registry(registry_path)
        result = registry.get(task_name)(**arguments)
        outcome = TaskOutcome.success(result)
    except Exception as error:
        outcome = TaskOutcome.failure(error)

    try:
        sender.send(outcome)
    finally:
        sender.close()
