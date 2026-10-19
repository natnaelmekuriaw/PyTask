# Package application handlers

Task registries are trusted Python modules. API and worker containers must
receive the same handler package and configuration. The sample in
`examples/container` adds a named multiplication task to a derived image.

Build the default base image first:

```powershell
docker compose --profile runtime build api
```

The example expects the default base tag `pytask:local`. Its Dockerfile uses
a runtime stage, copies only the handler module, and keeps the inherited
unprivileged user and process entry point.

Build the derived image through the overlay:

```powershell
docker compose -f compose.yaml -f examples/container/compose.handlers.yaml -f compose.auth.yaml --profile runtime build api
```

Start all application roles with the same overlay:

```powershell
docker compose -f compose.yaml -f examples/container/compose.handlers.yaml -f compose.auth.yaml --profile runtime up -d --no-build
```

The overlay sets `handlers:registry` on the API, worker, and operator service.
The scheduler uses the same image but does not import the registry.
Migrations remain on the base image because this example changes no schema.

The derived image exposes `math.multiply`. It does not also register the
base example functions. Submit only names registered by the selected module.

For a real application, package handler dependencies into the derived image
during its build. Keep modules importable in spawned child processes. A
read-only bind mount can help local development, but a release should use one
built artifact for API validation and worker execution.

Mount durable output storage explicitly when handlers need files. Temporary
files are bounded and disposable. Task arguments and results remain subject
to the existing JSON limits and idempotency requirements.
