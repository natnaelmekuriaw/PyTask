# Authenticated HTTP requests

Use a generated client token file with the permissions each request needs.
The [acceptance guide](authentication-verification.md) creates a local demo
key with all supported permissions. Never paste its value into commands.

Load the token into a header in the current PowerShell window:

```powershell
$token = (Get-Content -Raw .secrets/local-token.txt).Trim()
```

```powershell
$headers = @{ Authorization = "Bearer $token" }
```

Submit the existing example task with `tasks:submit`:

```powershell
$task = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/tasks" -Headers $headers -ContentType "application/json" -InFile .\examples\api\task.json
```

Read its status with `tasks:read`:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tasks/$($task.id)" -Headers $headers
```

Read execution history with the same permission:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/tasks/$($task.id)/attempts" -Headers $headers
```

Read aggregate statistics with `monitoring:read`:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/monitoring" -Headers $headers
```

The header applies to schedule requests in the [existing examples](api-examples.md)
too. See the [permission matrix](authentication-permissions.md).

A request without a header should return 401:

```powershell
curl.exe -i "http://127.0.0.1:8000/api/v1/tasks"
```

Only the Authorization header supplies credentials. Cookies, URL parameters,
form fields, and `X-API-Key` are unsupported. Avoid redirects to another host;
review destinations before sending credentials. Clear temporary variables when
finished, and keep terminal transcripts and debugging output private.

