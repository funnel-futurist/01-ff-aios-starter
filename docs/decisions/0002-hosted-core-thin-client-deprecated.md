# 0002 · The hosted-Core thin client is deprecated (no hosted Core)

**Scope:** release. **Status:** accepted 2026-11-11 (Phoenix, 03a #81 6792665307 and 6792949454, DW-697). **Supersedes:** the "Optional FF Intelligence capability" setup path. **Superseded by:** none.

## Problem
The Starter ships `.aios/core_bridge/core_call.py`, a thin client for a hosted FF Core service, and the optional credential `FF_CORE_KEY`. FF has decided on a GitHub-first AIOS with no hosted Core. A client's AIOS must keep working even if FF's infrastructure is completely unavailable. That leaves the thin client with no endpoint to call.

## Options
1. Remove the thin client and the credential in the next release.
2. Keep both unchanged, mark them deprecated, and stop recommending them.
3. Repoint the client at some other FF service.

## Decision
Option 2.
- **What ships unchanged:** `core_call.py`, its README, `instance.example.json`, the manifest and the optional `FF_CORE_KEY` entry. There is no code removal and no behaviour change, so an upgrade breaks nothing.
- **Notices:** the install guide's "Optional FF Intelligence capability" section and the README carry a deprecation notice.
- **Next release notes** (the next `releases/starter-X.Y.Z.BRIEF.md`) state: "`.aios/core_bridge/core_call.py` and `FF_CORE_KEY` are deprecated: no hosted Core exists. Client-facing FF methods will ship in your repository through the toolkit, scoped to your entitlement, once the methods pack is released."
- **Removal**, if ever, is a later release decision of its own.
- **Release follow-up:** the next release record lists this decision, as every record lists 0001, and carries the notes line above.

## Why
- **No surprises:** removing managed files in an upgrade would surprise workspaces that configured them.
- **Matches the architecture:** Option 3 would recreate the runtime dependency the architecture removes.
- **Where the value moves:** client-facing methods, including the premium workflows that apply, will ship into the client's own repository as an entitlement-scoped methods pack in a future release. Each pack is pinned and approved with the release like any managed file, and installs only for a purchased entitlement. That pack is not built yet.
