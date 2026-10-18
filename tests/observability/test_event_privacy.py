from pytask_service.observability.events import safe_fields


def test_payloads_and_nested_values_never_enter_events() -> None:
    fields = safe_fields({
        "task_id": "task", "arguments": {"password": "secret"},
        "result": "secret", "error": "secret", "database_url": "secret",
        "status": {"nested": "secret"}, "worker_id": object(),
    })
    assert fields == {"task_id": "task"}


def test_nonfinite_numbers_and_long_strings_are_bounded() -> None:
    assert safe_fields({"duration_seconds": float("inf")}) == {}
    assert safe_fields({"duration_seconds": float("nan")}) == {}
    assert safe_fields({"worker_id": "x" * 1000}) == {"worker_id": "x" * 256}
