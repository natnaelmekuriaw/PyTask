# Scaling and capacity

Run more workers with the same immutable image and task registry:

```powershell
docker compose --profile runtime up -d --no-build --scale worker=3
```

There is no fixed worker container name or published worker port. Each process
gets its own worker identity and claims one task at a time. Multiple schedulers
are supported by the queue's row locking and occurrence uniqueness, but one
scheduler is the normal starting point.

The API publishes a fixed localhost port. Scaling it with the same port
mapping needs a separate routing design; the base setup runs one API process.

## Connection budgets

Compose configures API pools for five persistent connections plus five overflow,
worker pools for two with no overflow, and scheduler pools for one. A separate
database probe can temporarily use another connection per worker or scheduler.
Include migrations, operator sessions, handler-owned pools, and other clients
when comparing the total with PostgreSQL's connection limit.

API concurrency is not a connection count. Requests wait for a bounded pool
checkout and fail if it cannot provide a connection in time. Raising request
concurrency without database capacity can increase waiting and errors.

Default memory limits are 512 MiB per API/worker container and 256 MiB for the
scheduler. Workers include their child task process within that budget.
The temporary filesystem is capped at 64 MiB. Adjust these limits for the
handler workload; the defaults are starting budgets, not measured capacity.

Use monitoring to compare ready queue age, retries, timeouts, and execution
samples as workers increase. Benchmark results and throughput claims require
a separate measured workload; deployment setup does not include such claims.
