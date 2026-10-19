# Deploy with API authentication

Generate a key manifest using the [key tool](authentication-keys.md).
By default, `compose.auth.yaml` mounts `.secrets/api-keys.json` into only
the API container. It never mounts the usable client token.

Validate the service definitions after creating that manifest:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime --profile tools config --quiet
```

Build the shared image:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime build api
```

Use the [deployment database procedure](deployment.md#prepare-the-database)
before starting services. Authentication introduces no database revision.

Start the API, worker, and scheduler:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime up -d --no-build
```

After changing key records, recreate the API:

```powershell
docker compose -f compose.yaml -f compose.auth.yaml --profile runtime up -d --no-build --force-recreate api
```

Use the same file options when inspecting status or logs. Scaled API instances
must all receive and reload the same reviewed manifest. Compose interpolation
variable `PYTASK_API_KEYS_SECRET_FILE` can select another host manifest path.

## Database secret files

The overlays compose together:

```powershell
docker compose -f compose.yaml -f compose.secrets.yaml -f compose.auth.yaml --profile runtime --profile tools config --quiet
```

Use that complete file list for migrations, startup, status, and recreation
when using database secret files. The API then mounts both its database URL
and its key manifest. Other roles receive only the database secrets they need.

The supplied ports remain bound to localhost. TLS termination, trusted ingress,
request throttling, and network policy are deployment responsibilities.

