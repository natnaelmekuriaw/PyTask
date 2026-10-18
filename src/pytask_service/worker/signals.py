import signal
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Event


@contextmanager
def stop_on_signals(stop_event: Event) -> Iterator[None]:
    previous = {
        signum: signal.getsignal(signum) for signum in (signal.SIGINT, signal.SIGTERM)
    }

    def request_stop(signum: int, frame: object) -> None:
        stop_event.set()

    try:
        for signum in previous:
            signal.signal(signum, request_stop)
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
