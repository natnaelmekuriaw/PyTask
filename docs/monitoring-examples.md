# Read monitoring data

Apply the [monitoring upgrade](monitoring-upgrade.md) first. Each command below
is a separate PowerShell command.

Set the database connection in this terminal:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

Read the default one-hour observation window:

```powershell
.\.venv\Scripts\pytask-service stats
```

Read attempt activity from the last five minutes:

```powershell
.\.venv\Scripts\pytask-service stats --window-seconds 300
```

The command prints one JSON object to stdout and returns zero on success.
It needs database access, but no registry, API process, worker, or scheduler.
The window changes attempt observations; it does not limit queue counts to
recently created tasks.

If the API is already running, use a key with `monitoring:read`. Load the token
from the [authentication acceptance setup](authentication-verification.md):

```powershell
$token = (Get-Content -Raw .secrets/local-token.txt).Trim()
```

```powershell
$headers = @{ Authorization = "Bearer $token" }
```

Read the same summary through HTTP:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/monitoring?window_seconds=300" -Headers $headers
```

To retain the response headers, including its request ID:

```powershell
Invoke-WebRequest "http://127.0.0.1:8000/api/v1/monitoring?window_seconds=300" -Headers $headers
```

Inspect an individual task's attempt history using its actual ID:

```powershell
.\.venv\Scripts\pytask-service attempts "PASTE_TASK_ID_HERE"
```

Each attempt reports its eligibility timestamp and queue wait when known.
See [monitoring definitions](monitoring.md) before comparing queue and attempt
counts, and [operational logs](operational-logs.md) for event fields.
