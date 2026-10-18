# Scheduling commands

Run commands separately from the repository root in PowerShell. Migrate first
using the [upgrade guide](scheduling-upgrade.md). Use an otherwise empty local
queue when trying the examples so unrelated tasks do not get claimed first.

Set these variables in each terminal that submits or executes example tasks:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

```powershell
$env:PYTASK_REGISTRY = "pytask_service.example_tasks:registry"
```

## Delay one task

```powershell
.\.venv\Scripts\pytask-service submit math.add --args-file examples/math-add.json --delay 30
```

The task is pending for at least 30 seconds before it can be claimed. A worker
may begin later because of polling or other queued work. Run a continuous
worker to pick it up when it becomes eligible:

```powershell
.\.venv\Scripts\pytask-service worker
```

Press Ctrl+C after it finishes. You can also use `--run-at` instead of
`--delay`. Replace this example timestamp with your intended time:

```powershell
.\.venv\Scripts\pytask-service submit math.add --args-file examples/math-add.json --run-at "2027-01-01T12:00:00+03:00"
```

That timestamp represents 09:00 UTC. Past timestamps are immediately eligible.

## Create a recurring schedule

Create a paused definition that will run every 60 seconds:

```powershell
.\.venv\Scripts\pytask-service schedule create minute-add math.add --args-file examples/math-add.json --every 60 --paused
```

Copy its schedule ID. Inspect and resume it:

```powershell
.\.venv\Scripts\pytask-service schedule show "PASTE_SCHEDULE_ID_HERE"
```

```powershell
.\.venv\Scripts\pytask-service schedule resume "PASTE_SCHEDULE_ID_HERE"
```

Without `--paused`, a new schedule is active immediately. Use `--start-at`
with an offset-aware timestamp to choose its first due time. Task policy
flags also work here: `--max-attempts`, `--timeout`, `--retry-base`, and
`--retry-max`. The name must be unique. Names start with a lowercase letter
and may contain lowercase letters, digits, dots, underscores, and hyphens.

## Dispatch and execute

Dispatch one batch of due schedules:

```powershell
.\.venv\Scripts\pytask-service scheduler --once
```

Each JSON report includes the task ID, schedule ID, logical occurrence time,
and whether a task was newly created. Run a worker to execute the queued task:

```powershell
.\.venv\Scripts\pytask-service worker --once
```

For continuous operation, run the scheduler in one terminal and workers in
other terminals. Every terminal needs the database URL; worker terminals also
need the registry. A scheduler terminal does not need to import handlers.

```powershell
.\.venv\Scripts\pytask-service scheduler --batch-size 100 --poll-interval 1
```

```powershell
.\.venv\Scripts\pytask-service worker
```

You may run several scheduler processes. Each uses row locks and the same
occurrence uniqueness constraint. Press Ctrl+C in each terminal to stop it.

## Inspect and pause

```powershell
.\.venv\Scripts\pytask-service schedule list --limit 100
```

```powershell
.\.venv\Scripts\pytask-service schedule history "PASTE_SCHEDULE_ID_HERE" --limit 20
```

Listing is ordered by name; history shows the newest occurrences first.
Both commands accept limits from 1 to 1000. Use a task ID from history with
`status TASK_ID` or `attempts TASK_ID` to inspect execution details.

```powershell
.\.venv\Scripts\pytask-service schedule pause "PASTE_SCHEDULE_ID_HERE"
```

Pausing prevents future dispatches. It leaves already queued tasks available
to workers. Resuming keeps the cadence and enqueues only the latest due
occurrence if several were missed. See [scheduling design](scheduling.md) for
the delivery and overlap rules.
