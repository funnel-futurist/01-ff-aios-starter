# Your AIOS

This is **your AI operating system**, your business's second brain. You own it and you shape it. This file (`CLAUDE.md`) is your constitution: it loads into every message, so keep it lean and make it yours.

## Start here (first run)
Run **`/onboard_wizard`**, it walks you through setup (your tool, this repo, your keys, inviting your team), captures your vision / mission / values, and gets you operating. A new teammate joining later runs it too.

## This file is yours to shape
Edit this `CLAUDE.md` freely as your business and workflow evolve, it's your brain, not a cage. Put your identity, your priorities, and a map to where things live. Keep it **lean** (a map, not a manual, detail belongs in your folders and skills). The only thing we ask: follow the best practices below.

## Best practices (the guardrails)
- **Secrets stay out of the repo.** Keys live in `.env` (it's gitignored, so it never reaches GitHub). Set a spend limit on each key; turn on 2FA. (Airlocks: scope access, contain the blast radius.)
- **Reversible by default.** Commit early and often, git is your safety net. Don't delete important work or force-push.
- **The PR reviewer has your back.** `.claude/skills/pr_review` reviews every PR, approves good work, flags real risk, and suggests the exact fix for safe issues (in CI it can't change your branch; run `/pr_review` yourself to have it apply them). It never blocks you.
- **When you're stuck, use the unstuck protocol** (`docs/UNSTUCK_PROTOCOL.md`): Claude in caveman mode → screenshot + AI → YouTube (last 1–2 months) → NotebookLM → escalate. You'll solve ~99% yourself.
- **Lean beats bloated.** Add the high-impact core; look the specifics up as you go.

## Work that reaches use
How work runs in this AIOS, for you and your agents. "The owner" means whoever owns this workspace.
- **Every unit states:** the outcome, the owner and reviewer, the risk tier, the sensitivity tier, an estimate in agent minutes (human minutes listed separately), what it needs from the owner, the exact file or resource it locks, what it blocks, and an acceptance check. A missing field holds that one unit only.
- **Ask first.** Before work starts, list every key, login and decision it needs in one batch, each with what it unblocks. Keep going on everything else.
- **One claim per action.** One agent claims each action and does it once, so nothing runs twice. An approval is not proof it ran.
- **Lock files, not areas.** A lock covers the exact files or resources being changed, never a whole folder.
- **Review by consequence.** Docs pass on automated checks. Code with no production effect gets one reviewer. Production databases, deletions, money and credentials go to the owner in one batch. Paid AI review runs only if the owner chooses it.
- **Investigations** state the expected result and a stop condition. They end in a fix, a handoff to the owner, one bounded next test, or "evidence exhausted". No polling and no "still working" posts.
- **Report four states separately:** source complete, installed, deployed, accepted in use. Using it day to day counts as accepted.
- **Sensitivity follows the data.** Personal goals and tasks are low. Company plans and team records are medium. Customer personal data, payments and credentials are high and get the full review.

## Your workspace
Seven domain folders, the same in every company's instance (`00_AIOS/routing.md` says which one takes which request):
`00_AIOS/` who we are (`company/` holds your Foundational 6), routing, decisions and the review queue · `01_Creation/` brand, the one asset library, preferences, finished outputs · `02_Team_Ops/` people, roles, projects, onboarding, routines · `03_RevOps/` site, funnels, CRM, automations, sales, customer journey, audits, reports, records · `04_Attention/` content, campaigns, publishing, accounts, performance · `05_Jobs/` recurring jobs · `99_Archive/`.
Setup is in `SETUP.md`. File naming: lowercase, underscores, no spaces (`taxonomy_rules.md`).

## Your skills
Type `/` to see them. What each one does: `.claude/skills/README.md`. Run `/start` any time to see the moves for your role.
- **Start and end every session:** start · start-my-day · wrap-up · context_load · dashboard
- **Setup and staying current:** onboard_wizard (run it first) · upskill · env_keys (your keys and your one core `.env`)
- **Think before you build:** grill_me · project_management
- **Your foundations and quality:** f6_completeness_check · qc_review · humanize
- **Keep the workspace healthy:** workspace_health · file_audit · security_check · changelog
- **Working as a team:** review-queue · resolve-conflict · pr_review (your guardian, runs on every change)
- **Money:** financial_teardown
- **Sounds (Mac):** pause · play (quiet or restore the finished / needs-you sounds for Claude and Codex)
- **Documents:** Word, PDF, PowerPoint and Excel come from Anthropic's `document-skills` plugin, which `/onboard_wizard` installs. They are Anthropic's, not copied here (`THIRD_PARTY_NOTICES.md`).

Add your own (see `docs/UNSTUCK_PROTOCOL.md` and the skills folder for how). Never run skills from sources you don't trust.

@.aios/operator_core/OPERATOR_CORE.md
@00_AIOS/routing.md
