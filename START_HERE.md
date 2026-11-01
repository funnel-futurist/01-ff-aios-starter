# START HERE — working in your AIOS (read once, ~3 minutes)

Welcome. This repo is your **AI Operating System**, your second brain. This page is everything you need to work in it safely. Branches and review protect the official version, and work that exists only on your computer is protected only once it is saved and pushed.

## The one picture you need: separate timelines
- **`main`** = the *one official timeline* you trust.
- A **branch** = a *private side-timeline*. You work here so you can never break the official one.
- **pull** = copy the latest official changes into yours (so you're never working from an old copy).
- **commit** = save a checkpoint of your work.
- **push** = upload your branch so it's safe and your team can see it.
- **PR (pull request)** = *"please add my side-timeline to the official one"* — where it gets reviewed.

**The rule that matters most:** *check where your work stands before you move anything, and push your own branch once you say it is ready.* Two commands walk you through it.

## The two commands (this is the whole routine)
| When | Command | What it does |
|---|---|---|
| First time in this workspace, or "what am I allowed to do here?" | **`/start`** | Tells you who you are, what your role may do, which release is installed, and whether it still matches. |
| Start of a work session | **`/start-my-day`** | Reads where your work stands first, including work that exists only on this computer. Then it figures out who you are, brings the latest official version in only when that is safe, puts you on your own branch, helps you decide what "done" looks like, and loads your brain (`/context_load`). It never switches, stashes or deletes anything in work you have not saved. |
| End of a work session | **`/wrap-up`** | Reviews your work like a senior engineer, saves it, and, when you say so, pushes your branch, opens your review request and writes a plain-English update for your team. It never deletes your files or pushes everything as a backup. |

That's it. Open the repo in Claude Code → type **`/start-my-day`** when you begin → **`/wrap-up`** when you're done.

## What happens automatically (you do nothing)
- When you open the repo, you get a friendly nudge **if** you're on `main` or behind the latest — telling you to run `/start-my-day`.
- Genuinely dangerous git commands (that could delete unsaved work) pause and ask you first. That check needs Node.js; `/start` warns you if it's missing, and a warning isn't protection.

## Where things go
Seven domain folders, the same in every company's instance: `00_AIOS` (who you are, routing, decisions, the review queue), `01_Creation`, `02_Team_Ops`, `03_RevOps`, `04_Attention`, `05_Jobs`, `99_Archive`. `00_AIOS/routing.md` says which one takes which request. Setting this workspace up, or adding a tool to it: **[SETUP.md](SETUP.md)**.

## If you get stuck or confused
- Tell Claude: *"treat me like a caveman, explain like I'm 5, give me every click."*
- **Saw scary `<<<<<<<` symbols after syncing?** That's a merge conflict — normal, nothing's lost. Run **`/resolve-conflict`**.
- Read **[CONTRIBUTING.md](CONTRIBUTING.md)** for the "what do I do when…" answers.
- New here? Run **`/onboard_wizard`** for the full guided first-time setup.
- When in doubt, run `/wrap-up` and ask. Nothing on your own branch can hurt the official version.
