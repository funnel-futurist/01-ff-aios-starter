# Your AIOS

**This workspace is yours.** AIOS Starter installs a reviewed operating layer into your own private repository. It gives your assistant a place to find company context, follow your rules, capture decisions and keep work moving. You own the company information and outputs you put here.

The Starter supplies the structure and tools. You and your team supply the business knowledge, choose the work and judge the result. Installing it does not run your business, grant access to Evergreen or prove that an integration is live.

## Start here

> **Getting implementation help from FF?** Your private AIOS repository belongs to your own GitHub account or organization. Give FF only the access agreed for installation, maintenance and support. Connect your own assistant through its existing GitHub integration. The steps below also support teams installing the workspace themselves.

1. **Install an approved release into an empty private repository.** You need git, Python 3, Node.js and the GitHub CLI. [GETTING_STARTED.md](GETTING_STARTED.md) steps 3 to 7 cover account creation, the repository and installation. Use the release installer rather than GitHub's green “Use this template” button: that button copies mutable `main`, without the installer's release and founder checks.
2. **Open your workspace in Claude Code and run `/onboard_wizard`.** It walks through setup, team access and your business context, then hands off to `/intake`. An operator joining later runs it too. Codex reads the managed `AGENTS.md`; the [install guide](docs/INSTALL_AND_UPGRADE.md) explains which instructions an upgrade replaces and which stay yours.
3. **Give it one real job.** “Help me plan this week,” “Draft this email in my voice,” or “What did we decide about pricing?” Check the result and keep the useful context. You can start with incomplete answers and add detail as you work.

For a first install, upgrade or rollback, follow [Install and upgrade](docs/INSTALL_AND_UPGRADE.md). Copying this repository's current branch is not an approved-release install.

## Where this repository fits

A **company instance** is one private, company-owned AIOS repository. Its folders hold company context, people, projects, configuration, work and evidence. Delegation, commercial operations and Attention are domains inside that workspace. They do not require separate instance repositories.

**FF's private Evergreen repository (shared with entitled clients)** is the planned shared source for five reusable brains. It holds methods, skills, jobs, operating instructions and quality controls. An authorized assistant reads the needed method, applies it to private company context and writes the result into this AIOS. Evergreen does not receive that private context.

| Brain | Owns the reusable method for | Typical company home |
|---|---|---|
| Copy Brain | Offers, persuasion, messaging, scripts and funnels | `00_AIOS/company/`, `01_Creation/outputs/copy/` or the owning campaign |
| Creation Brain | Design, documents, media and production quality | `01_Creation/` |
| AI-Augmented Team | Hiring, delegation, operator development, SOPs and jobs | `02_Team_Ops/` and `05_Jobs/` |
| Profit OS | Capture, conversion, close, commercial handoff and revenue operations | `03_RevOps/` |
| Attention | The authentic authority flywheel, distribution, publishing and performance | `04_Attention/` |

The five brains describe who owns a method. The seven workspace folders describe where this company's work lives. [Workspace routing](00_AIOS/routing.md) joins those two maps.

A separate deployed application or restricted data store can retain its existing home where there is a concrete deployment or access requirement. Record that dependency instead of inventing another instance.

### Read shared methods and keep company work private

The [Evergreen reference](00_AIOS/evergreen.json) starts **planned and unverified**. Its candidate repository and entry paths are a target structure, not a working connection. Confirm the actual published repository, access and method paths before using it. The [read contract](docs/architecture/evergreen_aios.md) explains the setup and evidence.

For new work, resolve the current method to an exact commit, read it and record that commit in the output's provenance. A running task keeps the revision it started with. Executable integrations that could break an existing workflow stay pinned and change through reviewed PRs.

Entitlement and GitHub Read access are separate records. Read access applies to the repository, including its readable folders and history; branches do not create private customer tiers. The client's agreement governs access and continuity. This Starter grants no entitlement.

**Hosted Core is deprecated.** There is no required FF service, endpoint or `FF_CORE_KEY` in the new-workspace path. The old thin client remains unchanged for compatibility under [decision 0002](docs/decisions/0002-hosted-core-thin-client-deprecated.md). Do not configure it for a new workspace.

If Evergreen is unavailable, continue work that can be completed from authorized company context. State which method read is unavailable. Do not claim to have used the latest method, silently invent it or treat a cached revision as current.

### Follow a request to its home

| Request | Route and result |
|---|---|
| “What price did we approve?” | Read the company's authoritative offer and economics records in `00_AIOS/company/`. Link the approval; do not generate another price. |
| “Plan next week's launch work.” | Put the plan, owners and evidence in `02_Team_Ops/projects/`, using the Team brain when its method is available. Link the approved offer and existing campaign. |
| “Create a campaign from our approved offer.” | Attention defines the campaign; Copy supplies the writing method; Creation supplies production methods; Attention owns the publishing plan and performance. Company artifacts stay in their designated folders. A saved campaign is not a published campaign. |
| “Activate this new customer.” | Profit OS supplies the commercial handoff method. The company [journey map](03_RevOps/customer_journey/journey_map.md) leads to an owned [90-day roadmap](03_RevOps/customer_journey/activation_roadmap_90_days.md). |
| “Bring this operator up to speed.” | Use the [operator journey](02_Team_Ops/onboarding/operator_journey.md) to connect the person's role, access, skills and first accepted result. |
| “Improve a reusable method.” | Prepare a sanitized finding for its FF brain owner. Company work does not grant permission to change Evergreen or disclose private inputs. |

For projects, PRs, reviews and evidence of actual use, read [How AIOS work reaches use](docs/how_aios_work_reaches_use.md). A PR is a proposed change; merging it does not prove that a deployment or business action happened.

## What the Starter installs

**A workspace with seven domain folders.** `00_AIOS` holds company context, routing, decisions and the review queue. `01_Creation`, `02_Team_Ops`, `03_RevOps` and `04_Attention` organize work inside this workspace; `05_Jobs` holds recurring-job records and `99_Archive` holds finished material. [The routing map](00_AIOS/routing.md) gives request-to-folder examples and the old-to-new folder map.

These seven folders are the company instance. Existing workspaces keep their current records until a reviewed adoption change maps the old paths and verifies their consumers. The Starter does not move existing repositories or provision Evergreen access.

**Skills you can run by name.** Type `/` in Claude Code or use [the skill index](.claude/skills/README.md). `/onboard_wizard` starts setup, `/intake` captures business context, and `/start` reports the role, installed release and workspace checks. A skill is instructions that run with your access, so read one before trusting it.

**Files with clear ownership.** `README.md` and `CLAUDE.md` are starter files you can shape for your business. An upgrade preserves existing copies, so a template README update does not replace your company's README. `AGENTS.md` and other managed system files follow the release's ownership list and are replaced on upgrade. Use [the install guide](docs/INSTALL_AND_UPGRADE.md) before changing or upgrading the managed layer; editing one instruction file does not automatically update every tool's instructions.

**A pull-request reviewer.** Its deterministic floor fails the `pr-gate` status for leaked secrets or env files, destructive or security-weakening SQL, file names with spaces, or a broken symlink under `.claude/`. An error-level AI finding, when AI review is configured, or an unfinished deterministic check also fails that status. Whether a failed status stops a merge depends on branch protection; other findings are advice. [PR reviewer setup](docs/PR_REVIEWER_SETUP.md) explains configuration. Paid review is disabled for FF-owned repositories; a client-owned installation needs its own authorized configuration.

## Keep the system yours

- **Keep secrets out of Git.** Put keys, passwords and tokens in the approved local secret store or ignored `.env`, never in committed company records. Set spend limits and use two-factor authentication. Private company records belong only in their authorized destinations.
- **Make reversible changes.** Work on a branch, commit useful progress and review changes before they reach shared use. Follow the separate owner gates for access, spending, publication and irreversible work.
- **Keep one authoritative record.** Link the authoritative company or provider record instead of keeping competing copies. Archive stale working material through the existing process rather than leaving several competing versions.
- **Review the result.** Source complete, reviewed, merged, installed, deployed and accepted in use are different stages. Use the existing work guide and receipts to say which one has actually happened.
- **Stay current through releases.** Run `/start` to see your installed release and verification result. Follow the approved-version upgrade and rollback route; do not overwrite company work with a copy of mutable `main`.

When a step fails, record what happened and follow [the unstuck protocol](docs/UNSTUCK_PROTOCOL.md). Keep working on independent tasks while the specific access, destination or technical problem is resolved.

## Guides to use next

| Need | Existing guide |
|---|---|
| First-time setup and team onboarding | [Getting started](GETTING_STARTED.md) and [Setup](SETUP.md) |
| Install, upgrade, ownership or rollback | [Install and upgrade](docs/INSTALL_AND_UPGRADE.md) |
| Choose a folder in this workspace | [Workspace routing](00_AIOS/routing.md) |
| Understand the work and its review stages | [How AIOS work reaches use](docs/how_aios_work_reaches_use.md) |
| Find a skill | [Skill index](.claude/skills/README.md) |
| Read the shared brains | [Evergreen and AIOS](docs/architecture/evergreen_aios.md) |
| Map customer and team progress | [Customer journey](03_RevOps/customer_journey/journey_map.md) and [operator journey](02_Team_Ops/onboarding/operator_journey.md) |
| Configure a repository reviewer | [PR reviewer setup](docs/PR_REVIEWER_SETUP.md) |
| Resolve a failed step | [Unstuck protocol](docs/UNSTUCK_PROTOCOL.md) |
