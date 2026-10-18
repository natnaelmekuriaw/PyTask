import json

from pytask_service.observability.serialization import snapshot_payload
from tests.observability.factories import empty_snapshot


def test_empty_snapshot_is_json_without_invented_timing_values() -> None:
    snapshot = empty_snapshot()
    payload = snapshot_payload(snapshot)
    encoded = json.dumps(payload, allow_nan=False)
    restored = json.loads(encoded)
    assert restored["observed_at"].endswith("+00:00")
    assert restored["window_start"] == snapshot.window_start.isoformat()
    assert restored["attempts"]["queue_wait"]["samples"] == 0
    assert restored["attempts"]["execution"]["max_seconds"] is None
    assert "arguments" not in encoded and "worker_id" not in encoded
