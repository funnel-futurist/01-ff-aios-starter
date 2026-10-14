# 0001 · The instance layout is seven domain folders (Starter 3.0)

**Scope:** operator. **Status:** accepted 2026-10-01 (estate plan §3.2, founder ruling C1). **Superseded by:** none.

## Problem
Starter 2.x had numbered folders (`01_Foundations` ... `11_Projects`) named after kinds of document. The business runs as AIOS, with Creation, Team Ops, RevOps and Attention under it, and the 2.x folders didn't show that. Every company's instance also had to look the same, Funnel Futurist's own included, so that one way of working carries across.

## Options
1. Keep 2.x and add a map document.
2. Rename the folders in place.
3. Move to domain folders, with an upgrade that moves every file.

## Decision
Option 3:
- the folders are `00_AIOS`, `01_Creation`, `02_Team_Ops`, `03_RevOps`, `04_Attention`, `05_Jobs` and `99_Archive`;
- `release/package_spec.json` declares the 2.x-to-3.0 map;
- the map ships inside the release record, so it's approved with the release.

## Why
The folders now say which part of the business owns what, and `00_AIOS/routing.md` turns that into a rule. A declared map, checked before any file moves, means an upgrade can't overwrite anything or strand a file.

## Consequences
- `upgrade` moves the person's files, including ones they made themselves.
- `rollback` reverses the moves.
- References to old folders inside the person's own files are reported, never rewritten.
- `07_Setup/` (three walkthroughs written for "Use this template" and Claude Code on the web) retires. `SETUP.md` and `docs/human_steps/` replace it; anything a person had added to `07_Setup/` moves to `99_Archive/07_Setup/`.
- Three 2.x deliverable folders (`ads`, `emails`, `webinars`) keep their names under `04_Attention/campaigns/`, so files can't collide.
- `11_Projects/` moves to `02_Team_Ops/projects/` as ruled. A new site lives in `03_RevOps/site/`; a site moved by the upgrade stays where it lands until the client chooses to move it.
- `REPO_CONTEXT.md` is at the root, and the decision notes are in `docs/decisions/`. §3.2 doesn't list either at the root, and R22 forbids new top-level folders; the repo contract (B11) requires both. This placement is proposed for the registry, not assumed.

## Amendment, 2026-10-14: the rebuild on 2.10.0
The 3.0 work above was rebuilt from 2.10.0 after a founder chose one repository with phase folders. Verifying the first build found that it could lose client files, so these rules replace its upgrade behaviour:
- **Paths change, bytes never do.** Each file is hard-linked to its new path, then the old name is removed. Nothing is copied, merged or rewritten.
- **No refresh.** The first build gave unedited starter files the 3.0 text. It decided "unedited" from hashes that an earlier upgrade had already reset to the client's own bytes, so it would have overwritten edits. Starter files are seeds: written once, never again.
- **Refused, with nothing changed:**
  - any existing destination, including one that differs only by case or Unicode form;
  - two files landing on one name;
  - a symbolic link, a nested repository or submodule, or another disk.
  
  (The first build deleted the source whenever the destination existed.)
- **Planned and journaled before the first move,** so a hard kill at any point is recoverable. Every moved file is re-hashed afterwards.
- **Junk files** (`.DS_Store`, `Thumbs.db`, `desktop.ini`) are set aside in the backup, not moved. Empty folders move too.
- **`02_Deliverables/copy/` gets its own subfolder** (`01_Creation/outputs/copy/`), so it can't collide with the rest of `02_Deliverables/`. **`10_Departments/` moves to `02_Team_Ops/departments/`.**
- **Founder requirements:**
  - **Website folders:** the upgrade refuses until every affected Vercel Root Directory is corrected and verified with Vercel.
  - **`CLAUDE.md`:** the client's file keeps every byte except one declared line, `@00_AIOS/routing.md`. The dry run shows it, it's never duplicated, and rollback takes it back exactly.
  - **Founder review:** `instance check` fails visibly until founder review is restored at the new paths and GitHub enforces it.
