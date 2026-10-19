# Authentication configuration

Only the API and its service preflight read these settings. Workers, schedulers,
CLI database operations, migrations, and health probe clients do not need keys.

| Setting | Default | Purpose |
| --- | --- | --- |
| `PYTASK_API_AUTH_MODE` | `required` | `required` or explicit local `disabled` mode |
| `PYTASK_API_KEYS` | unset | Version 1 JSON credential manifest |
| `PYTASK_API_KEYS_FILE` | unset | UTF-8 file containing that manifest |
| `PYTASK_API_DOCS_ENABLED` | `false` when required | Enable protected OpenAPI JSON |
| `PYTASK_API_KEYS_SECRET_FILE` | `./.secrets/api-keys.json` | Host file used by the Compose authentication overlay |

Set exactly one manifest source. File sources accept a UTF-8 BOM and surrounding
whitespace. Missing, empty, unreadable, oversized, or invalid files prevent API
startup. Direct manifests have the same 8192-byte limit.

A manifest contains exactly `version` and `keys`. Version must be integer
`1`. Each record contains exactly `id`, `sha256`, and `scopes`. Use the
[key tool](authentication-keys.md) to produce these fields.

Configure 1 to 32 credentials within the byte limit. IDs and digests must be
unique. IDs begin with a lowercase letter or digit and contain at most 48
lowercase letters, digits, underscores, or hyphens. Digests are lowercase
SHA-256 hex strings. Permissions must be supported, nonempty, and unique.
Duplicate JSON fields and unknown fields are rejected.

## Local development

Set `PYTASK_API_AUTH_MODE=disabled` explicitly and remove both manifest sources.
Documentation defaults to enabled in that mode; an explicit docs flag wins.
Compose sets its own docs flag to false unless overridden.

In required mode, interactive Swagger and ReDoc pages are hidden. If the docs
flag is true, `/openapi.json` requires `docs:read` and a bearer header.
Download it using a header-capable client. Browser navigation alone cannot
supply that header. No credentials are stored in browser storage.

