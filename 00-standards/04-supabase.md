# Supabase standard

Use a separate `SCHEMAS.md` beside a repo's Supabase source. For each connected project, name the project and environment, explain every team-owned schema, and distinguish template tables from custom tables. Verify the live project identity before writing the map; a project display name is not proof of what an app uses.

Leave provider schemas such as `auth`, `storage`, `realtime`, `graphql`, `vault`, `extensions`, `pgbouncer` and `supabase_migrations` alone. Schema names do not get numbers. New custom tables use an `x_` prefix in a team-owned schema. Do not rename existing tables to retrofit this rule or alter template tables for a custom feature.

Database policy changes need a tested staging migration, backup and production readback. Do not assume that a six-table warning or a similarly named staging project identifies the production target. The October 22 portal/database row in the source brief is superseded by the verified C54 writer-map correction: target identification and caller behavior must be checked before any RLS proposal. This document performs no database change.
