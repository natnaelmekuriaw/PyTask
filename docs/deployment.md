# Deployment setup

This setup runs Linux containers using Docker Compose. Docker Desktop on
Windows needs its Linux container backend. The API and PostgreSQL host ports
bind to localhost. Application services use the `runtime` profile; one-off
commands use `tools`. With no profile, Compose manages PostgreSQL only.

Run each PowerShell command separately from the repository root. Stop any
host API occupying port 8000 and choose which workers will consume this
database before switching to the container setup.

## Configure and build

For a new local environment, copy the template once. Keep an existing
`.env` file and review the new settings instead of overwriting it.

```powershell
Copy-Item .env.example .env
```

Validate the resolved service definition without printing credentials:

```powershell
docker compose --profile runtime --profile tools config --quiet
```

Build the shared image through the API service:

```powershell
docker compose --profile runtime build api
```

## Prepare the database

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Apply the image's migrations explicitly:

```powershell
docker compose --profile tools run --rm migrate
```

A migration failure must be resolved before starting the application. The
launcher checks revision compatibility; it never applies revisions itself.
There is no new database revision in the deployment setup stage.

## Start and inspect

Start the application services using the built image:

```powershell
docker compose --profile runtime up -d --no-build
```

Inspect service state:

```powershell
docker compose --profile runtime ps
```

Read aggregate statistics:

```powershell
docker compose --profile tools run --rm ops cli stats
```

Open `http://127.0.0.1:8000/docs` for the API. Use the
[acceptance checks](deployment-verification.md) to submit and execute a task.

## Operating guides

- [Configuration](deployment-configuration.md)
- [Image packaging](deployment-image.md)
- [Migration procedure](deployment-migrations.md)
- [Health checks](deployment-health.md)
- [Shutdown](deployment-shutdown.md)
- [Scaling and capacity](deployment-scaling.md)
- [Credentials](deployment-secrets.md)
- [Application handlers](deployment-handlers.md)
- [Troubleshooting](deployment-troubleshooting.md)
- [Backup and restore](deployment-backups.md)
- [Upgrades and rollback](deployment-upgrades.md)

The API has no authentication or tenant isolation. Keep the supplied localhost
publication until an access-control and TLS boundary is designed for hosting.
The image and Compose setup do not provide those application controls.
