# Download a backup of a Supabase database

**What it's for:** a copy of your database's roles, structure and data, saved on your own computer, before a risky change or on a schedule. About 15 minutes the first time.

**Why not a dashboard button:** Supabase's docs say "Dashboard backups are only available for older projects that still use logical backups." The command-line tool is the route Supabase documents for taking your own copy. Daily backups on Pro, Team and Enterprise plans can be *restored* from **Database > Backups**, but that isn't a copy you hold.

**You need:**
- **Docker Desktop**, installed and running: https://www.docker.com/products/docker-desktop/ (a Docker-compatible runtime such as OrbStack also works).
- **The Supabase CLI.** On a Mac, run `brew install supabase/tap/supabase`. Other systems: https://supabase.com/docs/guides/local-development/cli/getting-started
- **The database password** for the project.
- **A folder outside every Git repository**, so the backup can never be committed.

No access token is needed: these commands connect with the database password.

## Steps
1. Open the project at https://supabase.com/dashboard and click **Connect**. Copy the **Session pooler** connection string. (Use the direct one only if your network supports IPv6 or the project has the IPv4 add-on.) Put your database password where it says `[YOUR-PASSWORD]`. Supabase requires the string to be percent-encoded, so a password with special characters must be encoded.
2. Open Terminal (see `run_a_terminal_command_from_claude.md`), and go to your backup folder: `cd ~/Documents/supabase-backups` (create it first if it doesn't exist).
3. Type `read -s DBURL` and press **Enter**. Paste the connection string and press **Enter** again. Nothing shows on screen, and the password stays out of your command history.
4. Run these three commands exactly as written:
   ```sh
   supabase db dump --db-url "$DBURL" -f roles.sql --role-only
   supabase db dump --db-url "$DBURL" -f schema.sql
   supabase db dump --db-url "$DBURL" -f data.sql --use-copy --data-only -x "storage.buckets_vectors" -x "storage.vector_indexes"
   ```
5. Close Terminal.

## It worked when
The folder holds `roles.sql`, `schema.sql` and `data.sql`, and `data.sql` isn't empty (unless the database really is).

## Send back
"Backup of `<project name>` taken `<date>`: roles, schema and data, stored at `<where>`". Never the connection string, the password or the files themselves.

## If it goes wrong
- An error about the Docker daemon: open Docker Desktop, wait until it says it's running, and try again.
- An authentication error: the password in the connection string is wrong, or it has special characters that aren't percent-encoded. The project owner can reset the password on the **Database > Settings** page.

## Video and checks
- **Video: still to find.** The 2026-10-01 candidates showed the old dashboard download, which most projects no longer have, so none matches these steps. The steps stand on the official docs until a checked video is added.
- **Steps checked against:**
  - Supabase Docs, "Backup and Restore using the CLI" (https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore), the source of the three commands;
  - "Restore Dashboard backup" (https://supabase.com/docs/guides/platform/migrating-within-supabase/dashboard-restore), the source of the quote above;
  - "Database Backups" (https://supabase.com/docs/guides/platform/backups);
  - "supabase db dump" (https://supabase.com/docs/reference/cli/supabase-db-dump).

  All read 2026-10-14.
- **Our own additions, not Supabase's:** step 3's `read -s` (it keeps the password out of the command history, so the commands use `"$DBURL"` where the docs write `[CONNECTION_STRING]`), the folder rule, and the wording of the two errors.
