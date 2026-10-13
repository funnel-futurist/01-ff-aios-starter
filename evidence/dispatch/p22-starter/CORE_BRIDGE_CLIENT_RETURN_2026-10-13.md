# Core Bridge client return — 2026-10-13

Existing scope: PR70 Codex AIOS critical path, FF-as-client installation boundary.

Status: implementation candidate complete; not a hosted service and not an approved Starter release.

## Pins and ownership

- Repository: `funnel-futurist/ff-aios-starter`
- Base: `41edbad0961dec4e8afc489eef45750a388349da`
- Implementation commit: `d812f103ef57ba7600c1fe56458331748f33d356`
- Branch: `codex/core-bridge-client-20261013`
- Source contract: `funnel-futurist/ai-os` commit `ab6011e65849430820368042b935a1df3498eb63`, path `11_Operations/core_bridge/thin_caller/core_call.py`
- Writer: Codex AIOS lane; no other Starter writer was active in the inspected open-PR list.

## Implemented

- The Starter now ships the method-free client as a managed file under `.aios/core_bridge/`.
- Per-instance configuration and reports remain client-owned and outside release replacement.
- `FF_CORE_KEY` is an optional secret reference. Its value is never committed.
- Remote endpoints require HTTPS; loopback HTTP remains available for local acceptance.
- Responses are capped at 5 MiB, report paths cannot escape the instance, request IDs cannot control paths, and reports are written atomically with a SHA-256 readback.
- Founder-lane and CODEOWNERS rules cover the local instance configuration.
- The private method, entitlement store and deployment engine are not present in the client package.

## Evidence

- Focused boundary and policy tests: 45 passed.
- Full Starter unit suite: 271 passed.
- Fresh-clone install/verify/upgrade/rollback/hard-kill integration: 60 passed, 0 failed, pinned to the implementation commit.
- The fresh install selected 122 files: 86 managed and 36 seed. `FF_CORE_KEY` read back as optional and not configured.
- Adapter declaration check passed.
- Caller bytes match the source hash `19046b52c42132f6656e24fd0b2a73d616cc6ad532ea9a4cc2a3d8064eab8638`.

The HTTP behavior tests use a synthetic loopback service. They prove the installed caller's success, denial, missing-key and output-retention behavior; they do not claim a hosted FF endpoint.

## Consumer disposition

- Starter package contract: `UPDATED` in this candidate.
- Existing approved Starter 2.8.0: `DEFERRED`; immutable and unchanged.
- FF Client Zero live proof: `SCHEDULED` immediately after this exact caller is independently reviewed and merged. The AIOS proof will record the merged Starter revision in its receipt.
- External clients: `DEFERRED`; no client entitlement or production endpoint exists.

## Rollback and next dependency

Rollback is a normal revert of `d812f103ef57ba7600c1fe56458331748f33d356`; no client data or provider state was changed.

Next executable action: review and merge the Starter PR, then rerun the real FF-as-client acceptance against this exact installed caller. Production remains blocked on a hosted HTTPS bridge and a per-client GitHub App installation path; those missing integrations do not block the local Client Zero proof or the remaining commercial/Portal reconciliation.
