# PyTask

PyTask is a PostgreSQL-backed task execution service for registered Python
functions, with task claiming, retries, leases, and crash recovery.

The current stage supports registering named functions, submitting tasks with
JSON arguments, and running them in background worker processes. Multiple
workers can safely claim tasks from the same PostgreSQL queue. Failed attempts
use configurable backoff, and expired leases allow another worker to recover
interrupted work. Every execution attempt has its own history record.
Delayed tasks and fixed-interval schedules use the same queue and reliability
policy.

## Requirements

- Python 3.12 or newer
- Docker with Compose, or an existing PostgreSQL instance

## Local setup

The commands below use PowerShell. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -c constraints/runtime.txt -e ".[dev]"
docker compose up -d postgres
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
.\.venv\Scripts\pytask-service check-db
.\.venv\Scripts\alembic upgrade head
```

`check-db` prints `Database connection OK` when it can connect. Run it before
migrations to catch connection problems early. The credentials
in `compose.yaml` are for local development only. For another PostgreSQL
instance, set `PYTASK_DATABASE_URL` to its connection URL using the
`postgresql+psycopg` driver.

Run the checks with:

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\pytest -q
```

The PostgreSQL integration tests run when `PYTASK_DATABASE_URL` is set and skip
otherwise. Run `alembic upgrade head` before the full test suite.

For an existing checkout, stop API processes, workers, and schedulers before
migrating. Follow the [API upgrade guide](docs/api-upgrade.md) for dependency
updates and current migration checks. Earlier changes are described in the
[scheduling upgrade guide](docs/scheduling-upgrade.md) and the
[reliability upgrade guide](docs/reliability-upgrade.md).

## Submit a task

The [example registry](src/pytask_service/example_tasks.py) contains a
`math.add` task. Point the CLI at that registry and submit the example payload:

```powershell
$env:PYTASK_REGISTRY = "pytask_service.example_tasks:registry"
.\.venv\Scripts\pytask-service submit math.add --args-file examples/math-add.json
```

The command prints a task ID and `pending` status. Copy the ID from the output
to inspect the stored record:

```powershell
.\.venv\Scripts\pytask-service status "PASTE_TASK_ID_HERE"
```

You can also pass a JSON object directly with `--args`. `--args-file` is easier
to use across shells. The arguments must be a JSON object of keyword arguments
accepted by the registered function. The CLI rejects unknown task names,
invalid arguments, and payloads larger than 64 KiB.

Register application tasks in a Python module that exports a `TaskRegistry`:

```python
from pytask_service.registry import TaskRegistry

registry = TaskRegistry()


def uppercase(text: str) -> str:
    return text.upper()


registry.register("text.uppercase", uppercase)
```

Set `PYTASK_REGISTRY` to that module and attribute, such as
`my_app.tasks:registry`. Only import trusted task modules. Submission validates
the function signature and stores its name and arguments; it does not call the
function.

Each task defaults to three total attempts and a 300-second execution timeout.
Use submission flags to change its policy:

```powershell
.\.venv\Scripts\pytask-service submit math.add --args-file examples/math-add.json --max-attempts 5 --timeout 30 --retry-base 2 --retry-max 60
```

`--max-attempts` includes the first execution. Set it to `1` for a single
attempt. Retry delays use exponential backoff with full jitter. Handlers must
tolerate repeated execution; see the [reliability contract](docs/reliability.md)
for idempotency guidance.

To make a task eligible later, add `--delay` in seconds:

```powershell
.\.venv\Scripts\pytask-service submit math.add --args-file examples/math-add.json --delay 30
```

Alternatively, use `--run-at` with an ISO 8601 timestamp containing a UTC
offset. The two timing options are mutually exclusive. Delayed tasks use the
existing queue and need only a worker; the execution timeout starts when the
worker starts the task process.

## Run a worker

After submitting a task, process one queued task:

```powershell
.\.venv\Scripts\pytask-service worker --once
```

Run a continuous worker in a separate PowerShell window with both environment
variables set:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
$env:PYTASK_REGISTRY = "pytask_service.example_tasks:registry"
.\.venv\Scripts\pytask-service worker
```

Start the same command in another window to run a second worker. Each worker
claims one task at a time. Press Ctrl+C to stop claiming new tasks; the worker
waits for its current task to finish. Use `worker --poll-interval 1` to change
the idle polling interval in seconds. The worker renews its current lease
during graceful shutdown.

Workers use a 30-second lease and renew it every 10 seconds. Override them with
`--lease-seconds` and `--heartbeat-seconds`; the heartbeat interval must be at
most one third of the lease duration. `worker --once` processes at most one
eligible task, so it does not wait for future retries to become due.

The `status` command shows the current state, worker ID, result or error,
attempt count, next eligible time, and lease expiry. Successful results must
be JSON values no larger than 64 KiB. A handler exception or timeout returns
the task to `pending` when attempts remain, or marks it `failed` when its
budget is exhausted. Inspect the execution history with:

```powershell
.\.venv\Scripts\pytask-service attempts "PASTE_TASK_ID_HERE"
```

See [Worker design](docs/worker-design.md) for claim, process, and finalization
details.

## Recurring schedules

Create a named schedule using the example registry:

```powershell
.\.venv\Scripts\pytask-service schedule create minute-add math.add --args-file examples/math-add.json --every 60
```

Run a scheduler in a separate terminal with `PYTASK_DATABASE_URL` set:

```powershell
.\.venv\Scripts\pytask-service scheduler
```

Keep workers running to execute the tasks it enqueues. Schedulers can run
concurrently; row locks and a unique occurrence key prevent duplicate
submissions for the same schedule timestamp. After downtime, a schedule
enqueues its latest due occurrence and skips older missed ones. Its cadence
is preserved, and occurrences may overlap if earlier work is still running.

Use `schedule list`, `schedule show ID`, `schedule history ID`, `schedule pause ID`,
and `schedule resume ID` to manage definitions and inspect their tasks.
`schedule create --paused` creates an inactive definition. All timestamps use
explicit offsets and are normalized to UTC. Intervals are whole seconds;
cron expressions and local calendar scheduling are planned separately.

See the [scheduling commands](docs/scheduling-cli.md) and
[design](docs/scheduling.md). Existing checkouts should follow the
[scheduling upgrade guide](docs/scheduling-upgrade.md) before starting new code.

## HTTP API

The FastAPI service exposes versioned task submission, monitoring, and
schedule management under `/api/v1`. It reuses the same queue and execution
policies as the CLI. Workers and schedulers run as separate processes.

Generate a client key using the [authentication guide](docs/authentication-keys.md).
In a terminal with `PYTASK_DATABASE_URL` and `PYTASK_REGISTRY` set, configure the
digest manifest before starting the API on localhost:

```powershell
$env:PYTASK_API_KEYS_FILE = ".secrets/api-keys.json"
```

```powershell
.\.venv\Scripts\python -m uvicorn pytask_service.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Send the client token in an Authorization bearer header. Submit named tasks
with `POST /api/v1/tasks`, inspect them with `GET /api/v1/tasks/{id}`,
and read execution history at `/api/v1/tasks/{id}/attempts`. Collection reads
support bounded pagination and filters. Schedule endpoints create, inspect,
pause, resume, and list recurring work.

See [PowerShell examples](docs/api-examples.md), the [API contract](docs/api-contract.md),
and [operation notes](docs/api-operations.md). The API requires explicit
[permissions](docs/authentication-permissions.md); health probes remain public.
Use TLS and a trusted ingress before exposing it beyond localhost.

See the [authentication acceptance guide](docs/authentication-verification.md)
for the complete Docker, database, test, and authenticated request sequence.
Interactive documentation is available only in explicit local disabled mode;
required mode can expose protected OpenAPI JSON when configured.

## Monitoring

Read queue pressure, recent attempt outcomes, timing samples, and schedule
backlog with the CLI:

```powershell
.\.venv\Scripts\pytask-service stats
```

Use `--window-seconds 300` for five-minute attempt observations. Queue and
schedule counts always cover retained rows. The API serves the same summary
at `GET /api/v1/monitoring`; it does not start workers or schedulers.

Service events use JSON on stderr and include operational identifiers without
task arguments or results. API responses carry `X-Request-ID` for correlation.
New attempts record queue eligibility; older attempts can have unknown wait
times. Apply the [monitoring upgrade](docs/monitoring-upgrade.md) first.

See the [definitions](docs/monitoring.md), [PowerShell examples](docs/monitoring-examples.md),
[event reference](docs/operational-logs.md), [troubleshooting](docs/monitoring-troubleshooting.md),
and [crash recovery demonstration](docs/monitoring-demo.md).

## Container setup

Run the complete local acceptance sequence with Docker Desktop running:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

It sets up API keys, builds and starts containers, applies migrations, runs
the final checks and full test suite, and verifies authenticated task execution.
See the [runner options](docs/authentication-verification.md#run-everything-with-one-command).

The [deployment guide](docs/deployment.md) builds one application image and
runs the API, workers, and scheduler through the `runtime` Compose profile.
Database migrations stay an explicit one-off operation. With no profile,
the existing database-only Compose workflow remains available.

The runtime checks registry requirements and database revision compatibility
before starting a service. The image uses an unprivileged user; Compose adds
a read-only root filesystem, bounded temporary storage, resource limits,
role-specific probes, and shutdown grace periods.

See the [configuration reference](docs/deployment-configuration.md),
[secret files](docs/deployment-secrets.md), [handler image example](docs/deployment-handlers.md),
and [verification steps](docs/deployment-verification.md). Build and run these
checks manually before pushing a deployment change. This stage adds no new
database revision and does not publish an image. Use `compose.auth.yaml` to
mount the API credential manifest; see [authentication deployment](docs/authentication-deployment.md).

## Benchmarks

Run the full local checks and engine benchmarks with one command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -Benchmarks
```

The suite measures host Python workers against PostgreSQL with noop, sleep
and checksum workloads, repeated worker counts, and a separate crash recovery
check. It uses temporary schemas and writes JSON, CSV and Markdown to a new
directory under `benchmark-results/`. Generated results are ignored by Git.

See the [benchmark guide](docs/benchmarks.md) for scope, options, timing
definitions and interpretation. No performance numbers are published until
measured on a documented environment. This stage adds no database revision.

## Milestones

1. Register and submit named tasks with JSON arguments. **Implemented.**
2. Claim and run tasks across multiple workers. **Implemented.**
3. Add retries, leases, crash recovery, and timeouts. **Implemented.**
4. Add delayed and recurring scheduling. **Implemented.**
5. Expose submission and monitoring through an API. **Implemented.**
6. Add operational summaries and structured events. **Implemented.**
7. Package services and define deployment operations. **Implemented.**
8. Authenticate API clients and enforce operation permissions. **Implemented.**
9. Measure engine throughput, timing and crash recovery. **Implemented.**

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance.
