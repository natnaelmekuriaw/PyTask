# Deployment configuration

Compose reads `.env` for interpolation. The Python application reads process
environment variables and the supported secret file; it does not load `.env`.
A host CLI connection uses localhost and the published port. Containers use
the `postgres` service name and port 5432.

`PYTASK_CONTAINER_DATABASE_URL` supplies the container URL in the base Compose
file. Its default matches the local development database. The application
receives that value as `PYTASK_DATABASE_URL`. Changing PostgreSQL's user,
password, or database also requires updating the full application URL.
Percent-encode reserved characters in URL credentials.

## Compose settings

| Setting | Default |
| --- | --- |
| `PYTASK_IMAGE` | `pytask:local` |
| `PYTASK_HTTP_PORT` | 8000 on localhost |
| `PYTASK_POSTGRES_PORT` | 15432 on localhost |
| `PYTASK_REGISTRY` | `pytask_service.example_tasks:registry` |
| `PYTASK_API_KEYS_SECRET_FILE` | `./.secrets/api-keys.json` for `compose.auth.yaml` |
| `PYTASK_API_STOP_GRACE` | 45s |
| `PYTASK_WORKER_STOP_GRACE` | 330s |
| `PYTASK_SCHEDULER_STOP_GRACE` | 15s |
| `PYTASK_API_MEMORY`, `PYTASK_WORKER_MEMORY` | 512m each |
| `PYTASK_SCHEDULER_MEMORY` | 256m |

## Application settings

| Setting | Default; supported range |
| --- | --- |
| `PYTASK_DB_POOL_SIZE` | 5; integer 1–100 |
| `PYTASK_DB_MAX_OVERFLOW` | 10; integer 0–100 |
| `PYTASK_DB_POOL_TIMEOUT` | 5 seconds; 0.1–60 |
| `PYTASK_DB_POOL_RECYCLE` | 1800 seconds; integer 30–86400 |
| `PYTASK_DB_CONNECT_TIMEOUT` | 5 seconds; integer 1–30 |
| `PYTASK_API_GRACEFUL_SECONDS` | 30; integer 1–300 |
| `PYTASK_API_CONCURRENCY` | 100; integer 1–10000 |
| `PYTASK_API_AUTH_MODE` | `required`; explicit `disabled` for local development |
| `PYTASK_API_KEYS`, `PYTASK_API_KEYS_FILE` | One credential manifest source; required in required mode |
| `PYTASK_API_DOCS_ENABLED` | `false` in required mode and base Compose; `true` in standalone disabled mode |
| `PYTASK_API_KEEP_ALIVE_SECONDS` | 5; integer 1–60 |
| `PYTASK_WORKER_POLL_SECONDS` | 0.5; 0.05–60 |
| `PYTASK_WORKER_LEASE_SECONDS` | 30; 1–3600 |
| `PYTASK_WORKER_HEARTBEAT_SECONDS` | 10; 0.05–1200 and at most one third of lease |
| `PYTASK_SCHEDULER_BATCH_SIZE` | 100; integer 1–1000 |
| `PYTASK_SCHEDULER_POLL_SECONDS` | 1; 0.05–60 |
| `PYTASK_PROBE_TIMEOUT_SECONDS` | 3; 0.1–5 for the HTTP probe |
| `PYTASK_ALEMBIC_CONFIG` | `alembic.ini`; image sets `/app/alembic.ini` |

Compose deliberately uses smaller pools than standalone defaults: API 5+5,
worker 2+0, scheduler 1+0. API pool settings are exposed through
`PYTASK_API_DB_POOL_SIZE` and `PYTASK_API_DB_MAX_OVERFLOW`. The other application
settings can be provided in a service's environment through an override file
when they are not already mapped by the base Compose definition.

Only the selected role's runtime options are parsed. Invalid worker settings
do not prevent an API probe. Numeric errors identify the setting and bound
without echoing its value. Database URLs are excluded from the settings repr.

Authentication is parsed only by the API and its startup preflight. Its
[configuration reference](authentication-configuration.md) defines manifest
limits, strict flags, source conflicts, and documentation access. Key manifests
are loaded once per API process; recreate all instances after changing records.
