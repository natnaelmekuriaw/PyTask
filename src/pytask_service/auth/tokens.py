import base64
import hashlib
import re
import secrets

KEY_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}", re.ASCII)
TOKEN = re.compile(r"ptk_([a-z0-9][a-z0-9_-]{0,47})\.([A-Za-z0-9_-]{43})", re.ASCII)
MAX_TOKEN_LENGTH = 96


def validate_key_id(key_id: str) -> None:
    if not isinstance(key_id, str) or KEY_ID.fullmatch(key_id) is None:
        raise ValueError(
            "Key ID must contain 1 to 48 lowercase letters, digits, _ or -"
        )


def generate_token(key_id: str) -> str:
    validate_key_id(key_id)
    return f"ptk_{key_id}.{secrets.token_urlsafe(32)}"


def token_key_id(token: str) -> str | None:
    if len(token) > MAX_TOKEN_LENGTH:
        return None
    match = TOKEN.fullmatch(token)
    if match is None:
        return None
    secret = match[2]
    decoded = base64.urlsafe_b64decode(secret + "=")
    if base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=") != secret:
        return None
    return match[1]


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()
