from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def multiply(left: int, right: int) -> int:
    return left * right


registry.register("math.multiply", multiply)
