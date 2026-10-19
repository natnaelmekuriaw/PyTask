import os
from collections.abc import Iterator

import pytest

from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.fixture(autouse=True)
def clean_deployment_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    names = (
        "PYTASK_DATABASE_URL_FILE",
        "PYTASK_ALEMBIC_CONFIG",
        "PYTASK_DB_POOL_SIZE",
        "PYTASK_DB_MAX_OVERFLOW",
        "PYTASK_DB_POOL_TIMEOUT",
        "PYTASK_DB_POOL_RECYCLE",
        "PYTASK_DB_CONNECT_TIMEOUT",
        "PYTASK_API_GRACEFUL_SECONDS",
        "PYTASK_API_CONCURRENCY",
        "PYTASK_API_KEEP_ALIVE_SECONDS",
        "PYTASK_WORKER_POLL_SECONDS",
        "PYTASK_WORKER_LEASE_SECONDS",
        "PYTASK_WORKER_HEARTBEAT_SECONDS",
        "PYTASK_SCHEDULER_BATCH_SIZE",
        "PYTASK_SCHEDULER_POLL_SECONDS",
        "PYTASK_PROBE_TIMEOUT_SECONDS",
    )
    for name in names:
        monkeypatch.delenv(name, raising=False)
    yield
