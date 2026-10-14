# Release brief: AIOS Starter 3.0.0

**Written for:** the founder, before approving. About five minutes.

> **Candidate, not approved.** `releases/starter-3.0.0.json` is a draft pinned to `20ffb362a196e06f2a39caa53f9ee3eea4a7aa77`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 3.0.0 at `20ffb36`.** It's the folder rebuild you ruled on 2026-10-14: one repository per company with phase folders, rebuilt on 2.10.0. Client files keep every byte, and the migration and rollback are proven.

## Principle
- **Paths change, bytes never do.** The upgrade moves the client's files: it never rewrites, merges or deletes them.
- **Refuse rather than guess.** Anything the move can't do safely stops the upgrade before anything changes, and the refusal names the file.
- **Your three requirements are release gates, not notes:**
  - **R-A:** Vercel verified before any folder moves.
  - **R-B:** one declared map line in `CLAUDE.md`.
  - **R-C:** founder review restored at the new paths, or `instance check` fails.

## Evidence
**What changes for a client**

| Change | What the client gets |
|---|---|
| **Seven domain folders** | `00_AIOS`, `01_Creation`, `02_Team_Ops`, `03_RevOps`, `04_Attention`, `05_Jobs`, `99_Archive` replace `01_Foundations` ... `11_Projects`. `00_AIOS/routing.md` lists every old folder and its new home. |
| **The move (on upgrade)** | Every file in an old folder moves, git-ignored ones included. Each keeps its exact bytes, size and permissions, re-hashed afterwards. A `layout_proof.json` in the backup lists every old path, new path and hash. Empty folders move too. `.DS_Store`, `Thumbs.db` and `desktop.ini` are set aside in the backup instead. |
| **No starter text is rewritten** | A starter file the client already has keeps their copy, edited or not. New folders get their new starter files. |
| **R-B: one line in `CLAUDE.md`** | `@00_AIOS/routing.md`, so Claude reads the new map. The dry run shows it, it's added once and never duplicated, and every other byte stays the same. Rollback restores the file exactly. |
| **R-A: Vercel checked first** | Every 3.0 upgrade reads Vercel with the client's token (read-only, never printed or saved). It refuses while any project still builds a folder it moves, and prints the exact new Root Directory. A client not on Vercel says so with `--no-vercel`; that's recorded, and refused if Vercel's own files are in the folders that move. |
| **R-C: founder review** | `aios instance check` fails, and `start` says "NOT RESTORED", until two things are true: `CODEOWNERS` sends every founder-lane path to a founder, and GitHub enforces code-owner review. The upgrade says so as its next step. |
| **Refusals, with nothing changed** | uncommitted work; an existing destination; two names that one Mac or Windows disk would see as one; a symbolic link, nested repository, submodule or other disk in an old folder; a linked destination folder; a hand-edited release file |
| **Recovery** | The whole move is journaled before the first file moves. A kill at any instant, in the upgrade or in a rollback, is finished by the next `rollback`. |
| **Two new cards** | [Move a Vercel site to its 3.0 folder](../docs/human_steps/move_a_vercel_site.md) and [Restore founder review after the 3.0 move](../docs/human_steps/restore_founder_review.md), checked against Vercel's and GitHub's docs on 10-14. |
| **Docs** | The install guide, `SETUP.md`, `README`, `GETTING_STARTED`, `taxonomy_rules.md`, the decision record (with a 10-14 amendment) and 10 skills now use the new paths. |

**What was proven** (detail in `evidence/dispatch/p22-starter/release-3.0.0/`):
@@PROOF@@

**Three allow-listed public files changed one folder path each:** the `/humanize`, `/qc_review` and `/f6_completeness_check` skills. Their approved hashes were re-pinned in `release/public_methods.json`, and approving this release approves those three re-pins.

**Two defects in shipped 2.x behaviour, fixed here because the 3.0 proof found them:**
- **Empty folders:** an upgrade or rollback removed every empty folder in the workspace, including the client's own. Now it removes only folders it emptied itself.
- **Rollback after a crash:** if an upgrade was killed while still planning and the founder then ran `rollback`, it undid the previous successful upgrade. Now that rollback clears the stale lock and rolls nothing back.

## Recommendation
**Approve.** It's the layout you ruled on, rebuilt on the released 2.10.0. Your three release requirements are enforced in code and proven, and so is the proof bar you set: every starting version, previously upgraded and client-edited workspaces, existing destinations, case-insensitive collisions, interrupted moves, and exact rollback against the actual pre-upgrade snapshot. Two independent reviewers from different model families checked the move engine over several rounds, and every real finding was fixed with a test.

## Consequence
- **If approved:**
  - New installs get the domain folders.
  - Existing workspaces upgrade with one command plus either a Vercel token or `--no-vercel`, then do one human step: [Restore founder review after the 3.0 move](../docs/human_steps/restore_founder_review.md).
  - 2.10.0 becomes `superseded`.
- **Downsides:**
  - **It's a breaking release.** Bookmarks and the client's own notes that name an old folder still name it. The upgrade lists those notes; it never edits them.
  - **A site on Vercel needs its Root Directory changed** in the same sitting as the upgrade (the card says so).
  - **Clients wait one step for founder review.** Until someone restores it, GitHub doesn't ask a founder about changes in the founder lane; `instance check` makes the gap loud.
  - **No starter text is refreshed.** A client who never edited the 2.x starter files keeps the 2.x wording in them.
- **Recovery:**
  - `rollback` restores a workspace exactly right after an upgrade, and keeps the client's later edits if they've worked since.
  - Set 3.0.0 to `withdrawn` and the installer refuses it.
- **If not approved:** clients stay on 2.10.0 with the numbered folders. The rebuild waits on the branch.

## Owner action
1. **Say:** "Approve starter 3.0.0 at 20ffb36".
2. Lane 0.1 records the approval:
   - a commit to `releases/` only, with the record re-cut byte-identical;
   - 2.10.0 marked `superseded`;
   - the tag `starter-3.0.0`, once `check-tag` passes.
3. **Platform approval:** GitHub requires one code owner's approval on the release pull request. Either founder's approval works.
4. Chat Zero merges with a merge commit as the FF Agents App.

**Success:** `main` equals the `starter-3.0.0` tag.

## What is not claimed
- **No run on Windows.** Case-insensitive behaviour was proven on macOS's default disk and on a case-sensitive disk image, and the planner folds case and Unicode the way Windows does. A Windows disk itself wasn't used.
- **The Vercel check can only see what the client's token can see.** If it can't read a scope it knows about, it refuses. It can't find a project in an account the token doesn't belong to.
- **References to old folders inside the client's own files are reported, not fixed.**
- **The protected-text scan is a copy-and-paste tripwire.** It doesn't catch paraphrase or text in images. A clean scan is evidence, not a guarantee.
- **33–45 hours was an estimate.** This brief reports what was proven, not how long it took.
