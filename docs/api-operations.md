# Operating the API locally

Use the [upgrade guide](api-upgrade.md) before starting a new checkout. The
application factory reads configuration when its lifespan starts, not when
the module is imported. `PYTASK_DATABASE_URL` and `PYTASK_REGISTRY` are required.
The registry is loaded once per API process.

Start Uvicorn bound to `127.0.0.1`, using the command in the
[examples](api-examples.md). API processes, workers, and schedulers must use
the same database. Workers need the task handlers referenced by submitted
work and saved schedules. Starting the API does not start those processes.

## Health and failures

`GET /health/live` confirms that the process can answer a request. It does
not query PostgreSQL. `GET /health/ready` runs bounded reads against the task,
attempt, and schedule tables, checking that their mapped columns are
accessible. Readiness does not verify that every index or migration revision
is current; use `alembic check` as part of upgrades.

A database outage produces a 503 error envelope. Schema errors can produce
the same readiness failure. Check server logs and your migration state.
Malformed input and unknown handler names are client errors and do not
enqueue tasks. A duplicated schedule name produces 409.

Task creation is not an idempotent HTTP operation. If a response is lost,
inspect known task IDs and application business records before deciding
whether to submit again. Handler idempotency remains necessary even for one
submission because execution uses retries and lease recovery.

## Shutdown and ownership

Ctrl+C asks Uvicorn to finish active requests and shut down the application.
The application disposes its own SQLAlchemy engine during lifespan cleanup.
Each request owns its session and each write commits inside its handler.
An engine explicitly supplied to the factory is managed by its caller; this
is how isolated integration tests share a database engine without the app
disposing it.

Multiple API processes may use the same PostgreSQL database. Each owns a
separate connection pool and registry instance. Size connection capacity
across API processes, workers, and schedulers together when increasing their
counts. The new read indexes add storage and write maintenance costs; this
stage does not include benchmark claims about throughput.

## Proxy and access scope

When deploying behind a trusted proxy with a path prefix, configure Uvicorn's
root path to match that prefix. Created-resource Location headers include
the mounted root path. Configure forwarding and trust at the proxy/server
boundary; the application does not infer permissions from forwarded headers.

Authentication, authorization, and tenant separation are outside this stage.
Keep this API on localhost for development. It exposes task arguments,
results, errors, and controls that submit work. Public hosting needs an
access-control design before enabling untrusted access. Browser CORS is not
enabled, and does not provide authentication.

See the [contract](api-contract.md) for the supported HTTP surface and limits.

## Monitoring operations

Apply the [monitoring migration](monitoring-upgrade.md) before running this
version. Readiness now also checks access to the attempt eligibility column.
The [summary endpoint](monitoring.md) and `pytask-service stats` read persisted
queue state; neither proves that a worker or scheduler process is alive.

API startup configures service JSON events on stderr. `PYTASK_LOG_LEVEL`
defaults to INFO. Responses include a generated request identifier, which also
appears in submission and request events. See the [event reference](operational-logs.md)
for correlation, privacy boundaries, and log level behavior.

The aggregate statement runs in a read-only transaction with statement and
lock timeouts. Keep polling frequency proportional to measured database cost.
Counts are based on retained rows and observation windows; they are not
process-local or monotonic counters. See [troubleshooting](monitoring-troubleshooting.md)
for interpreting backlog and timing gaps.
