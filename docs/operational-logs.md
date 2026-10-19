# Operational logs

CLI processes and the API lifespan configure JSON events on stderr under the
`pytask_service` logger. CLI stdout retains command results. Human CLI
diagnostics may also appear on stderr. Host application handlers are retained;
the root logger and third-party loggers are not reconfigured.

Set the level before starting a process:

```powershell
$env:PYTASK_LOG_LEVEL = "INFO"
```

Supported levels are DEBUG, INFO, WARNING, ERROR, and CRITICAL. INFO is the
default. WARNING suppresses routine request and execution events without
changing database monitoring. Configuration is per process. Library callers
can call `pytask_service.observability.logging.configure_logging()` explicitly.

Every event contains a UTC timestamp, level, logger, and event name. Optional
identifiers connect related work without including handler payloads.

| Event | Fields and interpretation |
| --- | --- |
| `task.submitted` | Task ID after API or CLI submission commits |
| `task.claimed` | Task, attempt, worker IDs and attempt number after claiming |
| `task.attempt_finished` | Same identifiers, committed task status |
| `task.attempt_timed_out` | Same identifiers; status can be pending for a retry |
| `task.lease_lost` | Warning; this worker cannot publish an outcome |
| `worker.leases_recovered` | Worker ID and number of recovered expired leases |
| `worker.started`, `worker.stopped` | Continuous worker lifecycle |
| `schedule.created`, `schedule.paused`, `schedule.resumed` | Committed schedule controls |
| `schedule.dispatched` | Schedule and task IDs, occurrence timestamp, created flag |
| `scheduler.started`, `scheduler.stopped` | Continuous scheduler lifecycle |
| `http.request` | Request ID, method, route template, status, elapsed seconds, verified credential ID when present |
| `auth.configured` | Mode and configured key count; disabled mode emits a warning |
| `auth.rejected` | Safe reason: missing, invalid, or malformed; no claimed key ID |
| `auth.denied` | Verified credential ID for a denied operation or schema request |
| `api.database_failed`, `api.integrity_failed`, `api.unexpected_failure` | Exception class without exception text |

An attempt event's `status` is the resulting task state. A failed attempt
with retries remaining therefore reports pending. Consult attempt history
for its full persisted outcome.

Every HTTP request gets a fresh `X-Request-ID`. Client-supplied IDs are
replaced. API task and schedule events inherit the same ID. Unmatched paths
are labeled unmatched; matched paths use declared templates rather than task
IDs. Query strings, request bodies, results, SQL parameters, exception messages,
and tracebacks are excluded from service event fields.

Authentication events exclude token values, token digests, manifests, raw
headers, and credential file paths. A credential ID comes from the validated
manifest only after authentication succeeds. Public health requests do not
authenticate supplied headers and therefore have no credential ID. Early
authentication rejection can retain the `unmatched` route label.

This filtering applies to service events. Uvicorn, reverse proxies, and
application task handlers manage their own logs. Review those separately
when handling sensitive payloads.

Logs are best effort: a failed destination does not change a committed
outcome. A process can die after a commit and before writing its event.
Database attempt history remains the source of execution state. Idle polls
and successful lease renewals do not produce routine events.
