# FF Core Bridge client

This is the managed client for an entitled FF Intelligence capability. It sends a request and saves what comes back. It contains no private method and no deployment engine.

**Version 0.3** (contract 0.3), vendored unchanged from `funnel-futurist/01-ff-aios` at the revision and SHA-256 in `manifest.json`. It replaces 0.1.5 and still serves every 0.1.5 instance. See "Upgrading from 0.1.5" below.

1. Copy `instance.example.json` to `instance.json` and fill in the organization, the HTTPS endpoint and, for `repository-health`, the default repository that FF supplied. This local file is client-owned and ignored by the Starter.
2. Put the issued capability key in the secret store as `FF_CORE_KEY`. The repository contains only the environment-variable name. A key-shaped value anywhere in `instance.json` is refused.
3. Run the capability FF names:
   - **Contract 0.1:** `python3 .aios/core_bridge/core_call.py repository-health`. It saves the whole response under `reports/`, as 0.1.5 did.
   - **Contract 0.3:** `python3 .aios/core_bridge/core_call.py <domain>.<name>@<major> [--inputs inputs.json]`.
     - It saves the result under `outputs/` and the receipt, with its provenance, under `receipts/`.
     - It keeps nothing unless every hash in the receipt agrees (result, inputs, provenance), and it never overwrites a file.
     - It prints paths and SHA-256s, never the content or the key.

Remote endpoints require HTTPS. Plain HTTP is allowed only for a literal loopback IP. Redirects are refused, so the bearer credential is never forwarded to another URL. Exit codes:
- **2:** a refusal, such as `ORG_MISMATCH` when a key belongs to another organization, or `NOT_ENTITLED`. Nothing is saved.
- **3:** a transport, redirect or response failure, including a hash that disagrees. Nothing is saved.
- **4:** a local configuration or missing-secret failure.

## Upgrading from 0.1.5
Nothing to do for an existing instance:
- **`instance.json`:** your 0.1.5 file keeps working unchanged for `repository-health`, and for 0.3 capabilities. `outputs_dir` and `receipts_dir` are optional and default to `outputs` and `receipts` next to the file.
- **`default_repo`:** now needed only for a 0.1 call made without `--repo`.
- **Saved files:** reports you already saved stay where they are. The new `outputs/` and `receipts/` folders are ignored by git, like `reports/`, and an upgrade never touches them.
- **One stricter rule:** a key-shaped value anywhere in `instance.json` is now refused, with `MISSING_CREDENTIAL` and exit 4, even when `FF_CORE_KEY` is set. Move any such value into the secret store and keep only `key_env` in the file.
- **New for 0.3 calls only:** `--ref` is sent only together with `--repo`. A `repository-health` call still defaults `--ref` to `main`.

The organization check happens on FF's side: the service refuses a key used for another organization (`ORG_MISMATCH`). The 0.3 client does not yet compare the organization named in a receipt with your `instance.json`; that check would be added in the source first.

The current FF Core service is not hosted. Until a production HTTPS endpoint and a per-client GitHub App installation are wired, this package is an installed client candidate, not a live external service.
