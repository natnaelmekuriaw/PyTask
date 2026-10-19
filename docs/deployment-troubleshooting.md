# Deployment troubleshooting

## Services exit before starting

Read the service logs:

```powershell
docker compose --profile runtime logs --tail 100 api worker scheduler
```

Configuration errors name the relevant environment variable. A registry
failure happens before opening the database. A schema mismatch requires
checking the image/database pair and running the explicit migration command.
The restart policy allows three failure retries, rather than an endless loop.
PostgreSQL query failures include a validated SQLSTATE code when the driver
provides one. For example, 42703 identifies a missing column; diagnostics
exclude query text and credentials.

Check connectivity using the operator image:

```powershell
docker compose --profile tools run --rm ops cli check-db
```

Check schema compatibility:

```powershell
docker compose --profile tools run --rm ops check
```

## The host CLI works but containers cannot connect

Inside a container, localhost refers to that container. Use
`PYTASK_CONTAINER_DATABASE_URL` with the `postgres` service name for the
supplied database. Keep the host CLI URL on localhost and port 15432.
Compose's `.env` interpolation does not configure a separate PowerShell window.

## Ports are unavailable on Windows

Change `PYTASK_HTTP_PORT` or `PYTASK_POSTGRES_PORT` in `.env` to a free host
port. The API's container port stays 8000, and PostgreSQL stays 5432.
Internal health checks do not need changing.

## The API is unhealthy

The probe checks readiness, not just an open port. Inspect API logs and the
database schema. HTTP 503 usually means database/schema access is unavailable.
The probe refuses redirects and malformed or oversized success bodies.
Ambient proxy variables are ignored for the loopback readiness request.

## Workers are healthy but work is not completing

Worker and scheduler probes check database dependencies. Compare ready queue
age and attempt history, confirm the registry matches the image used for
submission, and inspect process events. A health label is not proof of loop
progress. Check memory limits when tasks exit without results.

## Configuration changes are not applied

A restart alone does not apply a changed Compose environment. Recreate the
affected containers after reviewing the new configuration:

```powershell
docker compose --profile runtime up -d --no-build --force-recreate
```

Allow the configured worker stop grace period. Updating a password file for
an existing PostgreSQL volume does not rotate the stored database password.

## Builds fail while resolving dependencies

The image uses Linux Python 3.12 and binary runtime wheels. Review
`constraints/runtime.txt`, target architecture, package-index access, and
the build output. The build backend requires setuptools 77 or newer.
Do not bypass dependency constraints merely to obtain a successful image;
resolve and verify a coherent updated set.
