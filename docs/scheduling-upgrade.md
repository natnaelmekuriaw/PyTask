# Upgrade to scheduling

Run commands separately from the repository root in PowerShell. Stop workers
and schedulers before upgrading, and wait for active work to finish. Use your
local development PostgreSQL instance or a disposable test database.

Set the database URL:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

Apply the migration:

```powershell
.\.venv\Scripts\alembic upgrade head
```

Check the resulting schema:

```powershell
.\.venv\Scripts\alembic check
```

Revision `20261018_05` adds `schedules`, its due-time index, and two nullable
task fields: `schedule_id` and `scheduled_for`. Existing standalone tasks keep
both fields null. Execution history, results, retry policy, and leases remain
in place. The new uniqueness and foreign-key constraints protect recurring
occurrence identity and its source definition.

## Verify before pushing

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

Keep the database URL set for the full suite. PostgreSQL tests skip without
it. The database user needs permission to create schemas; scheduling tests
reuse the worker suite's isolated-schema fixture and remove their schemas
afterward.

The suite covers timing boundaries, missed occurrences, competing schedulers,
transaction rollback, stale schedule state, CLI commands, retries and lease
recovery, database constraints, and migration upgrade/downgrade. The real
process execution tests also exercise Windows-compatible spawning.

After review and successful checks, push the branch:

```powershell
git push -u origin feat/task-scheduling
```

## Try it locally

Follow the [CLI examples](scheduling-cli.md). A delayed submission needs only
a worker. A recurring schedule needs a scheduler to enqueue occurrences and a
worker to execute them. `scheduler --once` does one bounded dispatch batch;
`worker --once` executes at most one eligible task.

## Downgrade

Stop schedulers and workers before returning to `20261018_04`. Downgrading
drops recurring definitions and removes scheduling provenance from tasks.
The queued tasks themselves and their execution attempts remain. Export
schedule definitions and occurrence history first if you need to preserve
that information. A schema downgrade does not reverse handler side effects.
