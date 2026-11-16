# Daily reconciliation

This is the shared procedure behind `/start-my-day` and `/wrap-up`. It helps you see, before you move anything, which of your work exists only on this computer. It prepares a routine you run yourself. It does not register a scheduler, send anything or change a repository, and the receipt it writes is private to you.

## Set it up once, then refresh when something changes

Decide which folders hold your work. A folder can be one repository or a container of many. Write down, in a private place outside any repository, each folder's full path, what it is for, who owns its decisions, and any folder you never want entered. Use an absolute path for each root. A nested repository, including a linked worktree whose `.git` is a file, is its own observation, and the target of a symbolic link is treated as not inspected. Keep real paths, change lists and receipts out of your repository and out of anything you share.

Pick a private folder for receipts that is outside every repository, then run the helper from your workspace, naming each folder you want checked:

```sh
python3 .claude/skills/start-my-day/scripts/reconcile_local.py \
  --root /absolute/path/to/work --root /absolute/path/to/other/work \
  --exclude /absolute/path/to/skip --out-dir /absolute/private/receipts
```

Nothing is scanned unless named. The home directory and the filesystem root are refused, and so is an output directory inside any Git repository or inside a scanned root. The receipt is a new file in `--out-dir` (mode 0600, directory 0700) and is never overwritten; the console prints counts only.

The helper walks the named roots without following symlinks and skips `.git` internals. It runs only read-only Git commands, with optional locks and fsmonitor disabled and no fetch, and records per repository: branch, HEAD, upstream and ahead/behind from the last fetched refs, linked-worktree flag, stash count, and counts of modified, staged, untracked, ignored and conflicted entries. A nested repository is its own entry and is not counted in its parent's untracked total. Path names are listed up to `--names-limit` per category, and a credential-like name is replaced by a placeholder. The receipt states `work_file_contents_returned: false` and `network_used: false`. Git may read tracked files internally to work out status, so do not claim Git reads nothing. The helper returns no file contents, remote URLs, git config values or credentials, and it performs no commit, checkout, stash, push, deletion, upload or delivery.

Limits are explicit: `--max-depth`, `--max-dirs`, `--max-repos`, `--timeout` for the whole run, `--git-timeout` for each command. The receipt's `coverage` block says what was read, what failed and what was not reached. Three conditions make coverage incomplete and are named in the receipt. A directory that could not be read is listed under `unreadable_paths`. Hitting the whole-run `--timeout`, including partway through the last repository, sets `timed_out`: each git command is bounded by the remaining budget and no further command runs after it. A repository that configures a content filter is not status-scanned, because `git status` would run that program and it could write; it is listed under `repos_status_skipped` with its branch, HEAD and upstream still read. The helper lists configuration key names only, never values, and if that listing fails for any reason (the capability probe, such as a Git that rejects the option) it skips status the same way and says so. Status also does not look inside a registered submodule, because it would run the child's filter before the child's own row is checked; a submodule is observed only through its own row, so a dirty child is not shown on its parent. Exit 0 means every repository found was read within the limits. Directories below `--max-depth` are not entered and are counted in `depth_cut`, so a repository that sits deeper is not found; raise the depth when that could matter. Exit 1 means the run finished with incomplete coverage and the receipt says why. Exit 2 means the request was refused before anything was scanned. Files that sit outside every repository are only counted (`loose_files_outside_repos`), never listed, so an unversioned draft or original media there must not be reported as inventoried or backup-safe from a count. A path that git reports for an ignored directory does not establish what its contents are or what they are worth. This is an inventory receipt, not a backup. A missing upstream leaves the branch's ahead/behind comparison unknown; it does not itself make the configured-scope inventory incomplete. Unreadable paths and other recorded scan limits can make coverage partial. Report inventory coverage and publication comparison separately, without inferring zero unpushed work or backup safety. Do not overwrite or automatically replay an ambiguous result.

## Prompt for an AI assistant

Use this prompt for a session you start by hand in Claude Code or Codex. MODE (initial, start, end or closeout) is context you give the assistant; it is not an option of the helper. Keep the concrete folders in your own private notes, not in this file.

> Run the daily reconciliation in MODE for my workspace only. Read my current start file, my work list and my last handoff. Use only the access I have already set up; a missing account or tool holds only the step that needs it. Inventory the folders I named, and their nested repositories, with the read-only helper or equivalent read-only commands, and leave local edits, ignored files, drafts and original media exactly as they are. Keep what you observe private. Label anything stale or not reached.
>
> Compare what I intended with what is actually there. Call each real gap one of: missing function, missing proof, unavailable access, or out of sync. Fix routine factual errors that are inside the task, send anything that belongs to someone else to its owner, and keep going on independent work. Do not create a new master plan. Before anything is published, check the base branch and open changes touching the same files. Never silently stage everything, commit, push, delete, switch a shared checkout, upload private material or assume permission I have not given.
>
> For start, tell me what changed, what is unfinished or exists only on this computer, and what is next. For end, preserve the intended work and its test results, and update my restart note. For closeout, only propose what could be archived or removed and what would need recovery; do nothing until I say exactly which. Keep "prepared", "registered", "enabled", "ran" and "someone used it" as separate facts. Stay quiet when nothing changed. Finish with the real receipt or a bounded finding and one next step.

## Assignment closeout and programme coordination

Ordinary workers close only their assigned unit, preserve its evidence and return unresolved or downstream actions through the existing handoff. That role carries no authority to inspect another portfolio or broaden access.

An explicitly assigned programme lead or coordinator has one additional check before saying the authorised portfolio is exhausted: refresh the current canonical queue, source revisions and active claims across its declared scope. Reconcile ready and unassigned work, returned candidates, source-only completed work with unfinished downstream actions, and deferred work whose restart trigger has fired. Check each `unit + head + action` against its current owner and previous dispatch, then route the next eligible action through the existing authorised handoff and record actual dispatch and receiving evidence.

Keep owner, access, review, release and capacity holds attached to the step they affect, and continue eligible independent work. A portfolio-exhaustion claim requires fresh, complete source dispositions with no pending routing edge. Name any stale or missing evidence and its next clearing action. When only genuine holds remain, report their exact gate, next actor and clearing event; wait through the existing mechanism without idle polling or invented dispatch. Assignment closeout, passing checks, full seats or the local inventory helper's exit status do not establish portfolio exhaustion. This source procedure does not establish installed or observed adoption.

### Completion to the next eligible action

This contract uses the existing unit issue, canonical queue and authorised handoff. It adds no queue, schedule, provider call or permission. An ordinary worker returns its assigned result; only an explicitly assigned coordinator selects work across the declared scope. Existing capacity, review, publication and access rules still apply.

**One accountable owner per assignment.** Record the unit, exact artifact revision, next action and file/resource scope, with one current executor. A reviewer has a separate review action. Read current claims and receiving-session state before assigning; a new chat, different agent or repeated message does not release an existing claim. Conflicting scope cannot be assigned twice. Reserve conflicting scopes with an atomic conditional operation, or use a demonstrably serialized coordinator pass covering the current-state read, claim and durable dispatch reservation. Serialization must include overlapping turns from the same coordinator; a sole writer identity alone is insufficient. If neither mechanism is available, record a hold for that conflicting scope instead of assigning it. Do not infer a lock from prose.

**A return is a durable event.** Preserve its original locator, stable return ID, producer session/turn ID, unit, artifact revision, action, checks and remaining gates in the existing work record. A relayed copy keeps the original identity. A timestamp or message summary alone is not a stable ID. If the source supplies no durable ID, the records owner must assign and persist one before dispatch. Missing revision or producer identity is an evidence gap to resolve, not permission to invent a successful return.

**Replay must resume, not duplicate.** In the existing record, associate the return ID and producer turn ID with a dispatch key based on `unit + exact revision + next action`. The same return repeated, or a second return describing the same action, must resolve to the existing dispatch. A retry keeps that key and its attempt history. Never use a fresh event ID or turn ID to bypass an active claim. A changed revision needs a new eligibility check and reconciliation of the previous scope.

During the same coordinator pass that accepts a return:

1. Verify the exact artifact and record the completed action at its demonstrated stage. Source complete, merged, installed and accepted in use remain different facts.
2. Refresh the authorised queue, claims, dependencies and available capacity. Record the next eligible action or the specific reason none can start. Release only the completed action's claim; unfinished downstream gates keep their own owners.
3. Under the reservation mechanism above, claim the next eligible action once and persist its prepared launch request and dispatch key. Before invoking the existing authorised adapter, transition the dispatch from **PREPARED** to **POSSIBLY_SENT** with its attempt identifier in one atomic conditional write against the current reservation and attempt state, or under proven per-dispatch serialization covering that transition. Only the winning turn may invoke the adapter. A losing or overlapping recovery turn reads the winning attempt and follows uncertain-start recovery; it must not call the adapter from its earlier prepared-state read. A prepared request has not been attempted; a possibly-sent attempt may already reach the host even without a response. Route any required independent review as its own action. A release gate on one result does not prevent unrelated eligible work.
4. Record the actual receiving session and turn ID, then verify a host start event or an executed action attributable to that assignment. A queued message, accepted request, claim, scheduled check or open chat is not a verified start. Keep launch requested separate from running.
5. Leave the recovery checkpoint below. If the start is not confirmed, record that uncertainty and its clearing action in this pass. Continue eligible independent work within the existing capacity limit; do not end with only “handoff sent.”

“Same pass” means evaluate and attempt the next authorised eligible action before finishing this coordinator turn. It does not promise an immediate worker start when capacity, permissions or the executor are unavailable. If interrupted after recording the return, replay resumes from the saved checkpoint; deduplication must not suppress an unfinished eligibility or launch step.

### Recovery checkpoint and uncertain starts

Keep one restart point in the existing unit record, not a second ledger. It contains the source-return locator and ID, producer session/turn ID, unit/revision/action, executor, scope claim and expiry if used, dispatch key, last durable step, prepared request, attempt identifier and possibly-sent status persisted before the call, launch attempt result, receiving session/turn ID when known, next clearing action, owner and wake event. Use explicit `unknown` for unavailable evidence. Retain the artifact and checks; never place credentials or private source contents in the receipt.

Before recovery, read back that checkpoint and the host's actual state. An expired claim, timeout or missing heartbeat does not prove the worker stopped. If it is still running, preserve ownership. Recovery may send a prepared request only after rechecking its reservation and eligibility and winning the atomic or serialized PREPARED → POSSIBLY_SENT transition above. Reading a prepared request or holding its existing assignment is not permission to call the adapter; two recovery turns must not both begin an attempt. If an attempt is possibly sent, including a crash immediately before or after the adapter call, retry only with the same key under the host's verified idempotency guarantee or after conclusive reconciliation that the original attempt cannot start later. An empty lookup alone is insufficient: a queued or in-flight attempt may still start. Otherwise retain the uncertainty and reconcile by the saved dispatch key/session; hold that conflicting scope while other eligible work continues. Count uncertain and running reservations against capacity until reconciled. If the host conclusively proves the attempt cannot start now or later, or the original execution is confirmed ended and its scope released, a single owner may retry through an already-authorised executor and record the new attempt. A failed launch remains visible with its reason and recovery owner. Do not create an account, buy capacity or start another schedule to repair it.

Exactly-once launch needs host idempotency or reliable lookup of the original attempt. Without either, retain an uncertain launch for reconciliation instead of blindly retrying. A local dedupe record alone cannot prove exactly-once execution across a lost host acknowledgement. After a verified start, preserve the receiving turn ID so later returns can be matched to the assignment; a result from another turn or revision needs reconciliation before closing it.

### Bounded proof before claiming adoption

Use fictional units and the already-authorised test route. This source contract does not itself run a host or install automation. Keep a scenario receipt in the existing owning record:

| Scenario | Required evidence |
|---|---|
| Normal completion | One return, refreshed eligibility, one claim, saved request, receiving turn and verified start in the same coordinator pass, or a specific recorded start hold |
| Return delivered twice, including a relayed copy | Same return/producer identity and dispatch key; one accepted launch |
| Different return IDs for the same unit/revision/action | Existing claim/dispatch reused; no duplicate executor |
| Crash after return recording, before an attempt is marked | Replay resumes eligibility/reservation; a prepared, unattempted request can proceed once |
| Same checkpoint after possibly-sent marking: crash immediately before the adapter call or immediately after it, before acknowledgement | Both recover as ambiguous; same verified host idempotency key or conclusive reconciliation, never a blind new launch. Empty lookup does not clear an in-flight attempt |
| Overlapping claim attempts, including two turns from the same coordinator | Atomic conditional reservation or proven serialization across read/claim/dispatch reservation accepts one owner; the other observes that reservation. Without either, hold conflicting scope |
| Two recovery turns resume the same already-reserved PREPARED dispatch | Conditional transition or proven per-dispatch serialization admits one winning turn, one attempt and one adapter call; the losing turn observes POSSIBLY_SENT and reconciles without calling. This is separate from competing claims |
| Expired claim with a running worker | Host readback preserves ownership; no replacement launch |
| Executor unavailable or confirmed launch failure | Visible recoverable failure and next actor; unrelated eligible work continues |
| One item release-held, another ready | Only the held action waits; the ready item follows normal capacity and ownership rules |
| Changed revision or wrong receiving turn | Evidence mismatch remains unresolved; old approval/return cannot close new work |

A useful positive example is a reviewed guide returning, its source integration being verified, and the already-owned dependent link update starting in that coordinator pass. A useful failure example is a finished result left in a PR body until a later pickup: the missing return-ingestion checkpoint must be repaired even if a schedule fired. Keep real customer or company examples in their own records. Report source checks, synthetic rehearsal, observed host start and sustained use separately.

## Cadence

Run it by hand when you start and end a session, or pick a cadence that suits your working hours. This skill does not create a schedule. A saved prompt, an open session or a hook is not a schedule: if you later want one, set it up with the tool that supports it and read back its real configuration before you call it enabled. On a failed run, keep the receipt, the scope it covered and the last good state, then try the one dependency that failed again rather than repeating everything.

## What counts as evidence

| Evidence | What it proves |
|---|---|
| The routine and prompt exist | A method has been written down |
| The tool's own readback of a schedule | It is registered; enabled only if its status says so |
| A dated receipt with its limits | That particular run happened |
| Your work list or notes showing the result | The result reached where you keep it |
| You doing the work the routine prepared | It was useful |

## Check it on a throwaway workspace first

Try the helper where nothing matters, so you can see exactly what it reads and that it changes nothing. Put the throwaway folders somewhere you can delete by hand afterwards.

```sh
helper="$PWD/.claude/skills/start-my-day/scripts/reconcile_local.py"
demo=$(mktemp -d)
git init -q "$demo/work" && cd "$demo/work"
git config user.email demo@example.com && git config user.name demo
printf 'tracked\n' > tracked.txt && git add tracked.txt && git commit -q -m start
printf 'a change\n' >> tracked.txt        # a tracked edit
printf 'a draft\n' > draft.txt            # an untracked draft
printf 'originals/\nnested/\n' > .gitignore
mkdir originals nested && printf 'raw media\n' > originals/take1.bin
git init -q nested/inner                  # an ignored nested repository
git status --short > "$demo/before.txt"
python3 "$helper" --root "$demo/work" --out-dir "$demo/receipts"
git status --short | diff - "$demo/before.txt" && echo "nothing in the repository changed"
```

Run the first line from your workspace, so the helper's full path is recorded. The console shows counts only. Open the receipt in `$demo/receipts` and check that it found the nested repository and says what it did not cover. Then delete the throwaway folder yourself. If a result surprises you, treat the receipt as a finding to read, not as a backup or a reason to delete anything.
