import logging

from starlette._utils import get_route_path
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from pytask_service.api.auth_errors import authentication_response, permission_error
from pytask_service.api.errors import error_response
from pytask_service.auth.headers import AuthenticationError, parse_bearer
from pytask_service.auth.permissions import ALL_PERMISSIONS, Permission, Principal
from pytask_service.auth.settings import AuthMode, AuthSettings
from pytask_service.auth.store import KeyStore
from pytask_service.observability.events import log_event

HEALTH_PATHS = frozenset({"/health/live", "/health/ready"})
DOC_PATHS = frozenset({"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"})
logger = logging.getLogger(__name__)


class AuthenticationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = get_route_path(scope)
        if path in HEALTH_PATHS and scope["method"] in {"GET", "HEAD"}:
            await self.app(scope, receive, send)
            return

        async def protect(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers.add_vary_header("Authorization")
            await send(message)

        state = scope["app"].state
        settings = getattr(state, "auth_settings", None)
        if not isinstance(settings, AuthSettings):
            await error_response(
                503, "authentication_unavailable", "Authentication is unavailable"
            )(scope, receive, protect)
            return
        if settings.mode is AuthMode.DISABLED:
            principal = Principal(None, ALL_PERMISSIONS)
        else:
            store = getattr(state, "auth_store", None)
            if not isinstance(store, KeyStore):
                await error_response(
                    503, "authentication_unavailable", "Authentication is unavailable"
                )(scope, receive, protect)
                return
            try:
                principal = store.authenticate(parse_bearer(scope.get("headers", [])))
            except AuthenticationError as error:
                log_event(logger, "auth.rejected", auth_reason=error.reason)
                await authentication_response(error)(scope, receive, protect)
                return
        scope["pytask.principal"] = principal
        scope["pytask.credential_id"] = principal.key_id
        if path in DOC_PATHS:
            if not settings.docs_enabled or (
                settings.mode is AuthMode.REQUIRED and path != "/openapi.json"
            ):
                await error_response(404, "not_found", "Resource not found")(
                    scope, receive, protect
                )
                return
            if Permission.DOCS_READ not in principal.permissions:
                log_event(logger, "auth.denied", credential_id=principal.key_id)
                denied = permission_error({Permission.DOCS_READ})
                await error_response(
                    denied.status, denied.code, denied.message, headers=denied.headers
                )(scope, receive, protect)
                return
        await self.app(scope, receive, protect)
