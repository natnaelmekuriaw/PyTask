from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def add(left: int, right: int) -> int:
    return left + right


def greet(name: str) -> str:
    return f"Hello, {name}"


def fail(message: str) -> None:
    raise RuntimeError(message)


registry.register("math.add", add)
registry.register("demo.greet", greet)
registry.register("demo.fail", fail)
