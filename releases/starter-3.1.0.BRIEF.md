# Release brief: AIOS Starter 3.1.0

**Written for:** the founder, before approving. About four minutes.

> **Candidate, not approved.** `releases/starter-3.1.0.json` is a draft pinned to `@@PIN@@`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 3.1.0 at `@@PIN7@@`.**
- It adds the one thing FF's own adoption needs (your G81 and G98 rulings): a way to bring the Starter into a repository that already exists, without overwriting anything. It also keeps who may approve founder-gated paths separate from who is a founder.
- For existing clients it's an ordinary upgrade: nothing moves.

## Principle
- **Only ever create.** Adopting into an existing repository never overwrites, merges or deletes a file of that repository's.
- **Nothing is inferred.** The repository's own committed plan names every path the release ships as adopted, kept as its own, or excluded. Anything unlisted, listed twice or covered by a catch-all refuses before a single write.
- **Review permission isn't founder status** (G98). A repository can name the accounts allowed to approve founder-gated paths. Founder status, and the founder-only actions, still come from each person's role.

## Evidence
**What changes**

| Change | What it means |
|---|---|
| **`aios adopt --existing`** (new) | A company's own repository adopts the release files its plan lists, and only those. Every adopted file must be absent; every file it calls its own must exist and is never written. It must be a git repository with the plan and its own role policy committed. Never a folder move, never a line added to `CLAUDE.md`. |
| **Rollback of an adoption** | It's journaled before its first write, and each file is recorded once it exists. `aios rollback` takes back exactly what it created and left unchanged, whether the adoption finished or was killed partway. Each new file appears whole, and can never replace a file that appeared meanwhile. |
| **Upgrading an adopted repository** | It writes only what the plan adopts, and the plan must still be committed. A new release path must be classified first, or the upgrade refuses. A file the plan stops adopting stays as the repository's own. |
| **`founder_lane_reviewers`** (new, optional) | It names who may approve founder-gated paths. `instance check` and the pull-request boundary check both honour it, and when it's set it's the whole permission. Unset, nothing changes for clients. |
| **Safer state files, for every workspace** | The installer's own records are written through unique temporary files, never a fixed name that something else could be. A release may never ship the installer's state paths, compared the way a Mac or Windows disk compares names. |

**What was proven** (detail in `evidence/dispatch/p22-starter/release-3.1.0/`):
@@PROOF@@

## Recommendation
**Approve.** It's the implementation route your G81 approval set and your G98 approval shaped. It was reviewed until both model families approved the exact pin, every finding was fixed with a test shown to fail without its fix, and it changes nothing for existing clients but safer internals.

## Consequence
- **If approved:**
  - Clients upgrade from 3.0.0 as usual, or from 2.x with the 3.0 folder move as before.
  - FF can then open its own adoption pull request into ai-os: the 18 files you approved (G98), FF's own role policy, and the plan. That's one reviewed pull request, after a rehearsal on a copy.
- **Downsides:**
  - The adopt mode needs a disk with hard links, which every Mac, Linux and Windows (NTFS) disk has.
  - A repository's plan must be kept current: each release that ships a new path needs it classified before upgrading.
- **Recovery:** `aios rollback` undoes an adoption or an upgrade. Setting 3.1.0 to `withdrawn` makes the installer refuse it.
- **If not approved:** FF's adoption waits; clients stay on 3.0.0.

## Owner action
1. **Say:** "Approve starter 3.1.0 at @@PIN7@@".
2. CL03 records the approval:
   - a `releases/`-only commit, with the record re-cut byte-identical;
   - 3.0.0 marked `superseded`;
   - the tag `starter-3.1.0`, once `check-tag` passes.
3. **Platform approval:** one code owner's approval on the release pull request.
4. Chat Zero merges as the FF Agents App. **Success:** `main` equals the tag.

## What is not claimed
- **No run on Windows.** Its file lock is tested with a stand-in only.
- **FF's adoption hasn't happened.** It was rehearsed on a throwaway copy of ai-os, and nothing was written to ai-os.
- **The protected-text scan is a copy-and-paste tripwire,** as before.
