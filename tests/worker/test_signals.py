import signal
from threading import Event

import pytest

from pytask_service.worker.signals import stop_on_signals


def test_signal_handler_requests_stop_and_is_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handlers: dict[signal.Signals, object] = {
        signal.SIGINT: signal.SIG_DFL,
        signal.SIGTERM: signal.SIG_DFL,
    }
    monkeypatch.setattr(signal, "getsignal", lambda signum: handlers[signum])

    def save_handler(signum: signal.Signals, handler: object) -> object:
        previous = handlers[signum]
        handlers[signum] = handler
        return previous

    monkeypatch.setattr(signal, "signal", save_handler)
    stop = Event()

    with stop_on_signals(stop):
        handler = handlers[signal.SIGINT]
        assert callable(handler)
        handler(signal.SIGINT, None)
        assert stop.is_set()

    assert handlers[signal.SIGINT] == signal.SIG_DFL
    assert handlers[signal.SIGTERM] == signal.SIG_DFL
