# Shutdown behavior

The runtime launcher replaces itself with the selected process. Compose
enables an init process so termination signals reach the service and orphaned
children are reaped. No shell process sits between the launcher and Python.

| Service | Default shutdown budget | Behavior |
| --- | --- | --- |
| API | 45 seconds in Compose; 30 in Uvicorn | Finish active HTTP requests within the server budget |
| Worker | 330 seconds | Stop claiming, finish current work, keep renewing its lease |
| Scheduler | 15 seconds | Finish the current bounded dispatch and stop polling |

The worker budget accommodates the default 300-second task timeout plus
process cleanup and finalization. Tasks can request longer execution
timeouts. Set `PYTASK_WORKER_STOP_GRACE` accordingly before relying on graceful
completion of those tasks. Likewise, increase the Compose API budget when
increasing `PYTASK_API_GRACEFUL_SECONDS`.

Stop application processes while retaining PostgreSQL:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime stop api worker scheduler
```

A stop can legitimately wait for a running task. After the grace period,
Docker may force termination. The task can then remain running in storage
until its lease expires and another worker recovers it. An external side
effect may already have happened, so handlers still require idempotency.

Memory or process-limit failures can also interrupt work. Resource limits
bound the container; they do not provide task-level isolation of side effects.

Use the [recovery demonstration](monitoring-demo.md) for a bounded crash test.
Capture logs and task attempt history before deciding whether a slow shutdown
is a live handler, database wait, or cleanup problem.
