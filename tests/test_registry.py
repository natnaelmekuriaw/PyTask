import sys
from types import ModuleType

import pytest

from pytask_service.registry import TaskRegistry, UnknownTaskError, load_registry


def test_registry_resolves_registered_function() -> None:
    registry = TaskRegistry()

    def add(left: int, right: int) -> int:
        return left + right

    registry.register("math.add", add)

    assert registry.get("math.add") is add


def test_registry_rejects_duplicate_names() -> None:
    registry = TaskRegistry()
    registry.register("math.add", lambda: None)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("math.add", lambda: None)


@pytest.mark.parametrize("name", ["", "Math.Add", ".hidden", "has space"])
def test_registry_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValueError, match="Invalid task name"):
        TaskRegistry().register(name, lambda: None)


def test_registry_reports_unknown_task() -> None:
    with pytest.raises(UnknownTaskError, match="Unknown task"):
        TaskRegistry().get("missing")


def test_registry_can_be_loaded_from_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("sample_registry")
    registry = TaskRegistry()
    setattr(module, "registry", registry)
    monkeypatch.setitem(sys.modules, module.__name__, module)

    assert load_registry("sample_registry:registry") is registry


def test_registry_path_must_name_an_attribute() -> None:
    with pytest.raises(ValueError, match="module:attribute"):
        load_registry("sample_registry")
