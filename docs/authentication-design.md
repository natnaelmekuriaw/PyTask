# API authentication design

The HTTP API accepts operator-issued bearer keys. Each key has a public ID,
a SHA-256 digest of its complete token, and explicit permissions. Tokens carry
32 random bytes; password-derived or user-chosen secrets are unsupported.
Configuration never stores the usable token.

Authentication is required by default. An explicit `disabled` mode supports
local development. CLI commands, workers, schedulers, migrations, and database
probes keep their existing database permissions and do not load HTTP keys.

Authentication runs before request-body buffering. Route dependencies enforce
permissions before opening a database session. Unknown routes and unsupported
methods still require authentication. Only exact health paths are public;
documentation can be disabled independently.

Permissions apply to the whole queue. This is a single-tenant service with no
per-task ownership, browser sessions, login endpoint, or token issuer server.
Keys are immutable for a process lifetime. Rotation and revocation require
recreating every API process with the updated manifest.

Bearer challenges follow [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750).
Transport and deployment guidance follows the
[OWASP REST security guidance](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).
Use TLS at the trusted ingress before exposing the API beyond localhost.
