from pytask_service.worker.outcome import TaskOutcome


def test_success_keeps_a_json_result() -> None:
    outcome = TaskOutcome.success({"items": [1, 2, 3]})

    assert outcome.succeeded
    assert outcome.result == {"items": [1, 2, 3]}
    assert outcome.error is None
