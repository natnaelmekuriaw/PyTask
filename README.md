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
.\.venv\Scripts\python -m pip install -e ".[dev]"
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

If upgrading an existing worker-engine checkout, stop all workers before
running the migration. Follow the [reliability upgrade guide](docs/reliability-upgrade.md)
for the migration checks and retry/timeout examples.

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

## Planned milestones

1. Register and submit named tasks with JSON arguments. **Implemented.**
2. Claim and run tasks across multiple workers. **Implemented.**
3. Add retries, leases, crash recovery, and timeouts. **Implemented.**
4. Add delayed and recurring scheduling. **Current stage.**
5. Expose submission and monitoring through an API.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance.
