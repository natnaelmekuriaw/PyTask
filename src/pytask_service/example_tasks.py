from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def add(left: int, right: int) -> int:
    return left + right


def greet(name: str) -> str:
    return f"Hello, {name}"


registry.register("math.add", add)
registry.register("demo.greet", greet)
