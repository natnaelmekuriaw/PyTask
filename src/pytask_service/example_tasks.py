import time

from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def add(left: int, right: int) -> int:
    return left + right


def greet(name: str) -> str:
    return f"Hello, {name}"


def fail(message: str) -> None:
    raise RuntimeError(message)


def pause(seconds: float) -> str:
    time.sleep(seconds)
    return "finished"


registry.register("math.add", add)
registry.register("demo.greet", greet)
registry.register("demo.fail", fail)
registry.register("demo.pause", pause)
