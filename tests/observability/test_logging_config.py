import logging

import pytest

from pytask_service.observability.logging import StderrHandler, configure_logging


def test_configuration_does_not_replace_host_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = logging.getLogger("pytask_service")
    handlers, level, propagate = list(logger.handlers), logger.level, logger.propagate
    root_handlers = list(logging.getLogger().handlers)
    try:
        monkeypatch.setenv("PYTASK_LOG_LEVEL", " warning ")
        configure_logging()
        configure_logging()
        assert sum(isinstance(h, StderrHandler) for h in logger.handlers) == 1
        assert logger.level == logging.WARNING
        assert logging.getLogger().handlers == root_handlers
        assert not logger.propagate
        monkeypatch.setenv("PYTASK_LOG_LEVEL", "invalid secret")
        with pytest.raises(ValueError, match="PYTASK_LOG_LEVEL") as failure:
            configure_logging()
        assert "invalid secret" not in str(failure.value)
    finally:
        for handler in logger.handlers:
            if handler not in handlers:
                handler.close()
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate
