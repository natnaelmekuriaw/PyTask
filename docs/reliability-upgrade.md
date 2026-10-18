# Upgrade and check task reliability

Run these commands from the repository root in PowerShell, one at a time.
Use your local development database or a disposable test database.

## Upgrade from the worker engine

Stop every worker before migrating. Ctrl+C lets an active attempt finish;
wait for the worker to exit. Old worker processes must not run against the
new schema because they do not enforce claim tokens or lease expiry.

Set the connection URL in the terminal where you will run the checks:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

Apply the migration:

```powershell
.\.venv\Scripts\alembic upgrade head
```

Check that the schema matches the models:

```powershell
.\.venv\Scripts\alembic check
```

The new revision is `20261018_04`. It adds retry policy, lease fields, queue
indexes, and the `task_attempts` table. Existing pending tasks keep their
creation order and receive the default policy. Existing running, succeeded,
and failed tasks receive one attempt record from their stored state. This
cannot reconstruct execution history that was never recorded.

Existing running tasks receive an already expired lease. Once a new worker
starts, it can mark that attempt abandoned and retry it. Existing terminal
tasks stay terminal. Review handlers for idempotency before restarting
workers; see the [reliability contract](reliability.md).

## Run the checks

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

Keep `PYTASK_DATABASE_URL` set for the full suite. Without it, PostgreSQL tests
skip. Worker tests create and remove isolated schemas, so the database user
needs permission to create schemas.

The integration suite covers competing claims, renewal and expiry, stale
tokens, retries, attempt history, migration upgrade/downgrade, and recovery
after a process exits immediately after committing its claim. That crash test
sets the saved lease into the past rather than waiting for a real expiry.

## Try retries

Use an otherwise empty development queue so other pending tasks do not get
claimed before the examples. Set the example registry:

```powershell
$env:PYTASK_REGISTRY = "pytask_service.example_tasks:registry"
```

Submit a handler that raises an exception:

```powershell
.\.venv\Scripts\pytask-service submit demo.fail --args-file examples/failure.json --max-attempts 3 --retry-base 1 --retry-max 2
```

Copy its task ID, then run a continuous worker:

```powershell
.\.venv\Scripts\pytask-service worker
```

Expect two reports with `pending` status followed by one with `failed` status,
with attempt numbers 1, 2, and 3. The delays vary because retries use jitter.
Press Ctrl+C after the third report, then inspect the task:

```powershell
.\.venv\Scripts\pytask-service status "PASTE_TASK_ID_HERE"
```

```powershell
.\.venv\Scripts\pytask-service attempts "PASTE_TASK_ID_HERE"
```

The history should contain three failed attempts with separate timestamps
and errors. `worker --once` processes at most one eligible task and does not
wait for a future retry.

## Try a timeout

Submit the example that sleeps for 30 seconds, with a two-second deadline and
one total attempt:

```powershell
.\.venv\Scripts\pytask-service submit demo.pause --args-file examples/pause.json --max-attempts 1 --timeout 2
```

```powershell
.\.venv\Scripts\pytask-service worker --once
```

Inspect the new task's history using its ID:

```powershell
.\.venv\Scripts\pytask-service attempts "PASTE_TASK_ID_HERE"
```

The task should be `failed` and its attempt should be `timed_out`. The deadline
includes process startup; termination and reaping can add cleanup time before
the worker reports the result.

## Downgrade considerations

Stop workers before downgrading too. Revision `20261018_03` removes the lease
and retry fields and drops all attempt history. Export history first if it
must be retained. A downgrade does not undo handler side effects or recover
work that was interrupted; inspect running tasks before returning to older
worker code.
