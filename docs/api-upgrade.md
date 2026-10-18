# Upgrade and verify the API

Run commands separately from the repository root in PowerShell. Stop API
processes, workers, and schedulers before migrating, and wait for active work
to finish. Use your local development database or a disposable test database.

Install the new dependencies in the project environment:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Set the database URL:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

```powershell
.\.venv\Scripts\alembic upgrade head
```

```powershell
.\.venv\Scripts\alembic check
```

Revision `20261018_06` adds indexes for task and schedule collection reads.
It does not change task payloads, execution state, attempts, or recurring
definitions. Index creation uses ordinary PostgreSQL DDL, so keep writers
stopped during this local upgrade. The API does not apply migrations itself.

## Run the final checks

```powershell
.\.venv\Scripts\ruff check .
```

```powershell
.\.venv\Scripts\ruff format --check .
```

```powershell
.\.venv\Scripts\mypy
```

```powershell
.\.venv\Scripts\pytest -q
```

Keep the database URL set. PostgreSQL tests skip without it. The database user
needs permission to create schemas; API tests use the same isolated-schema
fixture as worker tests. Offline HTTP tests use an in-memory client and do
not start Uvicorn or need PostgreSQL.

The suite covers request validation, transport limits, startup and shutdown,
transaction failures, pagination ties, concurrent schedule creation, results
and attempt history, recurring execution, readiness, proxy prefixes, and
migration upgrade/downgrade.

After reviewing the code and passing the checks:

```powershell
git push -u origin feat/task-api
```

Then follow the [HTTP examples](api-examples.md) to start a localhost server
and try submission and monitoring.

## Downgrade

Stop the API and other database users before returning to `20261018_05`.
Downgrade removes the API collection indexes and retains tasks, attempts, and
schedules. Existing scheduling and worker functionality remains available.
The API's collection reads depend on these indexes for their intended access
patterns, so restore the current schema before normal API operation.
