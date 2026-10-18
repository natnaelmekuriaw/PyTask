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
