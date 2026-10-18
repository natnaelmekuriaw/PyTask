import math
from collections.abc import Callable
from threading import Condition, Event, Thread
from time import monotonic
from types import TracebackType

from pytask_service.worker.errors import LostClaimError


class LeaseKeeper:
    def __init__(
        self, renew: Callable[[], bool], interval: float,
        *, lease_seconds: float = 30, initial_deadline: float | None = None,
    ) -> None:
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("Heartbeat interval must be positive and finite")
        if not math.isfinite(lease_seconds) or lease_seconds <= interval:
            raise ValueError("Lease duration must be finite and exceed the heartbeat interval")
        self.cancel_event = Event()
        self._stop_event = Event()
        self._renew = renew
        self._interval = interval
        self._lease_seconds = lease_seconds
        self._deadline = initial_deadline if initial_deadline is not None else monotonic() + lease_seconds
        self._condition = Condition()
        self._error: Exception | None = None
        self._thread = Thread(target=self._run, name="pytask-lease", daemon=True)
        self._watchdog = Thread(target=self._watch_deadline, name="pytask-watchdog", daemon=True)

    def __enter__(self) -> "LeaseKeeper":
        self._watchdog.start()
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._stop_event.set()
        with self._condition:
            self._condition.notify_all()
        self._watchdog.join(timeout=1)
        self._thread.join(timeout=6)
        if self._thread.is_alive():
            self._error = RuntimeError("Lease renewal did not stop within six seconds")
            self.cancel_event.set()

    def raise_if_lost(self) -> None:
        if self.cancel_event.is_set():
            raise LostClaimError("Task lease renewal failed") from self._error

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            started = monotonic()
            try:
                if not self._renew():
                    raise LostClaimError("Lease expired or its token changed")
            except Exception as error:
                with self._condition:
                    if not self.cancel_event.is_set():
                        self._error = error
                        self.cancel_event.set()
                    self._condition.notify_all()
                return
            with self._condition:
                if self.cancel_event.is_set() or self._stop_event.is_set():
                    return
                if monotonic() >= self._deadline:
                    self._error = LostClaimError("Local lease deadline elapsed")
                    self.cancel_event.set()
                    self._condition.notify_all()
                    return
                self._deadline = started + self._lease_seconds
                self._condition.notify_all()

    def _watch_deadline(self) -> None:
        with self._condition:
            while not self._stop_event.is_set() and not self.cancel_event.is_set():
                remaining = self._deadline - monotonic()
                if remaining <= 0:
                    self._error = LostClaimError("Local lease deadline elapsed")
                    self.cancel_event.set()
                    return
                self._condition.wait(remaining)
