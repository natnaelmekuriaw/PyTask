# Authentication troubleshooting

| Symptom | Check |
| --- | --- |
| API exits before database checks | Supply a valid manifest, or explicitly select local disabled mode |
| Both key sources rejected | Set one of `PYTASK_API_KEYS` and `PYTASK_API_KEYS_FILE` |
| Mounted file cannot be read | Check host path, UTF-8 encoding, file size, and API user access |
| 401 without a challenge error | Send an Authorization header containing the client token |
| 401 with `invalid_token` | Check the complete token, key ID, configured digest, and loaded manifest |
| 400 with `invalid_request` | Send exactly one Authorization header |
| 403 with `insufficient_scope` | Review the credential's permissions and the challenge's scope list |
| 404 for interactive documentation | Swagger and ReDoc are hidden in required mode |
| 404 for authenticated OpenAPI JSON | Enable the docs flag before API startup |
| 503 `authentication_unavailable` | Check application lifespan setup; recreate the API after reviewing startup logs |
| Revoked key still works | Recreate every API instance and verify which upstream answered |
| Key generation refuses an output | Select new output paths; existing key files are intentionally preserved |

The API expects a digest manifest, not the usable token file. Key inspection
validates structure and lists IDs and permissions without printing digests:

```powershell
.\.venv\Scripts\python -m pytask_service.auth inspect --manifest .secrets/api-keys.json
```

For an authenticated API failure, use the response's `X-Request-ID` to correlate
application events. Rejected requests do not log the supplied token, its claimed
ID, or raw headers. Successful requests log the configured public key ID.
Documentation served before route matching may use the `unmatched` route label.

Do not share token files, Authorization headers, full environment dumps, or
resolved Compose output. Share the status code, safe error envelope, request ID,
and relevant key IDs and scope names instead.

