# Release brief: AIOS Starter 3.0.0

**Written for:** the founder, before approving. About five minutes.

> **Candidate, not approved.** `releases/starter-3.0.0.json` is a draft pinned to `896a750bdd01e672cb753d4477e2cf1fc7cab0e6`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 3.0.0 at `896a750`.** It's the folder rebuild you ruled on 2026-10-14: one repository per company with phase folders, rebuilt on 2.10.0. Client files keep every byte, and the migration and rollback are proven.

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
- **Every starting version, each installed by its own installer:** the six approved releases (2.6.0, 2.7.0, 2.7.2, 2.8.0, 2.9.0 and 2.10.0) and the folder layouts of 2.6.1 and 2.7.1. Those two were never approved, so no real workspace carries their record; they ran on a rehearsal-only approval copy. Plus two previously upgraded workspaces (2.6.0 → 2.8.0 → 2.10.0 and 2.7.0 → 2.9.0) and one adopted workspace (2.7.2). Each carried the client's own edits: an edited seed, their own files in every old folder, a git-ignored `.env`, binary and executable files, a Unicode name, empty folders, junk files and their own `CLAUDE.md` rule.
- **For each of those 11:**
  - the dry run is blocked until Vercel is decided, and shows the exact map line;
  - after the upgrade, an independent proof finds every client file at its mapped path with the same bytes, size and permissions, and nothing else of theirs changed;
  - `CLAUDE.md` gains the line exactly once;
  - `verify` passes against the pinned commit;
  - rollback equals the actual pre-upgrade snapshot, field for field, and the upgrade then runs again;
  - an existing destination and a case-insensitive collision are each refused with nothing changed;
  - hard kills at 7 points in the upgrade and 3 in the rollback each recover to the exact snapshot.
- **The heavy run:** a 120 MB file and 6,000 git-ignored dependency files, with real SIGKILLs at five moments. Each recovered exactly; the full upgrade took 3.8 s.
- **A case-sensitive disk image:** `Plan.md` and `plan.md` side by side are refused, and rollback is exact.
- **R-A against Vercel's real API:** a throwaway project still building the old folder made the upgrade refuse with nothing changed. Once corrected, the upgrade verified and moved the site, a production deployment built from the new folder and served the page, and the project was deleted.
- **R-C:** an operator's edit at the new founder path is held; `instance check` fails and `start` says NOT RESTORED while `CODEOWNERS` names the old path.
- **Fresh Claude Code and Codex sessions,** in a fresh 3.0 install and in an upgraded workspace whose `CLAUDE.md` still lists the old folders, all name `00_AIOS/company/` and Operator Core v1.2.0.
- **Tests from a fresh clone of the candidate:** 459 unit and contract tests, 60/0 end-to-end on the real content, 17/17 PR floor, 49/49 hooks, and the allow-list in order.
- **Client names:** none in anything 3.0 adds. The whole-tree scan finds only the 14 ordinary-word matches `main` already has.
- **Protected text:** FF's private scan compared every one of its 15,595 protected files, the five over 25 MB included, and 0 were left unscanned. It found four overlaps, all generic: Python standard-library imports, `urllib` and `http.server` boilerplate, and GitHub documentation addresses.

**Three allow-listed public files changed one folder path each:** the `/humanize`, `/qc_review` and `/f6_completeness_check` skills. Their approved hashes were re-pinned in `release/public_methods.json`, and approving this release approves those three re-pins.

**Defects in shipped 2.x behaviour, fixed here because the 3.0 proof and its reviews found them:**
- **Empty folders:** an upgrade or rollback removed every empty folder in the workspace, including the client's own. Now it removes only folders it emptied itself.
- **Rollback after a crash:** if an upgrade was killed while still planning and the founder then ran `rollback`, it undid the previous successful upgrade. Now that rollback clears the stale lock and rolls nothing back.
- **Install into a folder that already has files:**
  - install could replace the client's own `CODEOWNERS` or `.aios/config.json` without a backup;
  - it didn't record a starter file the client already had, so the next upgrade refused it as a collision;
  - an owner GitHub ignores (not `@user`, `@org/team` or an email) installed "successfully".
  
  Now install checks everything before its first write, refuses with nothing changed, and records the client's file as theirs.
- **A starter file the client deleted** could come back, if a later release shipped it again or under another spelling, or if a 2.x record never listed it. It now stays deleted.
- **`verify --repo` and `adopt`:** `verify --repo` trusted the workspace's own list of release files, so a file dropped from both still verified; `adopt` ignored the executable bit. Both now check against the release itself.

## Recommendation
**Approve.** It's the layout you ruled on, rebuilt on the released 2.10.0. Your three release requirements are enforced in code and proven, and so is the proof bar you set: every starting version, previously upgraded and client-edited workspaces, existing destinations, case-insensitive collisions, interrupted moves, and exact rollback against the actual pre-upgrade snapshot. Two independent reviewers from different model families checked the move engine and the installer over many rounds (Gemini 10, Codex 9), and every real finding was fixed with a test (from round 5 on, each shown to fail without its fix).

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
1. **Say:** "Approve starter 3.0.0 at 896a750".
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
- **One shared-tooling file carries over unchanged.** `.claude/skills/pr_review/SKILL.md` is byte-identical to 2.10.0's, the one overlap found at that cut (shared with FF's own copy of the same skill). Its exception is ai-os #507, which waits on your security approval; this release doesn't change it.
- **Two Unicode spellings of one name weren't tried on a real disk:** macOS disks, even case-sensitive ones, treat them as one file. The planner's refusal of them is proven by tests.
- **33–45 hours was an estimate.** This brief reports what was proven, not how long it took.
