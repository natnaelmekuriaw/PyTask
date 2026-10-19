import json
from typing import Any

from pytask_service.auth.credentials import Credential
from pytask_service.auth.permissions import Permission
from pytask_service.environment import MAX_SECRET_BYTES

MAX_KEYS = 32


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate manifest field")
        result[name] = value
    return result


def validate_credentials(keys: tuple[Credential, ...]) -> None:
    if not 1 <= len(keys) <= MAX_KEYS:
        raise ValueError(f"Configure between 1 and {MAX_KEYS} API keys")
    if len({key.key_id for key in keys}) != len(keys):
        raise ValueError("API key IDs must be unique")
    if len({key.sha256 for key in keys}) != len(keys):
        raise ValueError("API key digests must be unique")


def parse_manifest(text: str) -> tuple[Credential, ...]:
    try:
        if len(text.encode("utf-8")) > MAX_SECRET_BYTES:
            raise ValueError
        data = json.loads(text, object_pairs_hook=_unique_object)
        if not isinstance(data, dict) or set(data) != {"version", "keys"}:
            raise ValueError
        if type(data["version"]) is not int or data["version"] != 1:
            raise ValueError
        records = data["keys"]
        if not isinstance(records, list) or not 1 <= len(records) <= MAX_KEYS:
            raise ValueError
        keys = []
        for record in records:
            if not isinstance(record, dict) or set(record) != {
                "id",
                "sha256",
                "scopes",
            }:
                raise ValueError
            scopes = record["scopes"]
            if (
                not isinstance(scopes, list)
                or not scopes
                or any(not isinstance(scope, str) for scope in scopes)
                or len(set(scopes)) != len(scopes)
            ):
                raise ValueError
            keys.append(
                Credential(
                    record["id"],
                    record["sha256"],
                    frozenset(Permission(scope) for scope in scopes),
                )
            )
        result = tuple(keys)
        validate_credentials(result)
        return result
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ValueError(
            "PYTASK_API_KEYS must be a valid version 1 key manifest"
        ) from None
