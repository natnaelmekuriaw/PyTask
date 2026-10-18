import logging

from pytask_service.observability.events import log_event


def test_handler_failure_does_not_escape_the_event_boundary() -> None:
    class BrokenHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            raise OSError("destination unavailable")

    logger = logging.Logger("isolated", level=logging.INFO)
    logger.addHandler(BrokenHandler())
    log_event(logger, "task.attempt_finished", status="succeeded")
