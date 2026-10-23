# The core four

Every FF system has a clear home: **GitHub** holds code and docs; **Vercel** hosts sites and apps; **Supabase** stores data; **Typeform** holds forms and certification exams. A system uses only the tools it actually needs. Make.com and GHL integrations remain separate.

For new FF-owned repos and matching service projects, use one shared number and `NN-scope-name` in lowercase hyphenated form wherever the tool permits. Example: `06-ff-command-os` in GitHub, Vercel and Supabase. Intelligence/instance pairs may use `02a`/`02b`. The number identifies the system across tools; it is not a substitute for a README or a live inventory.

| Prefix | Use |
| --- | --- |
| `00` | Standards and templates |
| `01`–`09` | Core FF systems |
| `10`–`29` | FF products, sites and shared sources |
| `30`–`49` | A named teammate's working projects |
| `50`–`69` | Client projects, with their own scope |
| `90-parked-*` | Kept, unmaintained repositories |
| `98-test-*` | Tests and experiments |
| `99-archive-*` | Scanned, read-only repositories |

Use `ff` only for FF-owned work. A client system uses its own invented client scope, such as `50-example-site`. Never put “slop” in a name. Rename before archiving, after checking links and integrations. Vercel projects are deleted only from a separately approved exact batch; Supabase projects are held or paused only after an approved review. None of these actions follows merely from a prefix.

**Typeform exception:** number the workspace, such as `06-example-system`; keep the respondent-facing form title plain and versioned, such as `System Basics (v1.1)`. Any cleanup marker is a review aid, not permission to delete a form.
