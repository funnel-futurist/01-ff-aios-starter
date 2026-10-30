# Security

Your AIOS holds the keys to your business. Treat it that way. This is the short version of how the template keeps you safe and what to do if something goes wrong.

## How the template protects you
- **Claude Code is told not to read your secrets, but that is a guard rail, not a wall.** `.claude/settings.json` denies reads of `.env*`, `*.pem`, `*.key` and credential files. Claude Code applies those rules to its own file tools and to shell commands that name the file, such as `cat .env`. They don't stop a command that reads files without naming them (a search across a whole folder, say) or a script that opens files itself. So: never ask Claude to show, print or search your keys; keep production keys in a password manager rather than in the workspace; turn on Claude Code's sandbox if you need the operating system to block every read (Claude Code docs, "Configure permissions", checked 2026-10-14); and if a key does appear in a conversation, treat it as leaked (below).
- **Secrets never reach GitHub.** `.gitignore` ignores `.env` (and `node_modules/`, logs, etc.), so they can't be committed by accident.
- **Destructive commands are blocked by default.** `settings.json` denies `rm -rf`, force-push, `git reset --hard`, `git clean -f`, and `sudo`. You can loosen this once you know what you're doing, but the floor is "hard to wreck."
- **The PR reviewer is a second set of eyes.** Every pull request gets scanned for leaked secrets or env files, destructive or security-weakening SQL, file names with spaces, or a broken symlink under `.claude/` before it merges. Those, an error-level finding from the AI review when one is set up, or a scan that did not finish, fail the pull request's `pr-gate` status; whether that stops the merge depends on your branch protection. Everything else it says is advice.

## Your part (the guardrails)
- Keys live in `.env` or a password manager. Nowhere else. Not Slack, not email, not a chat message, not a Google Doc.
- Put a **spend limit** on every API key and give each one a **specific name** so you can revoke one without touching the others.
- Turn on **2FA** on GitHub and on your Anthropic Console account.
- Keep your repo **private**.
- **Never run a skill from a source you don't trust.** A skill runs with your access. Read it first.

## If a key leaks (act in this order)
1. **Revoke it immediately** in the platform that issued it (Anthropic Console, Google Cloud, etc.).
2. **Generate a replacement**, put it in `.env`, and confirm `.env` is still gitignored (`git status` should not list it).
3. **Tell your team in the open** (don't hide it). Anyone sharing the repo needs to stop using the dead key.
4. **Scrub the history if it was committed.** If the key ever landed in a tracked file and got pushed, the value lives in git history forever (even after you delete the file), and bots scrape repos within minutes. Rotation in step 1 is what actually protects you, so treat the old value as burned. To also clean history: ask Claude Code to scrub it (`git filter-repo` or BFG), or for a brand-new repo just delete it and re-create from the template.

## Reporting a problem in the template itself
Found a flaw in this template (a weak default, a missing guardrail)? Tell whoever gave you the template, or open a private issue on the upstream repo. Don't post secrets or live keys in an issue.
