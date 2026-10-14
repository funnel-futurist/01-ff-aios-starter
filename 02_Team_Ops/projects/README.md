# Projects

One folder per project, and each starts with its written plan: `PROJECT.md`. Copy `_template/` to start one.

`PROJECT.md` holds the meaning (the outcome, scope, decisions, acceptance, evidence). Your task tool (ClickUp or similar) holds the live tasks and links back here. When something changes in a meeting, update `PROJECT.md` first, then the tasks.

A website or app isn't a project folder: it lives in `03_RevOps/site/`, or in its own repository once it outgrows that.

**Upgraded from Starter 2.x?** Your old `11_Projects/` folders moved here unchanged, byte for byte. If one is a deployed site, the upgrade moved it only after Vercel confirmed its project builds `02_Team_Ops/projects/<site>` (card: `docs/human_steps/move_a_vercel_site.md`). It can stay here, or move to `03_RevOps/site/` later: change Vercel's **Root Directory** in the same sitting as the move.
