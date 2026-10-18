# Upgrade to monitoring

Stop API processes, workers, and schedulers before applying the migration.
Existing editable installations pick up the new source; this stage adds no
dependencies. A fresh checkout still needs the setup in the README.

Run each PowerShell command separately. Start your local database if needed:

```powershell
docker compose up -d postgres
```

Set the connection used by the migration and integration tests:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

Check connectivity:

```powershell
.\.venv\Scripts\pytask-service check-db
```

Apply migration `20261019_07`:

```powershell
.\.venv\Scripts\alembic upgrade head
```

Check model/schema agreement:

```powershell
.\.venv\Scripts\alembic check
```

The migration adds nullable `task_attempts.queued_at` plus indexes on attempt
start and finish timestamps. Historical eligibility is not backfilled.
Creating the indexes uses normal DDL and needs a maintenance window on a
busy database. Keep older upgrade guides for the changes they describe.

Run the project checks:

```powershell
.\.venv\Scripts\ruff check .
```

```powershell
.\.venv\Scripts\ruff format --check .
```

```powershell
.\.venv\Scripts\mypy
```

Run the full suite with progress and duration reporting:

```powershell
.\.venv\Scripts\pytest -vv --durations=10
```

Integration tests use separate PostgreSQL schemas. The database user needs
permission to create them. The migration test checks upgrade, model agreement,
legacy attempt preservation, and downgrade.

For a quicker local pass that excludes database coverage:

```powershell
.\.venv\Scripts\pytest -q -m "not integration"
```

After verification, read `pytask-service stats`, review the
[examples](monitoring-examples.md), and restart processes using the commands
in the README. Workers still need their trusted registry configuration.

## Rollback

With processes stopped, `alembic downgrade 20261018_06` removes the eligibility
column and both indexes. It preserves task and attempt rows, but discards the
new eligibility timestamps. Pair the database rollback with the earlier code
before restarting; the monitoring code expects the new column.
