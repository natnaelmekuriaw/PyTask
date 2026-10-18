# Deployment design

One application image serves API, worker, scheduler, and one-off commands.
Compose keeps PostgreSQL available independently; the runtime profile enables
the application services. Migrations run only when the operator requests them.

Service startup validates configuration, registry requirements, and the
database migration head before replacing the launcher process. Health probes
are bounded reads. They never claim tasks, dispatch schedules, or migrate.

Containers use an unprivileged account, an immutable application filesystem,
and a writable temporary directory. Database storage remains a named volume.
The published API and database ports bind to localhost.

SIGTERM reaches the application process through Compose's init process.
Shutdown budgets allow default tasks to finish; larger task timeouts require
an explicit grace-period decision. Forced termination retains the existing
lease recovery and at-least-once delivery contract.
