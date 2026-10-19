import re
from collections.abc import Iterable
from typing import Literal


class AuthenticationError(Exception):
    def __init__(self, reason: Literal["missing", "invalid", "malformed"]) -> None:
        super().__init__("Authentication could not be verified")
        self.reason = reason


def parse_bearer(headers: Iterable[tuple[bytes, bytes]]) -> str:
    values = [value for name, value in headers if name.lower() == b"authorization"]
    if not values:
        raise AuthenticationError("missing")
    if len(values) != 1:
        raise AuthenticationError("malformed")
    value = values[0]
    if len(value) > 128:
        raise AuthenticationError("invalid")
    match = re.fullmatch(rb"(?i:Bearer) +([A-Za-z0-9_.-]+)", value)
    if match is None:
        raise AuthenticationError("invalid")
    return match[1].decode("ascii")
