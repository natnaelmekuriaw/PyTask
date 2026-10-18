from pytask_service.worker.identity import new_worker_id


def test_worker_ids_are_distinct_and_fit_storage() -> None:
    first = new_worker_id()
    second = new_worker_id()

    assert first != second
    assert 0 < len(first) <= 128
    assert first.count(":") == 2
