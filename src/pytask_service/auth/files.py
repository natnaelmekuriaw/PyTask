import os
from pathlib import Path

from pytask_service.auth.credentials import Credential
from pytask_service.auth.issuance import IssuedKey
from pytask_service.auth.manifest import parse_manifest
from pytask_service.environment import MAX_SECRET_BYTES


def _write_new(path: Path, text: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def write_key_files(issued: IssuedKey, token_file: Path, manifest_file: Path) -> None:
    if token_file.resolve() == manifest_file.resolve():
        raise ValueError("Token and manifest files must use different paths")
    try:
        _write_new(token_file, issued.token + "\n")
    except OSError:
        raise ValueError(
            "Cannot create token file; use a new path in an existing directory"
        ) from None
    try:
        _write_new(manifest_file, issued.manifest())
    except BaseException as error:
        token_file.unlink(missing_ok=True)
        if isinstance(error, OSError):
            raise ValueError(
                "Cannot create manifest file; existing files are preserved"
            ) from None
        raise


def read_manifest_file(path: Path) -> tuple[Credential, ...]:
    try:
        with path.open("rb") as stream:
            content = stream.read(MAX_SECRET_BYTES + 1)
        if len(content) > MAX_SECRET_BYTES:
            raise ValueError("Key manifest exceeds the supported size")
        return parse_manifest(content.decode("utf-8-sig"))
    except (OSError, UnicodeError):
        raise ValueError("Cannot read key manifest as a UTF-8 file") from None
