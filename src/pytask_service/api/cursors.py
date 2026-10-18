import base64
import hashlib
import json
import re
import binascii
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pytask_service.scheduling.time import as_utc, parse_timestamp


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


def decode_cursor(raw: str, scope: str) -> Position:
    try:
        if len(raw) > 1024 or not re.fullmatch(r"[A-Za-z0-9_-]+", raw):
            raise ValueError
        data = base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True)
        payload = json.loads(data)
        if not isinstance(payload, dict) or set(payload) != {"v", "scope", "at", "id"}:
            raise ValueError
        if type(payload["v"]) is not int or payload["v"] != 1 or payload["scope"] != scope:
            raise ValueError
        if not isinstance(payload["at"], str) or not isinstance(payload["id"], str):
            raise ValueError
        return Position(parse_timestamp(payload["at"]), UUID(payload["id"]))
    except (ValueError, TypeError, UnicodeError, binascii.Error) as error:
        raise InvalidCursor("Invalid pagination cursor") from error
