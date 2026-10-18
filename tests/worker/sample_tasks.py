import os

from pytask_service.registry import TaskRegistry


registry = TaskRegistry()


def crash() -> None:
    os._exit(7)


registry.register("test.crash", crash)
