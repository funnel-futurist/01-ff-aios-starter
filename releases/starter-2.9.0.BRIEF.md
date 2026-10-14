# Release brief: AIOS Starter 2.9.0

**Written for:** the founder, before approving. About three minutes.

> **Candidate, not approved.** `releases/starter-2.9.0.json` is a draft pinned to `e5646ae1691b8aee267fc0308d7ca321ca4917af`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 2.9.0 at `e5646ae`.** Every client's AI gets AIOS Operator Core 1.2.0, which teaches it how to write team updates and how to announce a rule change. The release also carries the three pull requests merged to `main` since 2.8.0 and not yet released: a sound when the AI finishes or needs you, and the Core Bridge client.

## Principle
- **Merged is not released.** A workspace installs only a release a founder approved at a pinned commit (D3). Until then, clients keep core 1.1.1 even though `main` moved.
- **A release is cut from `main`, and `main` must equal the tag.** So the core can't ship alone: whatever else is merged rides with it. That is why this brief covers three changes, not one.
- **An upgrade owns only release files.** It never writes a client's own files or data, and `rollback` restores the previous release exactly.

## Evidence
**What changes for a client**

| Change | Source | What the client gets |
|---|---|---|
| **Operator Core 1.2.0** | ai-os `003506ac4` (#492), client edition | Section 1: before writing a team message, the AI finds the workspace's own channels and templates, keeps one thread per project with short updates, asks before sending, and doesn't mention bots by default. Section 8: after an approved rule change, it drafts a short team notice and asks before sending. No channel, link or name from FF ships: those stay in each workspace's own configuration. Same three declared client-edition differences as 1.1.1. |
| **Sounds and `/pause` `/play`** | Starter #31 | A short sound when Claude or Codex finishes or needs you (Mac). One switch per computer turns them off. |
| **Core Bridge client** | Starter #32, #33 | A small caller under `.aios/core_bridge/`, with no FF method in it. It does nothing without an optional `FF_CORE_KEY` and a per-workspace config the client owns. No hosted endpoint or client entitlement exists yet. |

Left out on purpose: #492's two other files are FF's own team updates and stay in ai-os.

**What was proven** (the real installer, run from a fresh GitHub clone of this branch; detail in `evidence/dispatch/p22-starter/core-1.2.0/`):
- **Fresh install:** `verify` matches. The core reads v1.2.0 and its bytes match the manifest's pin. `CLAUDE.md` imports it once. No `releases/`, `tests/` or `evidence/`, and no private writing canon or team-update text.
- **Upgrade from 2.8.0** with the client's own `CLAUDE.md` rule, a deliverable, foundation notes, their own skill and a settings override: **every file the release doesn't own is byte-identical** by the installer's own fingerprint. History kept, `verify` matches. 11 release files change and 8 are added.
- **Upgrade from 2.7.2:** the same, identical.
- **Rollback to 2.8.0:** the whole workspace is byte-identical to before the upgrade (the installer keeps its own git-ignored undo copy), `git status` is clean, and the core reads v1.1.1 again.
- **A hand-edited core** makes the upgrade refuse, and the client's edit stays.
- **Fresh sessions** (Claude Code, Haiku): workspaces on 2.9.0 name "AIOS Operator Core v1.2.0" and answer from its new rules. The rolled-back workspace names v1.1.1 and says those rules are "not covered". A workspace with no core says NONE.
- **Nothing private ships:** 0 findings when the whole public tree (166 files) was scanned for text from the two team files and the private writing canon. Both planted copies were caught. 0 client names in the 122 package files.
- **Tests:** 282 unit (5 new pin the core's bytes to its manifest), 60 integration, 17 PR-floor, 49 hook. Adapter and allow-list checks pass.

## Recommendation
**Approve.** The alternative is a 2.8.1 cut from the 2.8.0 tag with only the core. It ships the core without the other two changes, but `main` would no longer equal the tag. The next release would then have to reconcile the split, and that check is how we know what clients run. Holding everything until the Bridge has a hosted endpoint delays the core for a file that does nothing without a key.

## Consequence
- **If approved:** new installs and upgrades get core 1.2.0, the sounds and the Bridge client. 2.8.0 is marked `superseded`.
- **Downsides:** the Bridge caller becomes part of a public approved release before any client can use it. It is reviewed, method-free and inert without a key. The sounds play on Macs until someone runs `/pause`.
- **Recovery:** set 2.9.0 to `withdrawn` and the installer refuses it. `rollback` is tested and restores the workspace byte for byte.
- **If not approved:** clients' AI keeps 1.1.1. It has no rule for team-update routing, bot mentions or rule-change notices, so client sessions and FF's own sessions work differently.

## Owner action
1. **Say:** "Approve starter 2.9.0 at e5646ae".
2. Lane 0.1 records the approval (a commit to `releases/` only, re-cut byte-identical), tags `starter-2.9.0` once `check-tag` passes, and marks 2.8.0 `superseded`.
3. **Platform approval:** GitHub requires one code owner's approval on `releases/`. Either founder's approval works. The technical review is done separately.
4. Chat Zero merges with a merge commit as the FF Agents App.

**Success:** `main` equals the `starter-2.9.0` tag and shows `protected: true`.

## What is not claimed
- **No hosted Bridge, and no client can call FF yet.** The Bridge owner reruns its FF-as-client proof from the merged revision; that is their step, not this release's.
- **The protected-text scan used a targeted list:** the material this release must not carry. The full private list isn't configured here, and CI prints `NOT RUN` for it.
- **No team notice was sent.** Section 8 asks before sending one.
- **The session test ran with hooks off,** so no sounds played during it. The hooks have their own tests.
