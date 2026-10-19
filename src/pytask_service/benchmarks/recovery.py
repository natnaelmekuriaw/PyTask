from time import perf_counter

from sqlalchemy.engine import Engine

from pytask_service.benchmarks.catalog import work_item
from pytask_service.benchmarks.database import BenchmarkDatabase
from pytask_service.benchmarks.deadline import Deadline
from pytask_service.benchmarks.monitor import wait_for_batch
from pytask_service.benchmarks.observations import observe, validate_results
from pytask_service.benchmarks.options import BenchmarkOptions, Workload
from pytask_service.benchmarks.recovery_history import verify_recovery
from pytask_service.benchmarks.results import RecoveryResult
from pytask_service.benchmarks.submission import submit_batch
from pytask_service.benchmarks.victim import crash_worker
from pytask_service.benchmarks.workers import WorkerGroup
from pytask_service.config import Settings
from pytask_service.policy import TaskPolicy


def run_recovery(admin: Engine, settings: Settings, options: BenchmarkOptions) -> RecoveryResult:
    with BenchmarkDatabase(admin, settings) as database:
        engine = database.connected_engine()
        deadline = Deadline(options.case_timeout)
        items = (work_item(Workload.NOOP, 0, options),)
        identities = submit_batch(
            engine, items, TaskPolicy(
                max_attempts=2, timeout_seconds=options.task_timeout,
                retry_base_seconds=0.01, retry_max_seconds=0.01,
            ), check_deadline=deadline.check,
        )
        crash_worker(settings, database.schema, deadline.remaining)
        started = perf_counter()
        with WorkerGroup(
            settings, database.schema, 1, startup_timeout=deadline.remaining,
            shutdown_timeout=options.task_timeout + 5,
        ) as workers:
            wait_for_batch(engine, identities, workers, deadline, options.poll_interval)
            elapsed = perf_counter() - started
            observed = observe(engine, identities)
            validate_results(items, identities, observed)
            outcomes = verify_recovery(observed)
        return RecoveryResult(True, elapsed, outcomes)

