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
