from pytask_service.runtime.roles import Role
from pytask_service.runtime.scheduler_command import scheduler_command
from pytask_service.runtime.scheduler_options import SchedulerOptions
from pytask_service.runtime.worker_command import worker_command
from pytask_service.runtime.worker_options import WorkerOptions


def test_worker_policy_is_passed_without_single_shot_execution() -> None:
    command = worker_command(WorkerOptions(0.2, 12, 3))
    assert command.role is Role.WORKER
    assert command.argv[2:4] == ("pytask_service.cli", "worker")
    assert "--once" not in command.argv
    assert command.argv[command.argv.index("--lease-seconds") + 1] == "12"
    assert command.argv[command.argv.index("--heartbeat-seconds") + 1] == "3"


def test_scheduler_batch_and_polling_are_forwarded() -> None:
    command = scheduler_command(SchedulerOptions(25, 0.5))
    assert command.role is Role.SCHEDULER
    assert command.argv[command.argv.index("--batch-size") + 1] == "25"
    assert command.argv[command.argv.index("--poll-interval") + 1] == "0.5"
