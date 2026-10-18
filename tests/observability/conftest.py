import logging
from collections.abc import Iterator

import pytest

from tests.worker.conftest import isolated_engine as isolated_engine


@pytest.fixture
def event_records() -> Iterator[list[logging.LogRecord]]:
    records: list[logging.LogRecord] = []

    class Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("pytask_service")
    collector = Collector()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(collector)
    try:
        yield records
    finally:
        logger.removeHandler(collector)
        logger.setLevel(original_level)
