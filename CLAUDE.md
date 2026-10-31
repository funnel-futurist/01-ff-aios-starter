# Your AIOS

This is **your AI operating system**, your business's second brain. You own it and you shape it. This file (`CLAUDE.md`) is your constitution: it loads into every message, so keep it lean and make it yours.

## Start here (first run)
Run **`/onboard_wizard`**, it walks you through setup (your tool, this repo, your keys, inviting your team), captures your vision / mission / values, and gets you operating. A new teammate joining later runs it too.

## This file is yours to shape
Edit this `CLAUDE.md` freely as your business and workflow evolve, it's your brain, not a cage. Put your identity, your priorities, and a map to where things live. Keep it **lean** (a map, not a manual, detail belongs in your folders and skills). The only thing we ask: follow the best practices below.

## Best practices (the guardrails)
- **Secrets stay out of the repo.** Keys live in `.env` (it's gitignored, so it never reaches GitHub). Set a spend limit on each key; turn on 2FA. (Airlocks: scope access, contain the blast radius.)
- **Reversible by default.** Commit early and often, git is your safety net. Don't delete important work or force-push.
- **Review follows risk.** Keep deterministic checks. Use one meaningful independent review for nonproduction code; batch irreversible actions for the owner. Paid review is disabled unless separately authorized. Check the actual CI configuration before publishing; this instruction alone does not disable a workflow.
- **When you're stuck, use the unstuck protocol** (`docs/UNSTUCK_PROTOCOL.md`): Claude in caveman mode → screenshot + AI → YouTube (last 1–2 months) → NotebookLM → escalate. You'll solve ~99% yourself.
- **Lean beats bloated.** Add the high-impact core; look the specifics up as you go.

## Work that reaches use

AIOS turns a business outcome into a bounded job, gives it one builder, checks the result and follows it into actual use. A **pocket** groups related work, a **unit** is one job with an outcome, and its **unit issue** is the shared work record. An **execution claim** names the builder responsible for the next action. A **file/resource lock** identifies the specific material that builder is changing so another session can work elsewhere. An **agent-minute** estimates active AI work, with your own time estimated separately. **Accepted in use** means the owner has used and accepted the result. These terms describe responsibilities and evidence, not automatic permissions or background execution.

Before asking a new person (founder or operator) to make a workflow decision, explain its purpose and concrete effect using [How AIOS work reaches use](docs/how_aios_work_reaches_use.md). Use these terms as written and introduce each through the worked example.

- Before a plan starts, batch all needed keys, logins and decisions, each with what it unblocks. Check available access and whether the owner can act before routing to a teammate. Continue independent work.
- Each unit links its owning pocket, project and optional round by stable IDs, with dependencies separate from parent-child placement, and states outcome, owner/reviewer, risk and sensitivity, agent-minute estimate (human time separately), required owner inputs, exact file/resource lock, dependency effect and acceptance check. Missing information holds that unit only.
- Use one builder per independent pocket and two shared reviewers, with at most two unfinished candidates per pocket. A pocket groups work; it is not a dependency. Start fresh tasks from a short spec and keep existing IDs.
- Working state belongs in the unit issue, including one execution claim, current revision, state-entry time and evidence. Decisions and accepted use belong in the decision log. Where issue access is unavailable, report that specific limit rather than claiming an automatic board is installed.
- Review by consequence: docs/planning use automated checks; nonproduction code gets one meaningful reviewer; production databases, deletions, money and credentials go into a prepared human batch. Do not revive paid AI reviews. Immediately before publication, recheck the target base, active claims and open PRs touching the same files; reconcile overlaps with the owner. Inspect the target base's PR and push workflow triggers before publication; a PR can start a paid action automatically. If paid execution is possible or unknown, keep the patch local until disabled and continue deterministic local checks. Do not rerun paid CI to obtain review.
- A verified owner decision from any chat counts, but one claimed executor performs it once. An approval is not proof of execution. Reversible defaults need an explicit deadline; silence never authorizes irreversible actions.
- Investigations name the expected result and a stop condition. Finish with a fix, escalation package, one bounded next experiment or evidence exhausted. No polling/holding posts.
- Report source complete, installed, deployed and accepted in use separately. Batch owner QC at pocket completion; using daily tools counts as acceptance. Preserve every commitment as delivered, cancelled, replaced, active, deferred with a watched restart, or unresolved.
- Sensitivity follows the data: goals/workouts/tasks low, company operating records medium, credentials/payments/client personal data high. Keep baseline security and privacy boundaries; do not assume every personal record is low sensitivity.

## Your workspace
Seven domain folders, the same in every company's instance (`00_AIOS/routing.md` says which one takes which request):
`00_AIOS/` who we are (`company/` holds your Foundational 6), routing, decisions and the review queue · `01_Creation/` brand, the one asset library, preferences, finished outputs · `02_Team_Ops/` people, roles, projects, onboarding, routines · `03_RevOps/` site, funnels, CRM, automations, sales, customer journey, audits, reports, records · `04_Attention/` content, campaigns, publishing, accounts, performance · `05_Jobs/` recurring jobs · `99_Archive/`.
Setup is in `SETUP.md`. File naming: lowercase, underscores, no spaces (`taxonomy_rules.md`).

## Your skills
Type `/` to see them. What each one does: `.claude/skills/README.md`. Run `/start` any time to see the moves for your role.
- **Start and end every session:** start · start-my-day (reads where your work stands before it moves anything) · wrap-up (saves your work; pushes only when you say so) · context_load · dashboard
- **Setup and staying current:** onboard_wizard (run it first) · intake (your role, business, priorities, voice and goals, written into your files; re-run any time) · upskill · env_keys (your keys and your one core `.env`)
- **Think before you build:** grill_me · explain-from-the-ground-up (the background, terms and consequences behind a decision, before you judge it) · project_management
- **Your foundations and quality:** f6_completeness_check · qc_review · humanize
- **Keep the workspace healthy:** workspace_health · file_audit · security_check · changelog
- **Working as a team:** review-queue · resolve-conflict · pr_review (proportionate review; no automatic paid calls)
- **Money:** financial_teardown
- **Sounds (Mac):** pause · play (quiet or restore the finished / needs-you sounds for Claude and Codex)
- **Documents:** Word, PDF, PowerPoint and Excel come from Anthropic's `document-skills` plugin, which `/onboard_wizard` installs. They are Anthropic's, not copied here (`THIRD_PARTY_NOTICES.md`).

Add your own (see `docs/UNSTUCK_PROTOCOL.md` and the skills folder for how). Never run skills from sources you don't trust.

@.aios/operator_core/OPERATOR_CORE.md
@00_AIOS/routing.md
