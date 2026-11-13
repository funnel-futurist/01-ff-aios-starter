# Supabase and GitHub: the FF standard

**Applies to:** every FF or client app that keeps its database changes in `supabase/migrations/`.
**Decided by:** Phoenix, 2026-11-13. He connected Command OS this way first.
**Status:** evergreen. Canonical copy: 01-ff-aios `docs/standards/SUPABASE_GITHUB.md`. This Starter copy follows it; if they differ, the 01-ff-aios copy wins.

## Why

Every pull request (PR, a proposed change) that touches the database gets its own preview database (a temporary copy built from the repo's files).
That catches a broken migration (a database change file) before anyone approves it.
Live database changes stay a human-approved step.

## Step 1: run the replay check first

A preview database is built from empty, applying `supabase/migrations/` in filename order.
So check that the repo's migrations replay from empty before connecting.

- Start a fresh local database.
- Apply every file in `supabase/migrations/` in order.
- Stop at the first error.

Command OS has the runner: `scripts/supabase-replay/replay.sh` in 06-ff-command-os.
It stubs what hosted Supabase provides: its roles, `auth`, `storage` and pgvector.
Copy it into the new repo if it has none.

If the replay fails, squash to a baseline first:
- take a schema-only dump of production (the owner's go is needed);
- make it one baseline migration;
- archive the old files;
- run `supabase migration repair`.

## Step 2: connect GitHub in Supabase

Supabase, then the project, then Settings, Integrations, GitHub.

| Setting | Value | Why |
|---|---|---|
| GitHub repository | the app's repo | |
| Working directory | `.` (the repo root, the folder that contains `supabase/`) | Supabase adds `supabase/` itself. Setting `supabase` makes it look in `supabase/supabase` and skip every PR. |
| Deploy to production | **OFF** | Live database changes stay a human-approved step. |
| Production branch name | blank | Only used when deploy is on. |
| Automatic branching | **ON** | Every PR gets a preview database. |
| Branch limit | **3** | Caps how many preview databases exist at once. |
| Supabase changes only | **ON** | Only PRs that touch `supabase/` get one, which saves cost. |

**Skip:**
- The Vercel integration. It copies keys into Vercel projects automatically and fights deliberate key management.
- AWS PrivateLink. It needs the Team plan and isn't needed.

## Step 3: watch the cost

- Preview databases bill per hour while they exist.
- The org Spend Cap does not cover them.
- A preview database stops billing when its PR closes.
- Check Usage once a month.

## Step 4: add the replay check to CI

CI (the automatic checks on every PR) should run the replay on any PR that touches `supabase/`.
Command OS does this in `.github/workflows/supabase-replay.yml`.
It catches an ordering mistake before the preview database does.

## Where this is used

- Command OS (06-ff-command-os): connected 2026-11-13. The setup steps are in `docs/install/SUPABASE_GITHUB.md`.
- The Portal's Command OS training adds a lesson from this file (Portal lane).
- Supabase basics for this Starter: `00-standards/04_supabase.md`.
