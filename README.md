# PyTask

PyTask is a PostgreSQL-backed task execution service for registered Python
functions. It is being built around task claiming, retries, leases, and crash
recovery.

The current stage supports registering named functions, submitting tasks with
JSON arguments, and running them in background worker processes. Multiple
workers can safely claim tasks from the same PostgreSQL queue.

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
the idle polling interval in seconds.

The `status` command shows the current state, worker ID, result or error, and
execution duration. Successful results must be JSON values no larger than
64 KiB. A handler exception marks the task as failed.

## Planned milestones

1. Register and submit named tasks with JSON arguments. **Implemented.**
2. Claim and run tasks across multiple workers. **Current stage.**
3. Add retries, leases, crash recovery, and timeouts.
4. Add delayed and recurring scheduling.
5. Expose submission and monitoring through an API.

This stage does not yet recover a task left `running` when its worker crashes.
The reliability stage will add leases, recovery, retries, and an at-least-once
delivery contract. Task handlers should be safe to run more than once.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance.
