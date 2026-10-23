# Repository standards pilot

These rules make a repository understandable to its owner before anyone edits it. Start with the [core four](01_core_four.md), then use the [README checklist](02_readme_standard.md) and [folder rules](03_folder_structure.md). [Supabase](04_supabase.md) and [Vercel](05_vercel.md) apply only when a repo uses those services. Copy the [new-repo template](template/README.md) when creating a repo.

This is a **pilot**, not an automatic rename of existing repos or client workspaces. The October 22 direction calls for a copy-brain pilot, then one approved Keep repo at a time. Existing Starter 3.0 folders and its `taxonomy_rules.md` still govern installed client instances until a reviewed migration changes them. The proposed `NN-scope-name` convention for repo and service names conflicts with that current underscore-based client taxonomy; do not silently rename those paths. Do not rename, archive, delete or change connected projects from this document alone.

| Conflict | Rule for this pilot | Installed instances |
| --- | --- | --- |
| Separators | New repo and service names use hyphens; new browsable folders use hyphens; files follow `taxonomy_rules.md` and use underscores. | Existing paths keep their install contract. |
| Starter taxonomy says not to add a top-level folder | Phoenix's October 22 standards pilot authorizes `00-standards/` in this source repository. | This source-only folder is excluded from client packages. |
| Which rules win after installation | Phoenix's accepted direction governs this pilot in its source repository. | The installed Starter taxonomy and the client's own instructions govern until a separately reviewed client release changes them. |

The GitHub check validates the template and newly added top-level browsable folders. It does not retroactively fail this repository's existing README or framework folders. Expand enforcement after the pilot and a compatible migration plan.
