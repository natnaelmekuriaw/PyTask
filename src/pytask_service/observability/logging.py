import logging
import os
import sys
from threading import RLock
from typing import TextIO

from pytask_service.observability.formatter import EventFormatter

_lock = RLock()


class StderrHandler(logging.StreamHandler[TextIO]):
    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stderr
        super().emit(record)


def configure_logging() -> None:
    level = os.environ.get("PYTASK_LOG_LEVEL", "INFO").strip().upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("PYTASK_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
    logger = logging.getLogger("pytask_service")
    with _lock:
        if not any(isinstance(handler, StderrHandler) for handler in logger.handlers):
            handler = StderrHandler()
            handler.setFormatter(EventFormatter())
            logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
