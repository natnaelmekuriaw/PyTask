# Monitoring

Monitoring combines a database snapshot with structured operational events.
The CLI and HTTP API share the same query and definitions. Reading a summary
does not claim tasks, recover leases, or dispatch schedules.

Queue and schedule counts describe all retained rows. Attempt statistics use
a bounded observation window. Counts are database observations, not durable
process counters or a promise that a worker is alive.

The implementation records queue eligibility on new attempts. Historical
attempts without that timestamp remain valid and have no queue wait sample.
Arguments, results, exception messages, and database credentials are excluded
from operational events and aggregate responses.

## Queue and schedule counts

| Field | Meaning |
| --- | --- |
| `queue.total` | All retained tasks, including completed work |
| `pending` | Tasks currently waiting for an attempt |
| `ready` | Pending, eligible now, with attempts remaining |
| `delayed` | First attempts whose eligibility is in the future |
| `retry_wait` | Retries whose backoff has not elapsed |
| `retry_ready` | The subset of ready work that has already been attempted |
| `exhausted_pending` | Pending rows with no attempt budget left |
| `running` | Claimed tasks, including expired or incomplete leases |
| `expired_running` | Running tasks whose lease has expired |
| `unleased_running` | Running rows without a lease timestamp |
| `succeeded`, `failed` | Current terminal task states |
| `oldest_ready_age_seconds` | Time since the oldest ready task became eligible |
| `schedules.active`, `paused` | Schedule definitions by pause state |
| `schedules.due` | Active definitions eligible for dispatch now |
| `schedules.oldest_due_age_seconds` | Age of the oldest active due timestamp |

`retry_ready` is already included in `ready`. Expired and unleased rows are
already included in `running`. A due schedule counts once regardless of how
many intervals were missed. An empty backlog has a null age.

For supported task states, pending work partitions into `ready + delayed +
retry_wait + exhausted_pending`. A snapshot does not repair anomalous rows.
It does not count live worker processes or scheduler instances.

## Observation windows and timings

The default window is 3,600 seconds. Supported windows range from 60 seconds
through 604,800 seconds (seven days). `observed_at` comes from PostgreSQL's
statement clock; `window_start` is exactly one window earlier. Both ends of
the window are inclusive. Future observations are excluded.

Attempt outcome counts use `finished_at`. A failed attempt counts even if its
task later succeeds. `retries_started` counts attempts numbered above one
whose `started_at` falls in the window, including attempts still running.
An abandoned attempt is observed when recovery records its finish, which can
be later than the worker's actual death.

Execution timings use `finished_at - started_at` for succeeded, failed, and
timed-out attempts completed in the window. This measures the attempt
lifecycle, including process startup and cleanup. It is not a profiler of
the Python handler. Abandoned attempts and reversed intervals are excluded.

Queue wait uses `started_at - queued_at` for attempts started in the window.
`queued_at` captures that attempt's eligibility at claim time. Intentional
delay and retry backoff before eligibility are excluded. Schedule dispatch
lag after an occurrence becomes eligible is included. Retries get their own
sample. Unknown historical timestamps and reversed intervals are excluded.

Both summaries report `samples`, `min_seconds`, `mean_seconds`, and
`max_seconds`. With no valid samples, all three measurements are null.
The per-attempt API and CLI expose `queued_at` and `queue_wait_seconds` too.

These counts describe retained database history. They can decrease after
retention or as a window advances; they are not monotonic metrics counters.
No throughput or percentile claims are inferred from them.
