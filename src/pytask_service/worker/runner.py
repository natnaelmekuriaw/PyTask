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
    process = context.Process(
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
                    outcome = TaskOutcome.process_exit(process.exitcode)
                process.join()
                return outcome
            if not process.is_alive():
                process.join()
                if receiver.poll():
                    try:
                        return receiver.recv()
                    except EOFError:
                        pass
                return TaskOutcome.process_exit(process.exitcode)
    finally:
        receiver.close()
        if started and process.is_alive():
            process.join()
