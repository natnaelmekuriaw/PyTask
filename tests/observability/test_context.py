import pytest

from pytask_service.observability.context import bind_context, current_context


def test_nested_bindings_restore_the_outer_context_after_failure() -> None:
    assert current_context() == {}
    with bind_context(request_id="outer"):
        with pytest.raises(RuntimeError):
            with bind_context(request_id="inner", task_id="task"):
                assert current_context() == {"request_id": "inner", "task_id": "task"}
                raise RuntimeError("stop")
        assert current_context() == {"request_id": "outer"}
    assert current_context() == {}


def test_context_callers_cannot_mutate_active_bindings() -> None:
    with bind_context(request_id="original"):
        copied = current_context()
        copied["request_id"] = "changed"
        assert current_context()["request_id"] == "original"
