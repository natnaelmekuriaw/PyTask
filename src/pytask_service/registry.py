import importlib
import inspect
import re
from collections.abc import Callable


TaskHandler = Callable[..., object]
_TASK_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,127}\Z")


class UnknownTaskError(LookupError):
    pass


class TaskRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, TaskHandler] = {}

    def register(self, name: str, handler: TaskHandler) -> None:
        if not _TASK_NAME.fullmatch(name):
            raise ValueError(f"Invalid task name: {name!r}")
        if name in self._handlers:
            raise ValueError(f"Task already registered: {name}")
        if not callable(handler):
            raise TypeError("Task handler must be callable")
        try:
            inspect.signature(handler)
        except (TypeError, ValueError) as exc:
            raise TypeError("Task handler must have an inspectable signature") from exc
        self._handlers[name] = handler

    def get(self, name: str) -> TaskHandler:
        try:
            return self._handlers[name]
        except KeyError as exc:
            raise UnknownTaskError(f"Unknown task: {name}") from exc


def load_registry(path: str) -> TaskRegistry:
    module_name, separator, attribute_name = path.partition(":")
    if not separator or not module_name or not attribute_name:
        raise ValueError("PYTASK_REGISTRY must be in module:attribute form")

    try:
        module = importlib.import_module(module_name)
        registry = getattr(module, attribute_name)
    except (ImportError, AttributeError) as exc:
        raise ValueError(f"Cannot load task registry: {path}") from exc

    if not isinstance(registry, TaskRegistry):
        raise TypeError(f"{path} is not a TaskRegistry")
    return registry
