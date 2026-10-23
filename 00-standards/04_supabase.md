# Supabase standard

Use a separate `SCHEMAS.md` beside a repo's Supabase source. For each connected project, name the project and environment, explain every team-owned schema, and distinguish template tables from custom tables. Verify the live project identity before writing the map; a project display name is not proof of what an app uses.

Leave provider schemas such as `auth`, `storage`, `realtime`, `graphql`, `vault`, `extensions`, `pgbouncer` and `supabase_migrations` alone. Schema names do not get numbers. New custom tables use an `x_` prefix in a team-owned schema. Do not rename existing tables to retrofit this rule or alter template tables for a custom feature.

Before a database policy change, verify the target project and every caller that reads or writes the affected tables. Test the migration against an approved staging target, verify a usable backup, then read back the production result after an authorized apply. A similar project name is not proof of the target. This document performs no database change.
