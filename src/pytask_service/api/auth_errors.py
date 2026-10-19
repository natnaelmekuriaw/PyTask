from fastapi.responses import JSONResponse

from pytask_service.api.errors import APIError, error_response
from pytask_service.auth.headers import AuthenticationError
from pytask_service.auth.permissions import Permission

REALM = 'Bearer realm="pytask"'


def authentication_response(error: AuthenticationError) -> JSONResponse:
    status, code, message, challenge = (
        401,
        "authentication_required",
        "Authentication required",
        REALM,
    )
    if error.reason == "invalid":
        code, message = "invalid_token", "Invalid authentication credentials"
        challenge += ', error="invalid_token"'
    elif error.reason == "malformed":
        status, code, message = (
            400,
            "invalid_request",
            "Ambiguous authentication headers",
        )
        challenge += ', error="invalid_request"'
    return error_response(
        status,
        code,
        message,
        headers={
            "WWW-Authenticate": challenge,
            "Cache-Control": "no-store",
        },
    )


def permission_error(required: set[Permission]) -> APIError:
    scopes = " ".join(sorted(required))
    challenge = f'{REALM}, error="insufficient_scope", scope="{scopes}"'
    return APIError(
        403,
        "insufficient_scope",
        "Credential does not grant the required permissions",
        headers={
            "WWW-Authenticate": challenge,
            "Cache-Control": "no-store",
        },
    )
