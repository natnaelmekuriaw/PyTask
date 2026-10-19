import logging
import signal
import sys
from multiprocessing.synchronize import Event

from pytask_service.benchmarks.engine import check_scope, scoped_engine
from pytask_service.config import Settings
from pytask_service.worker.service import Worker

REGISTRY_PATH = "pytask_service.benchmarks.workloads:registry"


def worker_main(
    settings: Settings, schema: str, stopped: Event, ready: Event, identity: str
) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.getLogger("pytask_service").setLevel(logging.WARNING)
    engine = None
    try:
        engine = scoped_engine(settings, schema)
        check_scope(engine, schema)
        worker = Worker(engine, REGISTRY_PATH, worker_id=identity)
        ready.set()
        while not stopped.is_set():
            if worker.run_once() is None:
                stopped.wait(0.01)
    except Exception as error:
        print(f"Benchmark worker failed: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        if engine is not None:
            engine.dispose()
