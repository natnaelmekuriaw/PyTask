import os
import time
from threading import Thread

from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def crash() -> None:
    os._exit(7)


registry.register("test.crash", crash)


def sleep(seconds: float) -> None:
    time.sleep(seconds)


registry.register("test.sleep", sleep)


def linger() -> str:
    Thread(target=time.sleep, args=(30,)).start()
    return "returned"


registry.register("test.linger", linger)
