import json
from email.message import Message
from typing import IO
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pytask_service.runtime.schema import RuntimeFailure

MAX_PROBE_BYTES = 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> None:
        return None


def probe_api(timeout: float = 3) -> None:
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(
            "http://127.0.0.1:8000/health/ready", timeout=timeout
        ) as response:
            if response.status != 200:
                raise RuntimeFailure("API readiness returned an unsuccessful status")
            payload = response.read(MAX_PROBE_BYTES + 1)
    except HTTPError as error:
        raise RuntimeFailure(f"API readiness returned HTTP {error.code}") from None
    except (URLError, OSError):
        raise RuntimeFailure("API readiness check failed") from None
    if len(payload) > MAX_PROBE_BYTES:
        raise RuntimeFailure("API readiness response exceeds the supported size")
    try:
        body = json.loads(payload)
    except (ValueError, UnicodeError):
        raise RuntimeFailure("API readiness response is invalid") from None
    if body != {"status": "ok"}:
        raise RuntimeFailure("API readiness did not confirm readiness")
