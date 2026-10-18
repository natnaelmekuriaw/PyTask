import os
import time

from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def crash() -> None:
    os._exit(7)


registry.register("test.crash", crash)


def sleep(seconds: float) -> None:
    time.sleep(seconds)


registry.register("test.sleep", sleep)
