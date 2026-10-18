import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pytask_service.scheduling.time import as_utc


class InvalidCursor(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Position:
    created_at: datetime
    id: UUID


def cursor_scope(resource: str, **filters: str | bool | None) -> str:
    data = json.dumps({"resource": resource, "filters": filters}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def encode_cursor(position: Position, scope: str) -> str:
    payload = {"v": 1, "scope": scope, "at": as_utc(position.created_at).isoformat(), "id": str(position.id)}
    encoded = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")
