# FF Core Bridge client

This is the managed client boundary for an entitled FF Intelligence capability. It sends a request and saves the returned report. It does not contain the private method or deployment engine.

1. Copy `instance.example.json` to `instance.json` and fill in the organization, HTTPS endpoint and default repository supplied by FF. This local configuration is client-owned and ignored by the Starter.
2. Put the issued capability key in the secret store as `FF_CORE_KEY`. The repository contains only the environment-variable name.
3. Run `python3 .aios/core_bridge/core_call.py repository-health`.

Successful reports are written atomically under `.aios/core_bridge/reports/` with a SHA-256 in the command output. Remote endpoints require HTTPS; plain HTTP is allowed only for a literal loopback IP. Redirects are refused so the bearer credential is never forwarded to another URL. A refusal exits 2. Transport, redirect or response failures exit 3. Local configuration or missing-secret failures exit 4.

The current FF Core service is not hosted. Until a production HTTPS endpoint and per-client GitHub App installation are wired, this package is an installed client candidate, not a live external service.
