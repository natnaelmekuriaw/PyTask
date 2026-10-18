import math
from collections.abc import Callable
from threading import Event, Thread
from types import TracebackType

from pytask_service.worker.errors import LostClaimError


class LeaseKeeper:
    def __init__(self, renew: Callable[[], bool], interval: float) -> None:
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("Heartbeat interval must be positive and finite")
        self.cancel_event = Event()
        self._stop_event = Event()
        self._renew = renew
        self._interval = interval
        self._error: Exception | None = None
        self._thread = Thread(target=self._run, name="pytask-lease", daemon=True)

    def __enter__(self) -> "LeaseKeeper":
        self._thread.start()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._stop_event.set()
        self._thread.join(timeout=6)
        if self._thread.is_alive():
            self._error = RuntimeError("Lease renewal did not stop within six seconds")
            self.cancel_event.set()

    def raise_if_lost(self) -> None:
        if self.cancel_event.is_set():
            raise LostClaimError("Task lease renewal failed") from self._error

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                if not self._renew():
                    raise LostClaimError("Lease expired or its token changed")
            except Exception as error:
                self._error = error
                self.cancel_event.set()
                return
