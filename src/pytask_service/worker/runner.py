import multiprocessing
from multiprocessing.context import BaseContext

from pytask_service.worker.claim import ClaimedTask
from pytask_service.worker.outcome import TaskOutcome
from pytask_service.worker.process import execute_child


def run_in_process(
    registry_path: str,
    task: ClaimedTask,
    context: BaseContext | None = None,
) -> TaskOutcome:
    context = context or multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(  # type: ignore[attr-defined]
        target=execute_child,
        args=(registry_path, task.name, task.arguments, sender),
    )
    started = False
    try:
        try:
            process.start()
            started = True
        except (OSError, RuntimeError) as error:
            return TaskOutcome.failure(error)
        finally:
            sender.close()

        while True:
            if receiver.poll(0.1):
                try:
                    outcome = receiver.recv()
                except EOFError:
                    process.join()
                    return TaskOutcome.process_exit(process.exitcode)
                process.join()
                if isinstance(outcome, TaskOutcome):
                    return outcome
                return TaskOutcome.process_exit(process.exitcode)
            if not process.is_alive():
                process.join()
                if receiver.poll():
                    try:
                        outcome = receiver.recv()
                    except EOFError:
                        pass
                    else:
                        if isinstance(outcome, TaskOutcome):
                            return outcome
                return TaskOutcome.process_exit(process.exitcode)
    finally:
        receiver.close()
        if started and process.is_alive():
            process.join()
