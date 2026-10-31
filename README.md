# Your AIOS

**This workspace is yours.** AIOS Starter installs a reviewed operating layer into your own private repository. It gives your assistant a place to find company context, follow your rules, capture decisions and keep work moving. You own the company information and outputs you put here.

The Starter supplies the structure and tools. You and your team supply the business knowledge, choose the work and judge the result. Installing it does not run your business, grant access to FF's private methods or prove that an integration is live.

## Start here

1. **Install an approved release into an empty private repository.** You need git, Python 3, Node.js and the GitHub CLI. [GETTING_STARTED.md](GETTING_STARTED.md) steps 3 to 7 cover account creation, the repository and installation. Use the release installer rather than GitHub's green “Use this template” button: that button copies mutable `main`, without the installer's release and founder checks.
2. **Open your workspace in Claude Code and run `/onboard_wizard`.** It walks through setup, team access and your business context, then hands off to `/intake`. An operator joining later runs it too. Codex reads the managed `AGENTS.md`; the [install guide](docs/INSTALL_AND_UPGRADE.md) explains which instructions an upgrade replaces and which stay yours.
3. **Give it one real job.** “Help me plan this week,” “Draft this email in my voice,” or “What did we decide about pricing?” Check the result and keep the useful context. You can start with incomplete answers and add detail as you work.

For a first install, upgrade or rollback, follow [Install and upgrade](docs/INSTALL_AND_UPGRADE.md). Copying this repository's current branch is not an approved-release install.

## Where this repository fits

The company architecture uses four repository roles. A **company instance** is that company's own working context, records, configuration and outputs. It can span these repositories while keeping one coherent system through explicit references and permissions.

These are roles, not prescribed GitHub names. Use your company's actual repository map and configured destinations. This Starter installs one AIOS workspace; it does not create the other repositories, move existing records or establish their connections. If a destination is missing or inaccessible, report that and stop that send. Do not guess another repository or create one as a fallback.

| Company repository role | Purpose and what belongs there | Keep outside it |
|---|---|---|
| **AIOS** | Company context, the system map, routing and integration references. Keep the context the assistant needs to understand the business and links to the authoritative domain records. | Duplicate copies of every domain's records, other companies' private material, or FF's protected method source. |
| **Delegation** | Company roles, tasks, projects, planning and operating evidence: who owns the work, what happens next and what proves completion. | The authoritative financial record, the full creative asset library, or a second copy of company context maintained independently. Personnel records keep their actual access restrictions. |
| **Profit OS** | Company commercial, revenue and financial operations and data, including the authoritative offer and pricing records. | Unrelated company data, reusable FF method source, or credentials committed as ordinary records. Restricted commercial and financial information keeps its access boundary. |
| **Authority/Attention** | Company positioning, content, ads, creative inputs and finished assets, plus publishing and performance references. | FF's reusable writing or production implementation, another company's assets, or an assumption that a saved asset has been published. |

A repository link grants no access. Before a write, show the actual repository and path and why that destination fits. If the destination was already explicit and authorized, use it without asking the same question again. If it was not, settle the destination before sending company material.

### Company work and FF intelligence

Your brief, voice, scripts, brand inputs, configuration and finished outputs stay in the owning company instance. FF maintains reusable methods in its intelligence repositories. Copy Brain owns persuasive writing methods; Creation owns production methods and code. A company does not need extra Copy Brain or Creation repositories just to use those capabilities, and owning an instance does not grant access to the private intelligence source.

Where an entitled capability is available, the authorized Core interface carries a scoped request and returns its result to the company instance. The Starter includes an optional thin client, not the private method or engine. [The Core Bridge client guide](.aios/core_bridge/README.md) and [the install guide's capability section](docs/INSTALL_AND_UPGRADE.md#optional-ff-intelligence-capability) explain its configuration and refusals. An installed client does not establish entitlement, a live endpoint or an available writing or production capability.

### Follow a request to its home

| Request | Route and result |
|---|---|
| “What price did we approve?” | AIOS uses its system map to find the authoritative offer or pricing record in Profit OS. Link that record rather than maintaining a conflicting price in several repositories. |
| “Plan next week's launch work.” | Delegation owns the plan, roles, tasks and completion evidence. Refer to Profit OS's commercial decisions and Authority/Attention's assets instead of copying their full records into the plan. |
| “Create a campaign from our approved offer.” | Profit OS supplies the approved offer; Authority/Attention owns the company brief, audience, voice and assets. Where the relevant capabilities are available and authorized, the handoff is Attention brief → Copy Brain script → Creation asset → Attention scheduling and performance. Retain company inputs and outputs in their company destinations and verify each handoff. This example does not establish those connections or authorize publication. |
| “Improve the reusable video-layout checker.” | Route a method or code correction to the existing FF Creation intelligence owner, using a bounded example that does not disclose company material. Do not change private method source from a client instance or copy company assets into shared intelligence. |

For projects, tasks, issues, reviewers and delivery states, use [How AIOS work reaches use](docs/how_aios_work_reaches_use.md). It explains those terms through one job. The repository roles above describe where information belongs; they do not replace that work model.

## What the Starter installs

**A workspace with seven domain folders.** `00_AIOS` holds company context, routing, decisions and the review queue. `01_Creation`, `02_Team_Ops`, `03_RevOps` and `04_Attention` organize work inside this workspace; `05_Jobs` holds recurring-job records and `99_Archive` holds finished material. [The routing map](00_AIOS/routing.md) gives request-to-folder examples and the old-to-new folder map.

Those seven folders are the shipped workspace layout, not seven repositories or proof that the four-repository company structure has been provisioned. Keep existing records in their current homes until their owner completes a reviewed transition and verifies the receiving consumers.

**Skills you can run by name.** Type `/` in Claude Code or use [the skill index](.claude/skills/README.md). `/onboard_wizard` starts setup, `/intake` captures business context, and `/start` reports the role, installed release and workspace checks. A skill is instructions that run with your access, so read one before trusting it.

**Files with clear ownership.** `README.md` and `CLAUDE.md` are starter files you can shape for your business. An upgrade preserves existing copies, so a template README update does not replace your company's README. `AGENTS.md` and other managed system files follow the release's ownership list and are replaced on upgrade. Use [the install guide](docs/INSTALL_AND_UPGRADE.md) before changing or upgrading the managed layer; editing one instruction file does not automatically update every tool's instructions.

**A pull-request reviewer.** Its deterministic floor fails the `pr-gate` status for leaked secrets or env files, destructive or security-weakening SQL, file names with spaces, or a broken symlink under `.claude/`. An error-level AI finding, when AI review is configured, or an unfinished deterministic check also fails that status. Whether a failed status stops a merge depends on branch protection; other findings are advice. [PR reviewer setup](docs/PR_REVIEWER_SETUP.md) explains configuration. Paid review is disabled for FF-owned repositories; a client-owned installation needs its own authorized configuration.

## Keep the system yours

- **Keep secrets out of Git.** Put keys, passwords and tokens in the approved local secret store or ignored `.env`, never in committed company records. Set spend limits and use two-factor authentication. Private company records belong only in their authorized destinations.
- **Make reversible changes.** Work on a branch, commit useful progress and review changes before they reach shared use. Follow the separate owner gates for access, spending, publication and irreversible work.
- **Keep one authoritative record.** Use pointers when another repository owns the fact. Archive stale working material through the existing process rather than leaving several competing versions.
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
| Configure the optional authorized capability client | [Core Bridge client](.aios/core_bridge/README.md) |
| Configure a repository reviewer | [PR reviewer setup](docs/PR_REVIEWER_SETUP.md) |
| Resolve a failed step | [Unstuck protocol](docs/UNSTUCK_PROTOCOL.md) |
