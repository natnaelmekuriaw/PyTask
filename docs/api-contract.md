# HTTP API contract

The API submits and monitors work through the existing task and scheduling
services. It does not execute handlers, run a scheduler loop, or migrate the
database at startup. Workers and schedulers remain separate processes.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/v1/tasks` | Submit a registered task; return 201 and Location |
| GET | `/api/v1/tasks` | List tasks with filters and pagination |
| GET | `/api/v1/tasks/{id}` | Read current state, result, and last error |
| GET | `/api/v1/tasks/{id}/attempts` | Read execution attempts in number order |
| POST | `/api/v1/schedules` | Create a recurring definition; return 201 and Location |
| GET | `/api/v1/schedules` | List recurring definitions |
| GET | `/api/v1/schedules/{id}` | Inspect a definition |
| POST | `/api/v1/schedules/{id}/pause` | Prevent subsequent dispatches |
| POST | `/api/v1/schedules/{id}/resume` | Resume on the original cadence |
| GET | `/api/v1/schedules/{id}/tasks` | List that schedule's occurrence tasks |
| GET | `/health/live` | Check process liveness without a database query |
| GET | `/health/ready` | Check database access and execution table columns |

`/docs` provides interactive OpenAPI documentation. `/openapi.json` exposes
the machine-readable schema. IDs are UUIDs. Missing tasks or schedules return
404; existing resources with no history return an empty page.

## Input validation

Write bodies use `application/json` or an `application/*+json` media type.
Pause and resume accept empty bodies without a Content-Type header. Total
request bodies are limited to 128 KiB, including streamed bodies without a
Content-Length. Task arguments retain the engine's 64 KiB normalized JSON
limit and nesting limit. Unknown fields are rejected.

Policy fields are `max_attempts`, `timeout_seconds`, `retry_base_seconds`, and
`retry_max_seconds`. Numeric strings and booleans are not accepted as numbers.
Attempts range from 1 to 1000; API duration fields are finite, positive, and
capped at 31536000 seconds (365 days). Retry base cannot exceed its cap.

Task requests use `name` and `arguments`, plus an optional `run_at` or
`delay_seconds`. Zero delay is allowed. Timestamps must include an offset and
are normalized to UTC. Relative delays use PostgreSQL's clock. Schedule
requests use `name`, `task_name`, `arguments`, `interval_seconds`, optional
`start_at`, and `paused`. Intervals are whole seconds from 1 to 31536000.

Registered handler names and keyword signatures are validated on submission.
This does not call the handler or infer business validation from annotations.
Only trusted, deployed registry modules are imported. Uploaded Python code
is not accepted.

## Collections

Task and schedule pages contain `items` and `next_cursor`. The default limit
is 50, with a maximum of 100. A null cursor marks the end. Send the returned
cursor with the same filters to continue; page size may change. Cursors are
opaque client values, not authorization tokens.

Tasks support `status`, `schedule_id`, and exact `name` filters. Schedules
support `paused` and exact `task_name` filters. Occurrence lists support
`status`. Pages use creation time descending and UUID descending to resolve
ties. Occurrence lists use task creation order, which can differ from their
logical `scheduled_for` order after downtime.

Pagination is a live view, not a database snapshot. Concurrent status changes
can change membership, and newly committed rows can become visible between
requests. Keyset positions avoid the offset shifts caused by newer rows.
Changing filters invalidates a cursor.

Attempt pages contain `items` and `next_after`. Pass that number as `after`
to continue. Attempts are ordered ascending by number, with the same 50/100
default/maximum limits. Attempt outcomes include failed, timed_out, and
abandoned even while the task itself is pending for a retry.

## Transactions and delivery

Each request has its own SQLAlchemy session. Synchronous handlers run database
work outside the ASGI event loop. Write responses are constructed and their
transactions committed before a success response is returned. A schedule
name conflict returns 409 and leaves the existing definition intact.

A lost connection around commit or a lost HTTP response can leave the client
uncertain whether submission succeeded. Repeating POST can create another
task. Use stable business identifiers and idempotent handlers; this stage
does not implement HTTP idempotency keys. See [reliability](reliability.md).

## Errors

Errors contain an `error` object with `code`, `message`, and `details`.
Validation details give locations, messages, and types without echoing input
values. Malformed JSON returns 400, invalid fields return 422, oversized bodies
return 413, and unsupported body media types return 415. Database failures
return 503; unexpected internal failures return 500. SQL and exception details
are logged on the server and are not included in those responses.

## Access scope

This stage serves trusted operators and has no authentication or tenant
isolation. Keep the server bound to localhost. Authentication and authorization
are required before exposing it to untrusted clients: monitoring includes
stored arguments, results, and execution errors.

See [API examples](api-examples.md), [upgrade steps](api-upgrade.md), and
[operation notes](api-operations.md).
