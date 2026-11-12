# Starter 3.6.0 draft: explain-from-the-ground-up writing standard, delegated install, phase unlock and a second compatible package

This is a draft release record.
A draft (a release record nobody has approved yet) cannot be installed.
It has no published tag (a fixed Git name for one exact commit).
The payload (the exact set of files this release ships) is pinned to commit `3fdd782b422598d774c67518c0bd908138d91972`.
The founder approves the exact payload later.
This record does not approve itself.

## Identity and version

The name is `starter-3.6.0`.
The version follows semver (semantic versioning: MAJOR.MINOR.PATCH).
A minor bump (the middle number) means new managed capability that existing workspaces can take without a new folder layout.
This release adds new commands and files, and it changes no folder layout.
So it is the next unused minor after published 3.5.0.
The repo's own generator built the manifest (the machine-readable list of files and their hashes).
It wrote `status: draft` and blank approval fields.

## What the package holds

The manifest selects 195 files.
Managed files (files the installer owns and replaces on upgrade): 126.
Seed files (starter files written once, then owned by the workspace): 69.
Canonical skills: 25.
Compared with 3.5.0, it adds 10 files (6 managed, 4 seed), changes 20 files (13 managed, 7 seed) and removes none.
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

## What the installer and upgrade do

A fresh install writes the 126 managed files and the 69 seed files.
An upgrade replaces changed managed files and adds the new ones.
It leaves client-owned files alone, including `CLAUDE.md` customizations, foundations and local settings.
If a managed file was edited by hand, the installer refuses and changes nothing.
Reconcile the edit first; do not force the upgrade.
Rollback restores the earlier release's managed files.

## How to verify

Run `python3 scripts/aios/aios.py release verify releases/starter-3.6.0.json`.
It should report the payload intact and the record still a draft.
Run `python3 00-standards/check.py origin/main`.
Run `python3 scripts/aios/aios.py protected check-allowlist`.
Run the suite: `python3 -m unittest discover -s tests/aios -t tests/aios`.

## Next gates

The founder approves the exact payload and record.
The full protected-text scan runs on the final tree before approval.
The approved record is then reviewed, merged and tagged in separate steps.
This draft authorizes no tag, push, default change, installation or trust change.
