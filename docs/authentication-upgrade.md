# Upgrade to API authentication

This changes the HTTP access contract. API startup requires a manifest unless
local `disabled` mode is explicitly selected. No new database migration is added.

1. Stop or remove API traffic while changing access configuration.
2. Refresh the editable Python installation under the runtime constraints.
3. Generate client keys and review their permissions.
4. Configure a direct manifest or the authentication Compose overlay.
5. Update clients to send `Authorization: Bearer <token>`.
6. Rebuild the image and recreate API processes.
7. Confirm health succeeds, anonymous API requests return 401, and authorized
   operations work.
8. Run the final checks and full PostgreSQL test suite.

See the [acceptance commands](authentication-verification.md).

## Compatibility

Workers and schedulers keep running their existing database queue. CLI commands
and migration tools do not load HTTP credentials. Existing tasks, schedules,
attempt history, and delivery guarantees keep their current schema and behavior.

Missing credentials are rejected before request-body buffering. Valid credentials
reach normal JSON and field validation; missing operation permissions return 403
before database session dependencies run. JSON syntax can still fail while the
framework parses an authenticated request.

Unknown paths and unsupported methods require authentication too. Interactive
documentation is hidden in required mode; downloading enabled OpenAPI JSON
requires `docs:read`.

## Local fallback

For a localhost-only environment, set `PYTASK_API_AUTH_MODE=disabled` and remove
both key manifest sources. Recreate the API to apply it. Do not retain this
setting in a hosted deployment. Rolling back application code can remove access
checks; keep ingress restricted throughout a rollback.

