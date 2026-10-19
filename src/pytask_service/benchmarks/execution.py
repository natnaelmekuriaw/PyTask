from time import perf_counter

from sqlalchemy.engine import Engine

from pytask_service.benchmarks.cases import CaseSpec
from pytask_service.benchmarks.catalog import work_item
from pytask_service.benchmarks.database import BenchmarkDatabase
from pytask_service.benchmarks.deadline import Deadline
from pytask_service.benchmarks.metrics import measure
from pytask_service.benchmarks.monitor import wait_for_batch
from pytask_service.benchmarks.observations import observe, validate_results
from pytask_service.benchmarks.options import BenchmarkOptions
from pytask_service.benchmarks.results import CaseResult
from pytask_service.benchmarks.submission import submit_batch
from pytask_service.benchmarks.workers import WorkerGroup
from pytask_service.config import Settings
from pytask_service.policy import TaskPolicy


def run_case(admin: Engine, settings: Settings, case: CaseSpec, options: BenchmarkOptions) -> CaseResult:
    items = tuple(work_item(case.workload, index, options) for index in range(options.tasks))
    warmup = tuple(work_item(case.workload, index, options) for index in range(options.warmup))
    policy = TaskPolicy(max_attempts=1, timeout_seconds=options.task_timeout)
    with BenchmarkDatabase(admin, settings) as database:
        engine = database.connected_engine()
        with WorkerGroup(
            settings, database.schema, case.workers, startup_timeout=options.case_timeout,
            shutdown_timeout=options.task_timeout + 5,
        ) as workers:
            if warmup:
                deadline = Deadline(options.case_timeout)
                warmup_ids = submit_batch(engine, warmup, policy, check_deadline=deadline.check)
                wait_for_batch(engine, warmup_ids, workers, deadline, options.poll_interval)
                validate_results(warmup, warmup_ids, observe(engine, warmup_ids))
            deadline = Deadline(options.case_timeout)
            started = perf_counter()
            identities = submit_batch(engine, items, policy, check_deadline=deadline.check)
            submitted = perf_counter() - started
            wait_for_batch(engine, identities, workers, deadline, options.poll_interval)
            elapsed = perf_counter() - started
            observed = observe(engine, identities)
            validate_results(items, identities, observed)
            metrics = measure(observed, elapsed, submitted)
        return CaseResult(case, metrics)

