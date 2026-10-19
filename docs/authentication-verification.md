# Authentication acceptance checks

## Run everything with one command

Start Docker Desktop with Linux containers, stop any host API, worker, or
scheduler processes, and run this from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The execution policy option applies only to that PowerShell process. The
runner installs dependencies, reuses or creates local keys, builds the image,
starts PostgreSQL, applies migrations, runs all checks and the full suite,
starts application services, and verifies readiness, anonymous rejection,
example execution, and authenticated monitoring. Steps print progress and stop
at the first failure. Services remain available for inspection after a failure
or running after success; database changes are not rolled back by the runner.

Existing `.env` and key files are preserved. If only one key file exists, the
runner stops. Existing keys must match and grant `tasks:read`, `tasks:submit`,
and `monitoring:read`. Keys are never printed. Keep `.secrets/` private.

The runner targets `compose.yaml` plus `compose.auth.yaml`. It reads published
ports and local database credentials from the resolved Compose configuration.
An existing `PYTASK_DATABASE_URL` takes precedence for host checks and tests;
use it only when it refers to the intended test database. Temporary environment
changes are restored on exit.

For repeat runs after dependencies and the image are already current:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -SkipInstall -SkipBuild
```

Optional `-ManifestFile` and `-TokenFile` select existing key files.
`-StartupTimeoutSeconds` defaults to 120; `-TaskTimeoutSeconds` defaults to 60
and can be increased for a busy local queue. The default run always executes
the full test suite. Container health waiting uses
[Compose's wait options](https://docs.docker.com/reference/cli/docker/compose/up/).

## Manual checks

Run each block separately in PowerShell from the repository root. Use Docker
Desktop's Linux containers. Stop existing API, worker, and scheduler processes
before the final tests. A failure stops the sequence.

## Prepare credentials and the image

```powershell
.\.venv\Scripts\python -m pip install -c constraints/runtime.txt -e ".[dev]"
```

Keep an existing environment file:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

```powershell
New-Item -ItemType Directory -Force .secrets | Out-Null
```

For a first local setup, generate a demo key with all supported permissions.
If these files already exist, inspect their grants or use new output paths;
generation never overwrites them. Hosted clients should receive narrower grants.

```powershell
.\.venv\Scripts\python -m pytask_service.auth generate --id local-demo --scope tasks:read --scope tasks:submit --scope schedules:read --scope schedules:write --scope monitoring:read --scope docs:read --token-file .secrets/local-token.txt --manifest .secrets/api-keys.json
```

```powershell
.\.venv\Scripts\python -m pytask_service.auth inspect --manifest .secrets/api-keys.json
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime --profile tools config --quiet
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime build api
```

## Database and final checks

These commands assume the supplied local database credentials and port 15432.
Use your actual URL if those settings differ.

```powershell
docker compose up -d postgres
```

```powershell
$env:PYTASK_DATABASE_URL = "postgresql+psycopg://pytask:pytask@localhost:15432/pytask"
```

```powershell
.\.venv\Scripts\pytask-service check-db
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile tools run --rm migrate
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile tools run --rm ops check
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile tools run --rm --entrypoint python migrate -m alembic -c /app/alembic.ini check
```

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
.\.venv\Scripts\pytest -x -vv --durations=10
```

Keep the database URL set in this window so integration tests run. This phase
adds four authentication acceptance cases backed by isolated PostgreSQL schemas.

## Start services and verify access

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime up -d --no-build
```

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime ps
```

Health remains public:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health/ready"
```

The following request must return 401 with a Bearer challenge:

```powershell
curl.exe -i "http://127.0.0.1:8000/api/v1/tasks"
```

Load the client token without printing it:

```powershell
$token = (Get-Content -Raw .secrets/local-token.txt).Trim()
```

```powershell
$headers = @{ Authorization = "Bearer $token" }
```

```powershell
$task = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/tasks" -Headers $headers -ContentType "application/json" -InFile .\examples\api\task.json
```

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tasks/$($task.id)" -Headers $headers
```

Repeat the last command if work is still pending. Expect `succeeded` and result
`3`. Verify monitoring with the authenticated examples as needed. Do not share
the token or headers when reporting results.

