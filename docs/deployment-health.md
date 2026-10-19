# Container health checks

| Service | Probe | What it establishes |
| --- | --- | --- |
| PostgreSQL | `pg_isready` | The server accepts connection attempts |
| API | `probe api` | Loopback HTTP readiness returns 200 and the expected JSON body |
| Worker | `probe database` | Its database credentials, revision, and mapped columns are usable |
| Scheduler | `probe database` | The same database dependency checks without importing handlers |

A worker or scheduler dependency probe does not prove its main loop is making
progress. Use task attempts, schedule occurrences, queue age, and process
events to assess progress. Container process exit is reported separately.

The API probe uses port 8000 inside the container. Publishing a different
host port does not change this endpoint. It ignores ambient HTTP proxies,
refuses redirects, reads at most 1025 bytes, and requires exactly the
`{"status":"ok"}` readiness payload. Its socket timeout defaults to three seconds.

Compose probes run every 30 seconds with three retries and a 15-second startup
period. The Docker timeout bounds the whole probe process: eight seconds for
HTTP and twelve for database checks. Database connection and statement waits
are also bounded by application settings.

Inspect current state:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime ps
```

Run the same API probe manually:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime exec api python -m pytask_service.runtime probe api
```

A health failure marks a running container unhealthy. The configured restart
policy reacts to process failures, not to an unhealthy label alone. See
[Compose service behavior](https://docs.docker.com/reference/compose-file/services/)
and the [troubleshooting guide](deployment-troubleshooting.md).
