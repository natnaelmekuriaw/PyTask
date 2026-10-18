import multiprocessing
from multiprocessing.context import BaseContext
from threading import Event
from time import monotonic

from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.errors import LostClaimError
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.process import execute_child
from pytask_service.worker.termination import stop_process


def run_in_process(
    registry_path: str,
    task: ClaimedTask,
    cancel_event: Event | None = None,
    *,
    context: BaseContext | None = None,
) -> TaskOutcome:
    if cancel_event is not None and cancel_event.is_set():
        raise LostClaimError(f"Task lease was lost before execution: {task.id}")
    context = context or multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(  # type: ignore[attr-defined]
        target=execute_child,
        args=(registry_path, task.name, task.arguments, sender),
    )
    started = False
    deadline = monotonic() + task.timeout_seconds
    try:
        try:
            process.start()
            started = True
        except (OSError, RuntimeError) as error:
            return TaskOutcome.failure(error)
        finally:
            sender.close()

        outcome: TaskOutcome | None = None
        pipe_open = True
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise LostClaimError(f"Task lease was lost: {task.id}")
            remaining = deadline - monotonic()
            if remaining <= 0:
                return TaskOutcome.timeout(task.timeout_seconds)
            if pipe_open and receiver.poll(min(0.05, remaining)):
                try:
                    message = receiver.recv()
                except (EOFError, OSError):
                    pass
                else:
                    if isinstance(message, TaskOutcome):
                        outcome = message
                pipe_open = False
            if not process.is_alive():
                process.join()
                if outcome is None and pipe_open and receiver.poll():
                    try:
                        message = receiver.recv()
                    except (EOFError, OSError):
                        pass
                    else:
                        if isinstance(message, TaskOutcome):
                            outcome = message
                return outcome or TaskOutcome.process_exit(process.exitcode)
            if not pipe_open:
                process.join(timeout=min(0.05, remaining))
    finally:
        receiver.close()
        if started:
            stop_process(process)
        process.close()
