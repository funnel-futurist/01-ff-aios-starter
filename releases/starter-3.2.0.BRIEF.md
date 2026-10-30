# Release brief: AIOS Starter 3.2.0

> **Candidate, not approved.** `releases/starter-3.2.0.json` is a draft pinned to `b84d1380b175a31aa4263532c0c1c354c7fc95f8`. Nothing is tagged and nothing installs it until a founder approves that exact commit in their own words (ruling D3). The approval block in the record is empty on purpose.

**Written for:** the founder, before approving. About three minutes.

## Decision
**Approve AIOS Starter 3.2.0 at `b84d138`.**
- **Why now:** the newest approved release, 3.1.0, does not contain the conversational intake, so a new learner who installs it never gets `/intake` or the onboarding wizard's hand-off to it. Both are already on `main`. 3.1.0 was approved before them, and the install route only ever installs an approved release, never `main`.
- **What it asks of you:** one approval of this exact commit. It changes no layout and moves no file, so a 3.1.0 workspace upgrades in the ordinary way. 3.1.0 workspaces keep every file they already have.

## What a learner gets that 3.1.0 lacks
| New | What it means for a learner |
|---|---|
| **`/intake`** | A conversation that asks one question at a time (role, business, priorities, voice samples, current tools, immediate goals) and writes each answer into `00_AIOS/company/profile_snapshot/intake.md` as it goes. It can stop halfway and pick up later, or re-run one topic. It writes nothing else. The question list is a managed file: a change to it goes back to the Starter's owner. |
| **The onboarding wizard's Step 4 hands off to `/intake`** | The vision, mission and values file the wizard saves is where `/intake` starts, so the learner is not asked twice. |
| **First-time setup uses the approved release installer** | The wizard no longer says "Use this template". It sends a new learner to the install guide: an empty private repository, the newest approved release, its tag checked, then that release's installer. |
| **`/env_keys` and one core `.env`** | Every key in `.env.example` is labelled with its purpose, phase, where to get it, cost and owner. A value-free key registry and a form registry template ship beside it, with an outline for the keys lesson. |
| **Wording fixes from the fresh-session check and its review** ([03a #244](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244#issuecomment-6490504337)) | In a voice sample, another person's name, email or phone number is replaced by `[name]`, `[email]` or `[phone]`, the question tells the learner to leave them in, and the sample is otherwise unchanged. One answer format and one skipped-question line. A blank template means the question is asked open, and the connections file's two default rows are ignored. The repository's new name (`01-ff-aios-starter`) is used wherever a learner clones or enters it. The docs that said the PR reviewer "never blocks" now say what the shipped workflow does: its deterministic check fails the `pr-gate` status on a real danger or when it did not finish, and everything else is advice. |
| **How AIOS work reaches use** (`docs/how_aios_work_reaches_use.md`, from #62) | A plain-language guide with a worked example. It defines the working terms the host instructions use (pocket, unit and its issue, execution claim, file lock, agent-minute, accepted in use) and tells the assistant to explain a workflow decision with it before asking a new person to make one. It is a managed file, so upgraded workspaces receive it. |
| **A GitHub agent App setup guide** (`docs/human_steps/configure_github_agent_app.md`, with matching `SETUP.md` and install-guide steps) | Step-by-step for a client creating their own GitHub App so their assistant can work in their repository: a baseline permission set and an optional one, which accounts qualify, and three separate checks (configured, accepted, fresh token). It carries no FF-specific IDs, secrets or bypass defaults. Independently reviewed (MATCH) before it was applied. |
| **The reviewer's blocking cases stated in full** | `README.md`, `GETTING_STARTED.md`, `SECURITY.md` and `SETUP.md` now list what actually fails the `pr-gate` status: leaked secrets or env files, destructive or security-weakening SQL, file names with spaces, a broken symlink under `.claude/`, an error-level finding from the AI review when one is set up, and a check that did not finish. |
| **Install guide and a human step corrected** | The upgrade steps that failed as written are fixed, and the restore-founder-review step has better commit wording. |

## Two changes to decide on before you approve
**1. FF's internal operating model reaches every upgraded workspace.**
- **`CLAUDE.md` is a starter file.** A new install gets the new text. An existing workspace keeps its own copy.
- **`AGENTS.md` is managed and replaced on upgrade.** Every 3.1.0 workspace that upgrades gets the new "Work that reaches use" section in `AGENTS.md`, which is what Codex reads, while its `CLAUDE.md` stays as it was. The two tools then run on different instructions in the same workspace.
- **Where it comes from.** The section came in with commit `364c763d` ("Align starter host instructions with approved unit execution model", 10-26). It is FF's internal operating model. #62 (merged 20:07:30Z on 10-30 as `1d1ff7c4`, with an approving review and every required check) now explains it: the section defines pocket, unit, unit issue, execution claim, file lock, agent-minute and accepted in use in one short paragraph, and points to the new guide, which teaches them through a worked example. One working term, **two shared reviewers**, is still used without a definition in the guide. The "Review follows risk" line beside it is generic and matches the shipped workflow.
- **Your choice.** Approving as written ships it, with the explanation. Trimming the section to the generic lines first is a separate change and would move the pin. I did not trim it.

**2. The shipped review workflow is stricter.**
- The review's verdict comes only from the reviewer and the base branch, a pull request that commits its own `verdict.json` is refused, and an incomplete deterministic check fails the gate (`gateFail = staticBlocked || !staticReported || STATIC_RESULT !== 'success' || hasErrorSeverity`).
- Auto-merge needs a successful AI review and the repository variable `PR_AUTOMERGE` set to `on`.
- Paid review is off for FF-owned repositories; a client-owned install may use its own credentials.

## Compatibility
- Upgrade from 3.1.0 is ordinary: no folder moves and no ownership-list change. The earliest release that can upgrade is still 2.6.0.
- 166 files (105 managed, 61 starter files), 24 skills. 3.1.0 had 157 files and 22 skills. Nothing is removed and 19 existing files changed. Nine files are new: the `intake` and `env_keys` skills (four files), the two registries, the keys lesson outline, the work-reaches-use guide and the GitHub App setup guide.

## Evidence
In `evidence/dispatch/p22-starter/release-3.2.0/`:
- `tests_3.2.0.txt`: the full suite (`tests/aios`) and `tests.test_verify_skills`, run on the candidate head.
- `release_checks_3.2.0.txt`: `aios release verify` on the draft, which refuses because it isn't approved, and the pin and file hashes it checks.
- `RECEIPT_2026-10-30.md`: what was built, from which commit, how it differs from the candidate you were first shown, and what was not done.

## What approving does
- **You write the approval,** in your own words, naming the exact commit. The approval commit then changes only release records and this brief: the approval block and the `approved` status in 3.2.0's record, the `superseded` status in 3.1.0's, and an approved banner here. That commit is the one that gets tagged, as with 3.1.0.
- **Not part of this approval:** Starter kit items 1 to 3 (the clean-markdown standard, `/tidy`, the core-four check), which stay behind the standard rollout.
