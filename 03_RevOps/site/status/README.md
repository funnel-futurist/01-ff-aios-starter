# Read a local work snapshot

This page shows a supplied projection of a learner's existing plan and work records. A projection is a display copy written by the designated Coordinator. The plan and work records remain authoritative. The page never collects records, changes their state or awards acceptance.

This is an isolated local candidate. It is not included in an approved release, installed on a learner's workspace or hosted. The sample contains fictional work only.

## Open and read

1. Keep `index.html` and `status.js` together. Open `index.html` in a browser. No server, account or installation is needed.
2. Choose `example_status.json` with the file picker. The source time is fixed, so the example will become stale. Reopening it does not make its evidence newer.
3. Read the canonical sources, source time, declared coverage and omissions before the work cards. The local read and render times describe this page's actions, not new source evidence.
4. Try an invalid JSON file. The failed load stays visible. A previously loaded snapshot remains visibly marked as the last-good view. Without an earlier successful load, no work is shown.

The page reads only the file you select, in browser memory. It performs no network request or upload and uses no browser storage. Closing or reloading it clears the snapshot. Canonical source files are not modified. HTTPS source links open only when you choose them; other source references are displayed as text. Do not use private learner data for this local candidate's testing.

## Export the existing tracker

The local source route is now `scripts/aios/learner_status_export.py`. It reads only the existing instance-owned `03_RevOps/customer_journey/task_tracker.md`, using that file's Active, Up Next and Completed tables. It never updates the tracker, collects other records or uses a network connection.

For explicitly invented practice rows in those existing tables, run from the repository root:

```sh
python3 scripts/aios/learner_status_export.py --repo . --output /tmp/learner_status.json --freshness-minutes 1440 --fictional
```

The output directory must already exist. Use a local output outside version-controlled content. The file is written with private permissions. `1440` is the example's explicit age policy, not a recommended operating standard. `--fictional` labels invented practice input and must not label real records. Candidate verification uses synthetic records only.

After exit 0, select that actual output file with **Choose a Coordinator projection**, without editing its JSON. A `REFUSED` error exits 2 and preserves any previous output. Fix the original tracker and export again. An export failure is visible in the command; this file-only reader has no connection through which it could learn that the command failed. Do not re-import an unchanged old output and describe it as a successful export or new source evidence.

### What the export establishes

The source revision is the SHA256 of the exact input bytes. `as_of` is the input file's filesystem modification time, explicitly labeled as local metadata. Re-exporting unchanged input changes neither of those fields. Copying a file can change its filesystem timestamp, so that time does not establish when the underlying work occurred or when an authority verified it.

The tracker records self-reported task progress. The exporter preserves every supported row's fields and reported status as visible text, including dates and notes exactly as supplied. It does not promote `In Progress`, `In Review` or `Completed` into verified execution, review, acceptance or assessment. The reader's canonical lifecycle badge remains **Unknown** for these rows, while the self-reported tracker status is shown in the card text. A Completed row's `By` value identifies the reported completer, not a current owner. Next actor and state-entry time remain unknown when the source supplies no such facts. Notes or URLs are not fabricated into typed evidence receipts.

The `tracker-...` IDs are deterministic display identifiers derived from normalized task labels. They survive owner/status/section changes, but renaming a task changes its display ID. They do not assign new canonical task identities or create another ledger. Duplicate labels, including across sections, are refused rather than merged or silently omitted. Coverage declares all nonempty rows in these three tables, not all work in the business. The unchanged template's blank placeholder rows are not tasks.

The adapter requires the actual table headings and columns. It refuses missing sections/statuses, unsupported statuses/columns, malformed or truncated rows, duplicate labels, invalid UTF-8, symlink input, future modification time and input/output beyond the reader's size/row limits. Unsupported escaped pipes are reported rather than guessed. Any validation or pre-replacement write failure leaves the previous output intact. Successful output replaces the prior file atomically; a retry with unchanged input produces identical bytes. This is local projection-file behavior, not installation or provider execution.

### Check the producing-to-reading connection

```sh
python3 -m unittest discover -s tests/aios -p test_learner_status_export.py -v
```

The affected tests create synthetic rows in the real tracker format, invoke the actual exporter and load its emitted bytes unchanged through the actual `status.js` reader. They also cover deterministic retry, missing/unsupported/duplicate input, source/provenance preservation and an interrupted replacement preserving last good. No compatible output fixture is hand-edited into place.

The normal template-only install-contract job discovers these Python tests. That same existing job now names `node --test tests/aios/test_learner_status_page.mjs` explicitly, so the reader's existing 12 tests are part of the normal command set. Actual hosted execution must be read back on the connected source candidate; a workflow edit alone is not a passing job.

## Supplied projection

The example declares `learner-status/1`, the format for this local reader. It uses the existing unit states: `ready`, `assigned`, `running`, `review`, `reviewed`, `source_complete`, `merged`, `deployed`, `accepted_in_use`, `blocked` and `parked`. It does not introduce another work-state vocabulary.

The designated Coordinator supplies a JSON projection from an existing learner-owned record home, selected explicitly when actual use is authorized. This method does not create a new repository, plan or task ledger. The example's source paths are invented, not a required folder layout.

Required snapshot fields are `schema`, timezone-bearing `as_of`, positive `freshness_minutes`, nonempty `sources` with exact `ref` and `revision`, explicit `units`, and `coverage` with `declared_ids` and `omitted_ids`. Displayed and omitted IDs must partition the declared scope. Files larger than 1 MiB or with more than 2000 displayed units are refused rather than silently truncated. Invalid or future source times are refused. A declared age limit is input policy, not proof that its sources are reliable; 1440 minutes is used only in the fictional example.

Each unit needs a unique stable `id`. Its supplied placement (`pocket`, `project`, `round`), owner, reviewer, next actor, outcome, source, state-entry time and agent/human effort are shown separately. Missing optional facts stay **Unknown**. A `blocker` names the affected `stage`, exact `dependency`, `next_actor`, `clearing_evidence` and sourced `next_look`; missing details stay unknown and hold only that dependent action.

`evidence` keeps `execution`, `source_complete`, `reviewed`, `merged`, `installed`, `deployed` and `accepted_in_use` separate. Each receipt carries `ref`, exact `revision` and timezone-bearing `observed_at`. For a reported running unit, a matching execution receipt also needs `owner`, `unit_id` and the unit's `execution_revision`. A claim or assignment is not execution. Supplied receipts remain unverified until their owning sources are checked. Owner acceptance must come from the linked owning decision; this reader cannot establish it. No progress percentage is inferred.

## Check the local candidate

From the repository root, run:

```sh
node --test tests/aios/test_learner_status_page.mjs
```

The tests exercise the same parser and view model used by the page. Local browser checks separately verify file selection, safe text rendering, visible failed-load retention and desktop/mobile layout. These checks do not prove installed or hosted use.

The four files in this site folder are client-owned seeds under the current package specification. The test does not ship. This candidate does not edit release records; later packaging belongs to the release owner. The local exporter/reader connection is now executable source. Official package delivery and install/upgrade/readback remain the release owner's separate candidate proof, and the existing teaching owner can use that exact route once it qualifies. Frozen 3.3 has no page seeds and remains unchanged; a distinct candidate must name its final payload. Hosting still needs the actual audience/access choice, access configuration and reader/refusal checks in the learner's own account.
