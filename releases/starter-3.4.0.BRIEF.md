# Release brief: AIOS Starter 3.4.0 (DRAFT)

**For the founder and release owner.** This candidate adds a usable local task-tracker view and corrects the explanation skill's ordinary-work behavior. The actual release remains `draft`, with both approval fields empty. Approved 3.2.0 remains unchanged. The separate 3.3.0 draft is frozen history; this candidate does not approve it.

## Exact payload

The official builder selected 174 files: 109 managed files, 65 starter files and 25 skills, pinned at `509908d696a87dadbd8e87b0def549fb3ef202f8`. The SHA-256 of `releases/starter-3.4.0.json` is `c7f969e72bf495d7beb3ea63c9580afefc21a24e557af0c59b7e84f5fec48c60`.

Compared with approved 3.2.0, eight files are added and none removed. The minimum upgrade version remains 2.6.0, and the existing layout and credential-reference rules are unchanged. The four page files are starter files; the exporter and explanation skill are managed. Tests are excluded from the install payload. No package-selector change was needed.

## What changes for a learner

| Capability | Practical result |
|---|---|
| Local task-tracker exporter and page | Run the installed `scripts/aios/learner_status_export.py` against the existing `03_RevOps/customer_journey/task_tracker.md`, then select its actual output in `03_RevOps/site/status/index.html`. No JSON editing is needed. The page has no automatic feed or hosting dependency. |
| Honest progress display | Original task fields and reported statuses remain visible. Canonical lifecycle state, verified evidence, reviewer and next actor remain unknown when the tracker does not supply them. A Completed row does not become acceptance, a grade or a certificate. |
| Explanation skill correction | Ordinary explanations end with practical meaning and the next action, without making someone repeat the explanation before work can continue. Explicit learning exercises and adopted assessment requirements keep their appropriate comprehension checks. |
| Daily routine and earlier integrated corrections | This successor also carries the 3.3 draft's client-edition daily reconciliation helper and instructions, repository explanation, reviewer wording and onboarding setup order. No scheduler is created. |

The exporter reads the three existing tracker tables. It gives rows derived display IDs, so renaming a task changes its ID; it creates no new task ledger. Source freshness comes from the local file's modification time and an explicitly supplied age limit. That time is not verified evidence age. Unsupported input refuses visibly and retains any previous output. Import a newly exported file only after the command exits successfully; the file-only page cannot observe an exporter command that failed elsewhere.

## Install and preservation evidence

On 2026-10-31 Pacific time, the shipped official CLI was exercised in a private source clone, with a scrubbed environment, invented organization and stub test identity. The actual draft refused installation with exit 2 before target files were written.

For the positive tests only, that private clone used the shipped integration contract's literal `internal-validation-fixture (NOT a human approval)` record. Official fresh install and approved-3.2.0-to-fixture-3.4.0 upgrade both passed ordinary verification and stronger `verify --repo` readback. Installed exporter, skill and page bytes/modes matched the candidate. Both installed exporters produced invented three-row snapshots accepted unchanged by their installed readers, retaining null lifecycle state and empty evidence.

Edited `CLAUDE.md` and task-tracker starter files, an ignored settings override and unmanaged work survived. A preexisting path for the new page README caused the expected conservative collision refusal, preserving its bytes. The invented note was then moved and committed beside the incoming README before the successful upgrade. An existing workspace with a colliding new path must resolve it before upgrading; the installer does not silently overwrite it.

The retained receipt is linked from working unit [03a #244](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244). It records the fixture scope and actual commands. A corrected private probe assertion is retained alongside its initial failure: the view model keeps null state, while the existing browser renderer labels it Unknown. No shipped runtime change was needed. Previous actual browser-import proof is retained by exact installed reader-byte comparison; no new installed browser session or real learner result is claimed.

## Release and use instructions

The release owner must approve this exact payload through the existing independent-review, eligible GitHub-review and founder decision route before any real installation. The real manifest must then pass `release verify` as approved. Private fixture approval is never an installation instruction for a learner.

After the actual approved record exists, use the ordinary official commands from the Starter source clone:

```sh
python3 scripts/aios/aios.py release verify releases/starter-3.4.0.json --repo .
python3 scripts/aios/aios.py install --release releases/starter-3.4.0.json --repo . --target /absolute/path/to/new-workspace --config /absolute/path/to/org-config.json
# For an existing installed workspace, use upgrade instead of install:
python3 scripts/aios/aios.py upgrade --release releases/starter-3.4.0.json --repo . --target /absolute/path/to/workspace
python3 scripts/aios/aios.py verify --target /absolute/path/to/workspace --repo .
```

From the installed workspace, choose an existing private output directory and an explicit freshness policy, then run:

```sh
python3 scripts/aios/learner_status_export.py --repo . --output /absolute/private/directory/learner-status.json --freshness-minutes 1440
```

The 1440-minute value is an example, not a prescribed operating policy. Use `--fictional` only for invented practice input. Open the installed local page and select that exact output after exit 0. Existing starter files remain the owner's files: an upgrade does not rewrite an edited `CLAUDE.md` or page, and a customized page is not claimed to match the shipped reader. The managed skills README names the explanation skill; Codex users open its file by hand as instructed. No fresh host registration, authenticated use, learner acceptance, deployment, tag or real release approval is established by this fixture qualification.
