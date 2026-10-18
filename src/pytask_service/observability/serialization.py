from dataclasses import asdict

from pytask_service.observability.snapshot import MonitoringSnapshot


def snapshot_payload(snapshot: MonitoringSnapshot) -> dict[str, object]:
    payload: dict[str, object] = asdict(snapshot)
    payload["observed_at"] = snapshot.observed_at.isoformat()
    payload["window_start"] = snapshot.window_start.isoformat()
    return payload
