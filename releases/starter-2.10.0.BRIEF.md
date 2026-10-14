# Release brief: AIOS Starter 2.10.0

**Written for:** the founder, before approving. About three minutes.

> **Candidate, not approved.** `releases/starter-2.10.0.json` is a draft pinned to `688521e47315850d3bffe055c48fddac0b6f5c9a`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 2.10.0 at `688521e`.** It's the small release agreed before the 3.0 folder rebuild. It bundles four reviewed pull requests:
- step-by-step cards for the human steps;
- instructions Codex can read;
- safer review workflows, whose reviewer can't change a client's branch;
- a daily notice when a newer approved release exists.

## Principle
- **Merged is not released.** A workspace installs only a release a founder approved at a pinned commit (D3).
- **`main` must equal the tag.** So the four ship together, in one release pull request, with this record.
- **An upgrade owns only release files.** It never writes a client's own files, and `rollback` restores the previous release exactly.

## Evidence
**What changes for a client**

| Change | From | What the client gets |
|---|---|---|
| **Human-step cards** | #35 | Seven click-by-click cards in `docs/human_steps/`: GitHub two-factor, removing an org member, a Supabase token, a Supabase backup, connecting Vercel, and running a terminal command from Claude. Each was re-checked against the vendor's docs on 10-14. The setup wizard now secures access before inviting the team, and `SECURITY.md` no longer overstates what the deny rules block. |
| **Codex reads the same instructions** | #36 | A generated `AGENTS.md`: the workspace's `CLAUDE.md` as shipped, plus the operator core, inlined. It carries the template's text, not a client's own edits: client rules for Codex go in `~/.codex/AGENTS.md`, and the file says so. |
| **Safer review workflows** | #38 | Every action is pinned to an exact version. Each job has only the access it uses, and only the separate auto-merge job can write, when switched on. The AI reviewer has no shell and no token: it reads the PR and writes its review, and a fixed step posts it. **In CI it now suggests exact fixes instead of pushing them.** |
| **Hearing about a new release** | #38 | Once a day, `aios start` and the session start show one line when a newer approved release exists. It's read-only, silent offline, and off with `AIOS_NO_RELEASE_NOTICE=1`. |
| **Docs** | this branch | The install guide records that the `starter-2.6.0` tag was withdrawn on 10-14, because it carried third-party files we may not redistribute. `CLAUDE.md`'s reviewer line matches the new behavior. |

#39 changes a maintainer document only. It isn't shipped to clients.

**What was proven** (the real installer, from a fresh GitHub clone; detail in `evidence/dispatch/p22-starter/release-2.10.0/`):
- **Fresh install:** `verify` matches, and the core is v1.2.0. `AGENTS.md` equals what the generator makes from the installed files. The cards, the notice and the pinned workflows are present.
- **Upgrade from 2.9.0** with the client's own rule, deliverable, notes, skill and settings: **every client file is byte-identical.** Rollback restores the whole workspace byte for byte.
- **Upgrades from 2.8.0 and from 2.6.0:** client files are kept. From 2.6.0, the bundled third-party document skills are removed, and the only change to the client's `CLAUDE.md` is the declared operator-core import line.
- **A client's own `AGENTS.md`:** the upgrade refuses, says which file, and changes nothing. A hand-edited workflow is refused too.
- **Fresh sessions:** Codex (reading `AGENTS.md`) and Claude Code both name "AIOS Operator Core v1.2.0" and describe the new reviewer correctly.
- **Tests:** 320 unit, 60 integration, 17 PR-floor, 49 hook tests. Adapters and allow-list pass.
- **Nothing private ships:** 0 client names. FF's protected-text scan at the cut found one overlap: the review skill's new wording, shared with FF's own copy of the same skill. It's classified as shared tooling, not method, and a narrow exception for it is in FF's security review.

## Recommendation
**Approve.**
- All four changes were reviewed on their own pull requests and pass together.
- Shipping them one at a time would need four approvals and four tags for the same result.
- The 3.0 rebuild is agreed to start from `main` after this release.

## Consequence
- **If approved:** new installs and upgrades get all of the above, and 2.9.0 becomes `superseded`. From 2.10.0 on, a workspace hears about later releases by itself.
- **Downsides:**
  - Clients who relied on the CI reviewer pushing small fixes now get exact suggestions instead. Running `/pr_review` themselves still applies them.
  - A client who wrote their own root `AGENTS.md` must move it before upgrading. The refusal explains how.
  - The notice makes one small read of GitHub per day.
  - `CLAUDE.md` belongs to the client after install, so the new reviewer sentence reaches existing workspaces only through these release notes.
- **Recovery:** set 2.10.0 to `withdrawn` and the installer refuses it. `rollback` is tested and restores a workspace byte for byte.
- **If not approved:** clients stay on 2.9.0: workflows not pinned, the reviewer able to push to their branch, no Codex instructions, no cards, no notice. The 3.0 rebuild waits.

## Owner action
1. **Say:** "Approve starter 2.10.0 at 688521e".
2. Lane 0.1 records the approval: a commit to `releases/` only, with the record re-cut byte-identical. It tags `starter-2.10.0` once `check-tag` passes, and marks 2.9.0 `superseded`.
3. **Platform approval:** GitHub requires one code owner's approval on the release pull request. Either founder's approval works.
4. Chat Zero merges with a merge commit as the FF Agents App.

**Success:** `main` equals the `starter-2.10.0` tag and shows `protected: true`. Then the 3.0 rebuild starts from that `main`.

## What is not claimed
- **The reviewer hasn't run inside Anthropic's GitHub Action itself,** because this repository has no Claude credential. The first credentialed review after release is that check. If it fails, the PR goes to a person and nothing auto-merges.
- **Existing 2.9.0 and older workspaces don't show the notice yet.** They get the code by installing this release.
- **The protected-text scan is a copy-and-paste tripwire.** It doesn't catch paraphrase or text in images. A clean scan is evidence, not a guarantee.
- **No run on Windows.**
