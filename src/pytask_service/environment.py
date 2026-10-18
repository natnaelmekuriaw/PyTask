import os
from pathlib import Path

MAX_SECRET_BYTES = 8192


def read_secret(name: str) -> str:
    direct = os.environ.get(name, "").strip()
    filename = os.environ.get(name + "_FILE", "").strip()
    if direct and filename:
        raise ValueError(f"Set only one of {name} and {name}_FILE")
    if not filename:
        return direct
    try:
        path = Path(filename)
        if not path.is_file():
            raise OSError
        with path.open("rb") as stream:
            content = stream.read(MAX_SECRET_BYTES + 1)
        if len(content) > MAX_SECRET_BYTES:
            raise ValueError(f"{name}_FILE exceeds the supported size")
        value = content.decode("utf-8-sig").strip()
    except (OSError, UnicodeError):
        raise ValueError(f"Cannot read {name}_FILE as a UTF-8 file") from None
    if not value:
        raise ValueError(f"{name}_FILE must not be empty")
    return value
