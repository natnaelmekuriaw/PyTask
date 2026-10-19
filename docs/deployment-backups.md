# Backup and restore

Queue tasks, attempts, schedules, and migration state live in PostgreSQL.
The named `postgres_data` volume persists when containers are replaced.
Changing Compose project names can select a different volume; confirm the
project and volume before assuming an empty queue means lost data.

Use your normal database backup policy for hosted deployments. The following
local example uses the default database user and name. Substitute your
configured values where needed.

## Create a backup

Create a local output directory:

```powershell
New-Item -ItemType Directory -Force backups
```

Write a custom-format dump inside the database container:

```powershell
docker compose exec -T postgres pg_dump -U pytask -d pytask --format=custom --file=/tmp/pytask.dump
```

Copy it as a file:

```powershell
docker compose cp postgres:/tmp/pytask.dump ./backups/pytask.dump
```

This avoids binary output redirection through older PowerShell versions.
Backups contain handler payloads, results, and execution errors. The local
`backups/` directory is ignored by Git and excluded from the image context.

## Verify an isolated restore

Create a separate database instead of overwriting the active queue:

```powershell
docker compose exec -T postgres createdb -U pytask pytask_restore
```

Copy the archive back into the container:

```powershell
docker compose cp ./backups/pytask.dump postgres:/tmp/pytask-restore.dump
```

Restore into that separate database:

```powershell
docker compose exec -T postgres pg_restore -U pytask -d pytask_restore --no-owner --no-privileges /tmp/pytask-restore.dump
```

Inspect its revision:

```powershell
docker compose exec -T postgres psql -U pytask -d pytask_restore -c "SELECT version_num FROM alembic_version;"
```

Keep the restored queue isolated from workers until a deliberate cutover.
Its pending tasks can represent side effects already performed elsewhere.
Stop consumers before switching their connection URL and verify image/schema
compatibility before starting them. A backup strategy is complete only after
a restore has been checked.
