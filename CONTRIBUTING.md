# Contributing to PyTask

Thanks for taking the time to contribute. Start with an issue for substantial
changes so the behavior and scope are clear before implementation.

## Development

Follow the local setup in the [README](README.md). Run linting, formatting,
type checking, and tests before opening a pull request:

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\pytest -q
```

Tests that need PostgreSQL run when `PYTASK_DATABASE_URL` is set. Use the local
Compose database or a disposable test database; integration tests may change
its contents as the project grows. Run `alembic upgrade head` first. Worker
integration tests create and remove their own PostgreSQL schemas; the database
user needs permission to create schemas.

Worker changes should cover both a single worker and competing claims where
concurrency matters. Keep the claim transaction short and run task handlers
outside it. Check child-process behavior on Windows as well as Linux when
changing process execution or shutdown.

For reliability changes, cover lease expiry and stale claim tokens as well as
successful execution. Reusing a worker ID must not let an old attempt renew or
finish a new one. Check retry exhaustion, timeout cleanup, and attempt history
when changing task transitions. Expire stored leases directly in integration
tests instead of waiting for wall-clock expiry; use bounded waits when the
process or heartbeat behavior itself is under test.

See the [worker design](docs/worker-design.md) for transaction boundaries and
the [reliability contract](docs/reliability.md) for delivery semantics. Stop
workers before schema upgrades; the [upgrade guide](docs/reliability-upgrade.md)
includes migration checks and examples.

Scheduling changes should preserve the original interval cadence and the
documented latest-due policy. Cover transaction rollback, competing scheduler
processes, paused schedules, and uniqueness of `(schedule_id, scheduled_for)`.
Retries and lease recovery must retain the original task's occurrence identity.
Use stored due times and the database clock to test boundaries without waiting
for real intervals to pass.

The scheduling suite reuses the worker suite's isolated-schema fixture.
Keep PostgreSQL tests marked `integration` so the Windows unit-test job can
exercise timestamp parsing and process behavior without a database. See the
[scheduling design](docs/scheduling.md) and [upgrade guide](docs/scheduling-upgrade.md)
when changing dispatch or its schema.

API changes should preserve the [HTTP contract](docs/api-contract.md).
Validate request shape before issuing queries, construct write responses
inside their transaction, and commit before returning success. Cover failed
commits, conflicting schedule names, and missing resources when changing
write handlers. Error responses should exclude raw input, SQL, and internal
exception details.

Pagination tests need tied timestamps, filter changes, and newer concurrent
insertions. Keep cursor filters consistent with the database query. Use the
shared PostgreSQL fixture for constraints and concurrency coverage; the
offline HTTP client rejects database access during validation checks.

Use `TestClient` as a context manager so application lifespan setup and cleanup
run. Test dependencies include the supported HTTPX2 backend. Keep database
tests marked `integration` and leave server startup to the developer running
the [API examples](docs/api-examples.md).

Use `feat/short-name` for feature branches and `fix/short-name` for fixes.

Monitoring changes should preserve the [count and timing definitions](docs/monitoring.md).
Read all aggregate sections with one PostgreSQL snapshot, keep reads bounded
and read only, and avoid ORM loads of task payloads. Cover empty databases,
retry eligibility, expired leases, paused schedules, historical nulls, and
window boundaries. Use explicit stored timestamps instead of real delays.

New execution attempts must retain their eligibility at claim time. Do not
infer historical queue wait from task creation timestamps or a later retry.
Keep abandoned attempts out of execution timing.

Emit success events after committing state changes. Cover rollback and
sensitive-field exclusion when changing event paths. Request identifiers must
be isolated across concurrent requests, and route labels must use declared
templates. Do not add raw URLs, SQL, handler payloads, or exception text to
service event fields. Keep CLI stdout parseable.

Deployment changes must preserve explicit migrations, read-only startup
checks, role-specific configuration, and literal process arguments. Keep
credentials out of arguments, settings reprs, build contexts, and diagnostics.
Cover failed preflight and cleanup paths when changing startup behavior.

Use the [deployment acceptance guide](docs/deployment-verification.md) for
image and Compose changes. Health labels must describe the checks actually
performed; dependency readiness is not proof of worker progress. Check the
shutdown budget against the workload's task timeout before changing defaults.
Use runtime constraints for CI and image builds, and review their dependency
updates as a coherent set. Docker commands and image publication are separate
actions; a successful unit suite does not establish a successful image build.

Keep commits focused and describe the change in a short, lower-case subject line.

Authentication changes must preserve required-by-default startup, explicit
local opt-out, immutable manifest snapshots, and safe credential diagnostics.
Use generated temporary keys in tests. Cover wrong secrets, duplicate headers,
scope denial before database access, mounted paths, and failed startup cleanup.
Keep bearer tokens and digests out of event fields and object representations.

Every versioned API operation must declare its permissions and authentication
error responses. Schedule task history requires both schedule and task read
access. Maintain the [permission matrix](docs/authentication-permissions.md)
and [acceptance procedure](docs/authentication-verification.md) with endpoint
changes. Authentication tests under `tests/auth/integration` require PostgreSQL;
the remaining authentication checks run entirely in process.

## Pull requests

Explain the behavior you changed, how you checked it, and any migration or
compatibility concerns. Add tests for behavior that could regress. For schema
changes, include an Alembic migration and check both upgrade and downgrade.
