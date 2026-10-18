# PyTask

PyTask is a PostgreSQL-backed task execution service for registered Python
functions. It is being built around task claiming, retries, leases, and crash
recovery.

The current branch contains the project foundation: an installable package,
database configuration, migration tooling, and development checks. Task
submission and workers are planned for the next stages.

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
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\pytask-service check-db
```

`check-db` prints `Database connection OK` when it can connect. The credentials
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

The integration test runs when `PYTASK_DATABASE_URL` is set and skips otherwise.

## Planned milestones

1. Register and submit named tasks with JSON arguments.
2. Claim and run tasks across multiple workers.
3. Add retries, leases, crash recovery, and timeouts.
4. Add delayed and recurring scheduling.
5. Expose submission and monitoring through an API and CLI.

PyTask will use at-least-once execution. Task handlers must be safe to run more
than once; a worker may lose its lease after starting a task.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance.
