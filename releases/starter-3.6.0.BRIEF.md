# Starter 3.6.0: explain-from-the-ground-up writing standard, delegated install, phase unlock and a second compatible package

This is the approved release record (`status: approved`).
It was a draft (a release record nobody had approved yet) until this approval commit, the "carrier".
It has no published tag yet (a fixed Git name for one exact commit); the tag follows the carrier's merge.
The payload (the exact set of files this release ships) is pinned to commit `2683816b1fa23cdf57d4d85356b27781b5e91e86`.
Phoenix (`phoenix-ship-it`) approved the exact payload and record natively on Starter PR #89 (review at 2026-11-20T11:24:47Z, head `3fcacf81`, merged as `09623ac7`).
Phoenix's native approval of the carrier PR is the founder's approval act for these fields; this record does not approve itself.

## Identity and version

The name is `starter-3.6.0`.
The version follows semver (semantic versioning: MAJOR.MINOR.PATCH).
A minor bump (the middle number) means new managed capability that existing workspaces can take without a new folder layout.
This release adds new commands and files, and it changes no folder layout.
So it is the next unused minor after published 3.5.0.
The repo's own generator built the manifest (the machine-readable list of files and their hashes).
It wrote `status: draft` and blank approval fields; the carrier then set `status: approved` and `approval.approved_by`, `approval.approved_at` and `approval.basis`.

## What the package holds

The manifest selects 196 files.
Managed files (files the installer owns and replaces on upgrade): 127.
Seed files (starter files written once, then owned by the workspace): 69.
Canonical skills: 25.
Compared with 3.5.0, it adds 11 files (7 managed, 4 seed), changes 23 files (15 managed, 8 seed) and removes none.
The folder layout, `min_upgrade_from: 2.6.0`, credential references and null AIOS-release link are unchanged.

## What changed since 3.5.0

- #82: the `explain-from-the-ground-up` skill now carries the FF writing standard.
  It means short sentences, one per line.
  It means each term is defined in parentheses the first time it appears.
  It means the basics come before the details.
  The skill was rewritten to follow its own standard, and it defines teach-back (asking the reader to say it back in their own words).
- #75: the Core caller (the small script that talks to the hosted FF service) moves from 0.1.5 to 0.3 and stays compatible with existing workspaces.
- #77: delegated install lets a helper install a release only under a founder grant tied to a real actor, target and release.
- #78: the hosted-Core thin client is marked deprecated in decision 0002; no code is removed.
- #79: Evergreen docs add five-brain routing, operator journeys and setup alignment.
- #80: `aios.py phase unlock` adds the buyer side of license-key phase gating (opening a paid phase with a key).
- #81: a setup guide for signing in to the board with GitHub, plus its evidence sections.
- #83: adds the Bowtie placement map, which names its path without linking a private repo.
- #85: the installer also accepts one second package, `life-os-release-1`, read only from a pinned commit.
- #86: adds the Supabase and GitHub standard (`docs/standards/SUPABASE_GITHUB.md`), the Starter copy of the FF standard.
- #87: `start-my-day`, `wrap-up` and the daily handoff routine now require verified continuation and safe replay recovery.
- #88: corrects the install and upgrade guide (`docs/INSTALL_AND_UPGRADE.md`), reviewed in 03a #259.

## What the installer and upgrade do

A fresh install writes the 127 managed files and the 69 seed files.
An upgrade replaces changed managed files and adds the new ones.
It leaves client-owned files alone, including `CLAUDE.md` customizations, foundations and local settings.
If a managed file was edited by hand, the installer refuses and changes nothing.
Reconcile the edit first; do not force the upgrade.
Rollback restores the earlier release's managed files.

For a client on 3.5.0, follow `docs/INSTALL_AND_UPGRADE.md`, run from the Starter clone:
`git fetch --tags origin`, then `python3 scripts/aios/aios.py release check-tag starter-3.6.0 --release-id starter-3.6.0`.
Only once that passes, `git checkout starter-3.6.0`.
Then `python3 scripts/aios/aios.py upgrade --release releases/starter-3.6.0.json --target ../my-workspace --dry-run` (writes nothing).
Then the same command without `--dry-run`.
Afterwards, check the workspace with `python3 scripts/aios/aios.py verify --target .` (a workspace holds no release records).
To go back to 3.5.0, run `python3 scripts/aios/aios.py rollback --target .` in the workspace.
Rollback removes the 7 managed files 3.6.0 added, and the 4 added seed files if you have not edited them.
3.6.0 changes no folder layout, so rollback moves no files between folders.

## How to verify

Run `python3 scripts/aios/aios.py release verify releases/starter-3.6.0.json`.
It should report the payload intact and the record still a draft.
Run `python3 00-standards/check.py origin/main`.
Run `python3 scripts/aios/aios.py protected check-allowlist`.
Run the suite: `python3 -m unittest discover -s tests/aios -t tests/aios`.

## Next gates

Done: the founder approved the exact payload and record (#89), and the carrier records it.
The full protected-text scan of payload `2683816b` is done: disposition CLEAR (03a #244, comment 7036570936).
It checked 15157 protected blobs, left 0 unscanned, and found 132 rule findings, all classified with 0 unresolved.
An independent sanitized-evidence review passed.
Sanitized evidence SHA-256 `00fa27346fc69e09a059e72bc76ca66139f709888bf1599835d344259df0f71c`.
The approval commit (the "carrier") changes only this record and brief.
Before tagging, confirm that with `git diff --name-only 2683816b <carrier>`.
The approved record is then reviewed, merged and tagged in separate steps.
This record authorizes the tag steps below only after the carrier is reviewed and merged. It authorizes no default change, installation or trust change.

## Exact release commands (for after approval and merge only)

1. The founder fills `approval.approved_by`, `approval.approved_at` and `status: approved` in `releases/starter-3.6.0.json`. This is a human act.
2. The approval PR is reviewed and merged to `main`. Call the merged commit `<carrier>`.
3. `git diff --name-only 2683816b1fa23cdf57d4d85356b27781b5e91e86 <carrier>` must list only `releases/starter-3.6.0.json` and `releases/starter-3.6.0.BRIEF.md`.
4. `python3 scripts/aios/aios.py release verify releases/starter-3.6.0.json` at `<carrier>` must say installable.
5. `git tag -a starter-3.6.0 <carrier> -m "Approved Starter 3.6.0 release"`
6. `python3 scripts/aios/aios.py release check-tag --release-id starter-3.6.0 starter-3.6.0` must pass.
7. Push the tag with the FF Agents App identity: `git push origin refs/tags/starter-3.6.0`.
