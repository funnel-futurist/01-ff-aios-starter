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

Limits are explicit: `--max-depth`, `--max-dirs`, `--max-repos`, `--timeout` for the whole run, `--git-timeout` for each command. The receipt's `coverage` block says what was read, what failed and what was not reached. Three conditions make coverage incomplete and are named in the receipt. A directory that could not be read is listed under `unreadable_paths`. Hitting the whole-run `--timeout`, including partway through the last repository, sets `timed_out`: each git command is bounded by the remaining budget and no further command runs after it. A repository that configures a content filter is not status-scanned, because `git status` would run that program and it could write; it is listed under `repos_status_skipped` with its branch, HEAD and upstream still read. The helper lists configuration key names only, never values, and if that listing fails for any reason (the capability probe, such as a Git that rejects the option) it skips status the same way and says so. Status also does not look inside a registered submodule, because it would run the child's filter before the child's own row is checked; a submodule is observed only through its own row, so a dirty child is not shown on its parent. Exit 0 means every repository found was read within the limits. Directories below `--max-depth` are not entered and are counted in `depth_cut`, so a repository that sits deeper is not found; raise the depth when that could matter. Exit 1 means the run finished with incomplete coverage and the receipt says why. Exit 2 means the request was refused before anything was scanned. Files that sit outside every repository are only counted (`loose_files_outside_repos`), never listed, so an unversioned draft or original media there must not be reported as inventoried or backup-safe from a count. A path that git reports for an ignored directory does not establish what its contents are or what they are worth. This is an inventory receipt, not a backup. A missing upstream or an unreadable path makes coverage partial. Do not overwrite or automatically replay an ambiguous result.

## Prompt for an AI assistant

Use this prompt for a session you start by hand in Claude Code or Codex. MODE (initial, start, end or closeout) is context you give the assistant; it is not an option of the helper. Keep the concrete folders in your own private notes, not in this file.

> Run the daily reconciliation in MODE for my workspace only. Read my current start file, my work list and my last handoff. Use only the access I have already set up; a missing account or tool holds only the step that needs it. Inventory the folders I named, and their nested repositories, with the read-only helper or equivalent read-only commands, and leave local edits, ignored files, drafts and original media exactly as they are. Keep what you observe private. Label anything stale or not reached.
>
> Compare what I intended with what is actually there. Call each real gap one of: missing function, missing proof, unavailable access, or out of sync. Fix routine factual errors that are inside the task, send anything that belongs to someone else to its owner, and keep going on independent work. Do not create a new master plan. Before anything is published, check the base branch and open changes touching the same files. Never silently stage everything, commit, push, delete, switch a shared checkout, upload private material or assume permission I have not given.
>
> For start, tell me what changed, what is unfinished or exists only on this computer, and what is next. For end, preserve the intended work and its test results, and update my restart note. For closeout, only propose what could be archived or removed and what would need recovery; do nothing until I say exactly which. Keep "prepared", "registered", "enabled", "ran" and "someone used it" as separate facts. Stay quiet when nothing changed. Finish with the real receipt or a bounded finding and one next step.

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
