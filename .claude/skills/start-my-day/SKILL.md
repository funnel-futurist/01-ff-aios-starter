---
name: start-my-day
description: The safe daily boot ritual for working in this repo. Use at the start of any work session, or when the user says "start my day", "start here", "start my session", "begin work", "let's get started", or asks how to safely start / get on a branch. Reads where your work stands first (including work that exists only on this computer), identifies the operator, brings the latest official main in only when that is safe, gets them onto a well-named task branch, and pins down what "done" looks like. NOT for ending a session (use /wrap-up) and NOT for retiring, archiving or deleting a project, which needs its own decision. Pairs with /wrap-up.
---

# /start-my-day — the safe boot ritual

You are a calm, encouraging guide for a possibly non-technical operator. **Plain English. One step at a time. Confirm before moving on.** Never run a destructive command. If they seem lost, slow down and explain like they're brand new — and offer: *"want me to treat you like a total beginner and give you every step?"*

> **Mental model to reuse if they're unsure:** `main` is the one official timeline everyone trusts. A branch is your private side-timeline so you can't break the official one. Look at where your work stands before you move anything, and bring the latest in only when that is safe.

## Step 0 — Read the situation (deterministic)
```bash
bash scripts/team/git-safety-check.sh --fetch
```
Read the `KEY=VALUE` output. You now know: branch, on-main?, clean?, behind/ahead of main, identity, operator-file present?

**Pre-flight (do this before anything else):** if `GH_USER=unknown`, GitHub isn't connected yet - pushing and PRs will fail later. Stop and hand them the one-line fix: *"First, let's connect GitHub - run `gh auth login` and pick GitHub.com → HTTPS → login with a browser. Tell me when it's done."* Don't proceed past Step 5 until `gh` is authenticated.

## Step 1 — Who is working?
- If `OPERATOR_FILE=present`: read `.aios/local-operator.json` and greet them by name (use the `display_name` field, falling back to `operator`). Sanity-check the file's **`github`** field against `GH_USER`, and `GIT_EMAIL` looks like theirs. If they clearly **don't** match, say so plainly: *"this machine is signed in as X but the operator file says Y — is that right?"* (Don't pretend this is verified identity — it's a label.)
- **Operator-file field contract** (so the greeting/identity-check never silently no-ops): `operator` (slug), `display_name` (greeting), `github` (must equal `GH_USER`), `role`. Write exactly these keys.
- If `OPERATOR_FILE=absent`: ask *"What's your first name, and what's your GitHub username?"* Then copy `.aios/local-operator.example.json` → `.aios/local-operator.json` and fill in their answers. (Git-ignored — a local label so the routine can greet you, not a login.)

## Step 2 - See where your local work stands (read-only)
Before you move anything, find out what exists only on this computer. This step reads; it never changes anything.
- **One folder, one repository:** say what Step 0 actually shows: `DIRTY_FILES` (uncommitted changes), `AHEAD_MAIN` (commits ahead of the recorded `origin/main`), and the current branch. `AHEAD_MAIN` is not an unpushed-commit count: a fully pushed task branch can still be ahead of main. If publication status matters, use the helper below even for one repository. Its ahead/behind counts compare HEAD with the branch's last-fetched configured upstream, not every remote or backup. Missing upstream or a failed comparison means unknown, never zero or "exists nowhere else."
- **More than one folder, nested repositories, or you've been away:** run the bundled read-only helper and name each folder you want checked. Nothing is scanned unless you name it, and your home folder is refused:
  ```bash
  python3 .claude/skills/start-my-day/scripts/reconcile_local.py \
    --root /absolute/path/to/a/work/folder --exclude /absolute/path/to/skip \
    --out-dir /absolute/path/to/a/private/folder/outside/any/repo
  ```
  It reads each repository's branch, last commit, ahead/behind from the last fetch, stash count and the counts of changed, staged, untracked, ignored and conflicted files, and writes one private receipt. It never fetches, switches, pulls, stashes, cleans or deletes. Read its coverage limits out loud: a folder it could not reach, or a depth it did not enter, is not an empty result. Details and a throwaway check: `.claude/skills/start-my-day/references/reconciliation.md`.
- Report observed local work and publication status separately: uncommitted changes, ignored originals, drafts, nested repositories and commits ahead of a verified recorded upstream. State which comparison was checked, when its refs were fetched if known, and which publication or backup facts remain unknown. None of these counts proves a file or commit exists nowhere else. A name like `scratch` or `old` is not a reason to delete anything.

## Step 3 - New work, or continue something?
- If `ON_MAIN=true`: explain *"`main` is the official timeline - we never work directly on it,"* then go to Step 5 to make a branch.
- If on a task branch already: tell them which one and ask *"continue this, or start something new?"* New → Step 4 then 5. Continue → Step 4 (offer to bring main's latest into it via a safe `git merge origin/main`, only when the checkout is clean), then Step 6.

## Step 4 - Bring in the latest official version (only when it is safe)
- If `WORKTREE_CLEAN=true`, `BEHIND_MAIN > 0`, this is the operator's own checkout (not a folder someone else or another session is using), and preservation of the work on the branch you'd leave is verified: bring the official version current. `AHEAD_MAIN` alone neither proves unpushed work nor triggers a refusal. Explain *"pulling the latest so you're not building on something old,"* then:
  ```bash
  git checkout main && git pull --ff-only origin main
  ```
  (Fast-forward only — never a merge commit, never force. If git refuses with "not possible to fast-forward," that's fine — it just means local `main` diverged; tell them and don't force it.)
- If `WORKTREE_CLEAN=false` (uncommitted work), the checkout is shared, or preservation of the branch's work is not verified: **do NOT switch branches, pull, merge or stash.** Name the observed reason and any unknown comparison; do not label unknown publication status as unpushed work. Offer (a) verify only the missing preservation or upstream fact, or finish and run `/wrap-up`, or (b) leave this checkout exactly as it is and start from a separate checkout. A stash only if they ask for it and understand that it hides their work until they bring it back. **Never discard.**
- **If any pull/merge reports a CONFLICT** (`CONFLICT`, `<<<<<<<`, "fix conflicts and then commit"): stop and run **`/resolve-conflict`** — do not try to fix it by hand or with `git reset`. Reassure them it's normal and nothing is lost.

## Step 5 - Make today's branch
Ask: **"In a few words, what are you working on today?"**
Create a clearly-named branch `‹operator›/‹short-topic›-‹YYYY-MM-DD›` (lowercase, hyphens), e.g. `alex/welcome-emails-2026-06-18`:
```bash
git checkout -b <operator>/<topic>-<date>
```

## Step 6 - Pin down the work (adaptive - don't over-interrogate)
Ask **"what"** first. Then scale the questions to the size of the task:
- **Small / obvious task** (a typo, a copy tweak, one file): just confirm the *what* and the *definition of done* in one line, and move on. Don't make them answer 7 questions to fix a typo.
- **Real / multi-step task**: get short answers to the full set and reflect them back:
  1. **What** are you working on?
  2. **Why** does it matter — which bucket: **Acquisition / Client Success / Operations**?
  3. **Definition of done** — what does finished look like?
  4. **What files/areas** will you likely touch?
  5. **What must you NOT touch?** (anything owned in `CODEOWNERS` — governance, migrations, other clients' folders)
  6. **Smallest useful deliverable** — the first shippable slice?
  7. **When do you stop and ask?** (blocked > ~30 min, or about to touch the "don't touch" list)

## Step 7 - Orient the brain
If a `/context_load` skill exists (template repos), run it to load the foundational docs. Otherwise read `CLAUDE.md` and surface anything in-flight. Now they're git-safe **and** brain-oriented.

## Step 8 - Hand them a Slack-ready "starting" line
> 🔧 Starting: ‹topic› (‹bucket›). Branch `‹branch›`. Done = ‹definition›. — ‹operator›

## Always
- Never edit `main` directly. Never force-push, hard-reset, or delete branches.
- If anything is destructive or unclear, **STOP and ask.**
- Reassure accurately: *"Branches and review protect the official version. Work that exists only on this computer is protected only once it's saved and pushed, and I won't move or delete anything without telling you first."*

## Boundaries

| Ask | Skill |
|---|---|
| "I'm done for today", "save my work", "wrap up" | `/wrap-up` |
| "Fix this merge conflict" | `/resolve-conflict` |
| "Archive, retire or delete this project or folder" | Not this skill. Closing a project needs its own decision about what is kept and who can still reach it; route it to the repo owner. |
| "Work out where I stand in this repo" | This skill, Steps 0 to 2: it reads and reports, and changes nothing. |

## Definition of done

- [ ] **D-1 - Local work and verified or unknown publication facts are distinguished.**
  - **Example:** "Your branch is ahead of recorded main by 1 but matches its last-fetched upstream. Two files have uncommitted edits; I have not checked backups elsewhere."
  - **Counter-example:** Calling `AHEAD_MAIN` an unpushed count, or treating missing upstream as zero unpushed commits.
- [ ] **D-2 - Nothing was moved, deleted or published without being said.**
  - **Example:** The checkout had unsaved edits, so the sync was skipped and the reason was given.
  - **Counter-example:** Running `git pull` or `git stash` in a dirty checkout "to make it current".
- [ ] **D-3 - The operator and the branch are named.**
  - **Example:** "Hi Alex. You're on `alex/welcome-emails-2026-06-18`, which is your own branch."
  - **Counter-example:** Starting work on `main`, or greeting by the operator file without checking it against `GH_USER`.
- [ ] **D-4 - "Done" is written down before work starts.**
  - **Example:** A one-line definition of done for a small task; the full seven answers for a real one.
  - **Counter-example:** Seven questions for a typo fix, or none for a multi-step task.

## QC gate

Check D-1 to D-4 before you tell the operator to start. If a step could lose or hide their work, stop and hand the choice to them, or to the repo owner when they cannot decide. A checklist item you could not verify is reported as unverified, not as passed.

No approved gold standard yet.
