import logging

from fastapi import Request
from fastapi.security import HTTPBearer, SecurityScopes

from pytask_service.api.auth_errors import permission_error
from pytask_service.api.errors import APIError
from pytask_service.auth.permissions import Permission, Principal
from pytask_service.observability.events import log_event

logger = logging.getLogger(__name__)


class APIKeyAccess(HTTPBearer):
    async def __call__(
        self, request: Request, security_scopes: SecurityScopes
    ) -> Principal:
        principal = request.scope.get("pytask.principal")
        if not isinstance(principal, Principal):
            raise APIError(503, "authentication_unavailable", "Authentication is unavailable")
        required = {Permission(scope) for scope in security_scopes.scopes}
        if not principal.permits(required):
            log_event(logger, "auth.denied", credential_id=principal.key_id)
            raise permission_error(required)
        return principal


access = APIKeyAccess(
    scheme_name="APIKey", bearerFormat="ptk_<id>.<secret>", auto_error=False,
    description="Operator-issued API key. Permissions are listed on each operation.",
)
