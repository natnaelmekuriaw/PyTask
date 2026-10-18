# Try the API

Run each command separately from the repository root in PowerShell. First
follow the [upgrade guide](api-upgrade.md), then start the server in one
terminal. Set its database URL and trusted registry:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

```powershell
$env:PYTASK_REGISTRY = "pytask_service.example_tasks:registry"
```

```powershell
.\.venv\Scripts\python -m uvicorn pytask_service.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` to inspect the schema and try requests.
Use another terminal for the examples below:

```powershell
$base = "http://127.0.0.1:8000/api/v1"
```

## Submit and inspect

Submit the complete JSON example and save the returned task:

```powershell
$task = Invoke-RestMethod -Method Post -Uri "$base/tasks" -ContentType "application/json" -InFile examples/api/task.json
```

```powershell
Invoke-RestMethod -Uri "$base/tasks/$($task.id)"
```

The task starts as pending. In a worker terminal, set the same database and
registry variables, then execute an eligible task:

```powershell
.\.venv\Scripts\pytask-service worker --once
```

Use an otherwise empty local queue so another pending task does not get
claimed first. Inspect this task again to see its result, then its attempts:

```powershell
Invoke-RestMethod -Uri "$base/tasks/$($task.id)/attempts"
```

Add `delay_seconds` to a request body for relative scheduling, or `run_at`
with a timestamp such as `2027-01-01T12:00:00+03:00`. Use your intended future
time; past timestamps are immediately eligible. Those timing fields cannot
be combined.

## Browse pages

```powershell
$page = Invoke-RestMethod -Uri "$base/tasks?status=pending&limit=20"
```

```powershell
$page.items
```

When `next_cursor` is non-null, pass it with the same filters:

```powershell
$next = Invoke-RestMethod -Uri "$base/tasks?status=pending&limit=20&cursor=$($page.next_cursor)"
```

The cursor is URL-safe. A null cursor marks the end, so do not run the next
request after reaching it. Attempts instead return `next_after`; send it as
`after` with that task's attempts endpoint.

## Manage a schedule

The example creates a paused definition:

```powershell
$schedule = Invoke-RestMethod -Method Post -Uri "$base/schedules" -ContentType "application/json" -InFile examples/api/schedule.json
```

```powershell
Invoke-RestMethod -Uri "$base/schedules/$($schedule.id)"
```

```powershell
Invoke-RestMethod -Method Post -Uri "$base/schedules/$($schedule.id)/resume"
```

Run a scheduler in a terminal with the database URL set:

```powershell
.\.venv\Scripts\pytask-service scheduler
```

Run workers in other terminals to execute its tasks. Monitor occurrences:

```powershell
Invoke-RestMethod -Uri "$base/schedules/$($schedule.id)/tasks?limit=20"
```

```powershell
Invoke-RestMethod -Method Post -Uri "$base/schedules/$($schedule.id)/pause"
```

Pause leaves previously queued tasks available to workers. Reusing the same
schedule name returns 409; use `GET /schedules` to find an existing definition.
Press Ctrl+C in the server, scheduler, and worker terminals when finished.

See the [API contract](api-contract.md) for limits, error codes, pagination,
and delivery semantics.
