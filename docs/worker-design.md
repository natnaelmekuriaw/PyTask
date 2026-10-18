# Worker design

Each worker runs one task at a time. Running more worker processes increases
parallelism without sharing Python state between task handlers.

## Claim transaction

The worker selects the oldest pending row using `FOR UPDATE SKIP LOCKED`, marks
it running, records its worker ID and start time, and commits. A competing
worker skips the locked row and can claim another. The transaction ends before
the handler starts, so user code never holds a row lock open.

## Task process

The parent starts a fresh Python process using the `spawn` start method. It
passes the registered task name and JSON arguments; the child imports the
configured registry and calls the handler. Database connections and handler
objects are not sent to the child. The child returns a bounded JSON result or
an error through a pipe. An exit without a message becomes a failed outcome.

## Finalization

The parent updates the task only when its ID, running state, and worker ID still
match the claim. It stores either the result or error and a finish time. The
status command computes duration from the start and finish timestamps.

This stage does not reclaim running tasks after a worker crash. That requires
leases and recovery, which are part of the reliability stage. A task handler
should avoid relying on process-local state and should be safe to run more than
once as recovery is added.
