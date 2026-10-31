---
name: wrap-up
description: The safe end-of-session closeout + handoff ritual. Use when finishing work, ending the day/session, or when the user says "wrap up", "wrap-up", "end my day", "close out", "I'm done", "save my work", or asks how to safely commit/push/PR and update the team. Preserves local work first, runs a self-review before anything is published (auto-fixing only safe issues), commits only the paths you intend, and, when you say so, pushes your own branch, opens or updates the PR and writes a plain-English team update. NOT for starting a session (use /start-my-day) and NOT for retiring, archiving or deleting a project or bulk-publishing everything, which each need their own decision. Pairs with /start-my-day.
---

# /wrap-up - the safe closeout + handoff

Calm, plain-English, one step at a time. Protect the operator's work **and** the team's time.

## Step 0 - Read the situation
```bash
bash scripts/team/git-safety-check.sh
```
If `ON_MAIN=true`: **STOP.** We never commit on `main`. Help them move their changes onto a branch first (`git checkout -b <operator>/<topic>-<date>` carries the uncommitted changes along), then continue.
If `GH_USER=unknown`: GitHub isn't connected — the push/PR steps will fail. Do Steps 1–4 (so their work is at least committed locally and safe), then hand the fix before Step 5: *"run `gh auth login` (GitHub.com → HTTPS → browser), then we'll push."*

## Step 1 - See what changed
```bash
git status
git diff --stat
```
Summarize, in plain English, what they actually changed.

Then name what exists only on this computer: saved commits that aren't pushed (`git log @{u}..` when the branch tracks one), edited files not yet saved, ignored originals, drafts and nested repositories. If they worked in more than one folder or have nested repositories, run the bundled read-only helper and name each folder (it never fetches, switches, stashes, cleans or deletes; details in `.claude/skills/start-my-day/references/reconciliation.md`):
```bash
python3 .claude/skills/start-my-day/scripts/reconcile_local.py --root /absolute/path/to/a/work/folder --out-dir /absolute/path/to/a/private/folder/outside/any/repo
```

## Step 2 - Keep the junk out of the commit (don't delete work you didn't make)
Flag anything that shouldn't be committed: logs, `__pycache__`, `.DS_Store`, build artifacts, scratch files - and **anything that looks like a secret** (keys, tokens, connection strings, `.env`). Leave those out of the commit. Remove only generated junk made in this session, and only after they agree. A name like `scratch` or `old` is not evidence a file can be deleted, and ignored originals, drafts, other people's edits and nested repositories stay exactly as they are.
**If you spot a likely secret, STOP and walk them through removing it — don't just warn:**
1. Take it out of the file (replace with a placeholder or move it to `.env`, which is git-ignored).
2. If the secret's file should never be tracked, add it to `.gitignore`.
3. If it was already **committed earlier** on this branch, tell them plainly the key must be **rotated/regenerated** (treat it as exposed), and ask a senior person for help — don't attempt history rewrites yourself.
4. Re-run `/wrap-up` once it's clean. Do not commit until the secret is gone.

## Step 3 - 🔒 Self-review (always run it, act as a world-class engineer / GitHub reviewer)
Run this every time — it's how you ship clean work. (Honest about what it is: a strong built-in habit, not a hard technical gate — if your repo has an AI PR reviewer or a maintainer, that's the real gate. Review against the same bar they'll use so nothing you pass here gets bounced there.) Review the full diff like a senior reviewer would, then:
- **Auto-fix ONLY the safe set** (apply directly): formatting, lint, obvious typos, removing generated junk, small consistency fixes.
- **NEVER auto-change the judgment set — surface it for the operator's approval instead:** strategy/docs content, offer logic, client-facing claims, large deletions, and anything governance — `.github/`, `CODEOWNERS`, `.claude/hooks`, `.claude/settings.json`, workflows, migrations, `.env`/secrets. *(If a human owns it in `CODEOWNERS`, you do not silently change it.)*
- Sanity-check against your repo's standards: `CLAUDE.md` and any naming / voice / framework guides it points to.
- **Documentation check:** if this change adds or edits a skill, hook, or process step, confirm it's documented where people will actually find it — the skill's own description, `README`/`CONTRIBUTING`, and (if it changes how the team works) the onboarding wizard. If it isn't, add it before opening the PR. *A new step nobody knows about doesn't exist.*
Tell the operator what you fixed and what needs their call. **Goal: the PR is already best-practice before it ever goes to review.**

## Step 4 - One clean commit (you write the message, not them)
**Don't make a non-technical operator format a commit message.** Ask in plain English what they did, then YOU write the conventional message — `type(scope): what changed and why` (e.g. `docs(offer): tighten the guarantee section`). Show it, get a nod.
```bash
git add <intended paths>
git commit -m "<message you wrote>"
```

## Step 5 - Push YOUR branch (never main)
A saved commit is safe from a mistake but only a push shares it, so ask: *"Want me to push this branch so the team can see it?"* Push only your own branch, and only when they say so or their standing instructions do. Never push everything as a backup, and never to `main`.
```bash
git push -u origin HEAD
```
(If your repo protects `main`, a direct push is rejected. You only ever push your own branch.)
If the push is **rejected because the branch is behind**, don't force it - in your own clean checkout bring the latest in first (`git merge origin/main`), and if that conflicts, run **`/resolve-conflict`**, then push again.

## Step 6 - Open or update the PR (fill the template, don't skip it)
Before you publish, check the base branch and any open PR touching the same files, and look at what the repo's PR workflow will run. If a paid or external step could run and you can't tell, keep the branch local and ask.
- No PR yet → create one and **populate the PR template** (don't rely on `--fill`, which only copies the commit and skips the checklist / AI-disclosure). Write the body to match `.github/pull_request_template.md`, then:
  ```bash
  gh pr create --base main --title "<type(scope): summary>" --body-file <(printf '%s' "<filled template body>")
  ```
- PR already exists → it updates automatically on push.
Share the PR URL. If your repo has the AI PR reviewer, it checks the PR automatically; otherwise a maintainer reviews it. Anything touching an owned / governance path waits for a code-owner (**[PRIMARY_REVIEWER]**).

## Step 7 - Plain-English team update (protect everyone's time)
Run the **`/changelog`** skill (or use its plain-English style) to produce a closeout a founder can read in 10 seconds — no jargon, no file paths unless needed:
```
✅ ‹Operator› — end of session
Completed: ‹plain English›
In progress: ‹plain English›
Blocked / needs review: ‹or "none"›
PR: ‹url›
Next step: ‹one line›
```

## Step 8 - Catch invisible work
If `git status` still shows uncommitted or unpushed changes, say so plainly: *"You still have work that exists only on this laptop. Want me to save it and push it so it's safe and the team can see it?"* Offer; don't do it unasked. Put the local-only work, any unpushed commits and the exact next step in the handoff. **Don't end the session with work stranded or moved without telling them.**

## Always
- Never force-push, hard-reset, or delete branches. Never commit secrets. Never bulk-stage, stash, clean or overwrite work you didn't make.
- If a fix is a judgment call, **ask** — don't decide for them.

## Boundaries

| Ask | Skill |
|---|---|
| "Start my day", "where do I stand" | `/start-my-day` |
| "Fix this merge conflict" | `/resolve-conflict` |
| "Write the team update" | `/changelog` |
| "Archive, retire or delete this project", or "push everything as a backup" | Not this skill. Each needs its own decision about what is kept and who can still reach it; route it to the repo owner. |

## Definition of done

- [ ] **D-1 - Local work is preserved and named.**
  - **Example:** The handoff lists "2 unpushed commits and 1 untracked draft in `notes/`" by name.
  - **Counter-example:** Deleting "scratch" files to tidy up, or pushing every discovered file as a backup.
- [ ] **D-2 - No secret is committed.**
  - **Example:** A token found in a file is replaced with a placeholder, the file is ignored, and a key that was already committed is flagged for rotation.
  - **Counter-example:** Warning about a key and committing it anyway.
- [ ] **D-3 - One clean commit of only the intended paths, with a message written for them.**
  - **Example:** Adding only the one file you changed, by name, then writing `docs(offer): tighten the guarantee section`.
  - **Counter-example:** `git add -A`, which commits logs and scratch files.
- [ ] **D-4 - Publishing matches what was said.**
  - **Example:** The branch was pushed after a yes, to the operator's own branch, with the PR template filled in.
  - **Counter-example:** A push to `main`, or a push nobody asked for.
- [ ] **D-5 - The next step is written down.**
  - **Example:** "Next step: review comment on the pricing page, then re-run the check."
  - **Counter-example:** A handoff that says only "done for today".

## QC gate

Check D-1 to D-5 before you say the session is wrapped. If a likely secret is found, stop and hand it to the repo owner for rotation advice. If any step could lose or hide work, hand the choice to the operator. Report an unverified item as unverified.

No approved gold standard yet.
