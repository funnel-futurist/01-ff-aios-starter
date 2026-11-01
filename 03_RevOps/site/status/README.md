# Read a local work snapshot

This page shows a supplied projection of a learner's existing plan and work records. A projection is a display copy written by the designated Coordinator. The plan and work records remain authoritative. The page never collects records, changes their state or awards acceptance.

This is an isolated local candidate. It is not included in an approved release, installed on a learner's workspace or hosted. The sample contains fictional work only.

## Open and read

1. Keep `index.html` and `status.js` together. Open `index.html` in a browser. No server, account or installation is needed.
2. Choose `example_status.json` with the file picker. The source time is fixed, so the example will become stale. Reopening it does not make its evidence newer.
3. Read the canonical sources, source time, declared coverage and omissions before the work cards. The local read and render times describe this page's actions, not new source evidence.
4. Try an invalid JSON file. The failed load stays visible. A previously loaded snapshot remains visibly marked as the last-good view. Without an earlier successful load, no work is shown.

The page reads only the file you select, in browser memory. It performs no network request or upload and uses no browser storage. Closing or reloading it clears the snapshot. Canonical source files are not modified. HTTPS source links open only when you choose them; other source references are displayed as text. Do not use private learner data for this local candidate's testing.

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

The four files in this site folder are client-owned seeds under the current package specification. The test does not ship. This candidate does not edit release records; later packaging belongs to the release owner. Once a runnable setup method and installation/readback evidence exist, the existing teaching owner can resume the related lesson. Hosting still needs the actual audience/access choice, access configuration and reader/refusal checks in the learner's own account.
