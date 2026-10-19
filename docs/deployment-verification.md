# Deployment verification

Run these checks after reviewing the branch. Commands are separate PowerShell
steps. Docker operations, database operations, and the full suite are manual.

For a complete current startup sequence, use the
[authentication acceptance guide](authentication-verification.md). It includes
key generation, the authentication overlay, a 401 check, and task execution.
Stop API, worker, and scheduler processes before running the full test suite.

## Host checks

Refresh the editable installation with the runtime constraints:

```powershell
.\.venv\Scripts\python -m pip install -c constraints/runtime.txt -e ".[dev]"
```

Run the static checks:

```powershell
.\.venv\Scripts\ruff check .
```

```powershell
.\.venv\Scripts\ruff format --check .
```

```powershell
.\.venv\Scripts\mypy
```

Set the test database connection in this terminal. Prefer a disposable test
database; the integration suite requires permission to create schemas.
With the supplied local development database:

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

Ensure PostgreSQL is running and the database is migrated, then run the full
suite with progress, duration reporting, and immediate failure:

```powershell
.\.venv\Scripts\pytest -x -vv --durations=10
```

The [startup guide](deployment.md) contains the explicit PostgreSQL and
migration commands if that database has not been prepared yet. Set
`PYTASK_DATABASE_URL` in this PowerShell window; a Compose `.env` file does
not configure host tests. Missing connection variables skip integration tests.

The deployment integration checks cover unstamped, outdated, matching, and
incomplete schemas. Tests that submit tasks use isolated schemas so normal
deployment workers cannot claim their test tasks.

## Compose and image checks

Follow the [startup sequence](deployment.md): validate Compose, build the
image, start PostgreSQL, run migrations explicitly, then start the runtime
services. Inspect container state and logs.

Read readiness from the host:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health/ready"
```

Load the token from the authentication acceptance setup:

```powershell
$token = (Get-Content -Raw .secrets/local-token.txt).Trim()
```

```powershell
$headers = @{ Authorization = "Bearer $token" }
```

Submit the registered example through the API with `tasks:submit`:

```powershell
$task = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/tasks" -Headers $headers -ContentType "application/json" -InFile .\examples\api\task.json
```

Inspect it with `tasks:read` after the worker has had time to claim it:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/tasks/$($task.id)" -Headers $headers
```

The task should reach succeeded with result 3. Inspect its attempt history
and aggregate monitoring, then confirm the scheduler can dispatch an example
schedule using the existing API examples.

## Shutdown and retention

Stop application services and confirm the worker completes its active default
task within the configured budget. Restart and confirm stored task history
remains. For larger task timeouts, adjust the stop grace period before
checking graceful completion.

CI has a separate image job that validates Compose, builds the image, checks
help under a read-only filesystem, and inspects identity and migration scripts.
It does not replace this running-stack acceptance exercise and does not push
an image to a registry.
