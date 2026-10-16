# Release brief: AIOS Starter 3.1.0

**Written for:** the founder, before approving. About four minutes.

> **Candidate, not approved.** `releases/starter-3.1.0.json` is a draft pinned to `@@PIN@@`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3).

## Decision
**Approve AIOS Starter 3.1.0 at `@@PIN7@@`.**
- It adds the one thing FF's own adoption needs (your G81 and G98 rulings): a way to bring the Starter into a repository that already exists, without overwriting anything. It also keeps who may approve founder-gated paths separate from who is a founder.
- For clients on 3.0.0 it's an ordinary upgrade: nothing moves. A 2.x client still gets the 3.0 folder move, as before. Review hardened three things that apply to every workspace, listed below: the committed install record is no longer trusted, a shallow clone can't upgrade, and an upgrade made before 3.1 is rolled back with its own installer.

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
| **The committed install record isn't trusted, for every workspace** | Anyone's pull request can edit `.aios/install.json`. So upgrade and `verify --repo` check the record against the release source and git history: the pinned release, its managed files, its folder layout, the seed lines (and, for an upgrade, the seeds already handled), and whether the workspace was adopted. On a fresh clone an adopted repository's record may call a file the release's only if git history shows the installer made it. Rollback acts only on the record its last operation here wrote or, to undo an adoption, the one committed with it. An edit that fails these checks is refused by upgrade and rollback, with nothing changed, and reported by verify. Every command that reads the record or the plan is listed, with what it trusts, in the install guide. |
| **A shallow clone can't upgrade** | A `git clone --depth 1` can't show that history, so an upgrade, or undoing an adoption, refuses until `git fetch --unshallow`. In a client's repository, the workflows the Starter ships never upgrade or undo an adoption against their own checkout (the job that runs the installer's tests runs only in the Starter's own repository, on temporary repositories it makes), so CI is unaffected. |
| **Undoing a finished adoption** | It needs the release's source, `aios rollback --repo <your ff-aios-starter clone>`, so only that release's files are removed. On a fresh clone it refuses if an upgrade or rollback came after the adoption, or if the record was added more than once: undo it where it ran, or with git. |
| **Rolling back an upgrade made before 3.1** | Refused, changing nothing: those installers kept no copy of the record they wrote. Roll it back with that release's own installer (`python3 scripts/aios/aios.py rollback --target .`, run in the workspace) or with git. |

**Who reads the install record, and what each one trusts**
- **Upgrade, and its dry run:** each field checked against the release source and git history, plus this machine's note of its last operation when there is one; the plan file you committed, which it applies.
- **Verify:** with `--repo`, the same checks, reported rather than acted on. Without it, only the record's own consistency, its paths and its git history.
- **Rolling back an upgrade:** only a record equal to the copy that upgrade kept on this machine.
- **Undoing an adoption:** only the record and plan as committed with the adoption (added once), the release source, and git history since.
- **Recovering an interrupted operation:** its local journal, and a record that journal names.
- **Install and adopt:** they write the record, and read it only to refuse when one is already there.
- **`aios start`:** the release line and any drift it shows. The founder-review check doesn't use it.
- **The new-release notice:** the installed version, which only changes the notice's text.
- **Clearing a dead lock:** only whether a record exists.
- **The notice and identity caches:** written only where the repository has no file of its own, and never read from a copy it tracks.

**What was proven** (detail in `evidence/dispatch/p22-starter/release-3.1.0/`):
@@PROOF@@

## Recommendation
**Approve.** It's the implementation route your G81 approval set and your G98 approval shaped. It is carded only once both model families approve the exact pin with no findings. Every code finding was fixed with a test shown to fail without its fix; findings in the documentation and this brief were corrected and checked by the next review round. For existing clients it changes nothing but safer internals and the hardening listed above.

## Consequence
- **If approved:**
  - Clients upgrade from 3.0.0 as usual, or from 2.x with the 3.0 folder move as before.
  - FF can then open its own adoption pull request into ai-os: the 18 files you approved (G98), FF's own role policy and plan (committed first), and the people map and install record the adoption writes, all in one commit. That's one reviewed pull request, after a rehearsal on a copy.
- **Downsides:**
  - The adopt mode needs a disk with hard links. A Mac's APFS, Linux's usual file systems and Windows NTFS have them; FAT and exFAT drives don't, and adoption refuses there and takes back anything it made.
  - A repository's plan must be kept current: each release that ships a new path needs it classified before upgrading.
  - A shallow clone must fetch its full history before an upgrade.
  - An upgrade an older installer made is rolled back with that installer, not this one.
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
- **No run on Windows.** Its file lock, byte-for-byte record writes and permission check are tested with stand-ins only, and hard links on NTFS aren't tested.
- **FF's adoption hasn't happened.** It was rehearsed on a throwaway copy of ai-os, and nothing was written to ai-os.
- **The protected-text scan is a copy-and-paste tripwire,** as before.
