# Release brief: AIOS Starter 3.3.0 (DRAFT)

> **Draft only: nothing installs it until a founder approves this exact payload in their own words.** The record is pinned at `006fd6f853ff1c7fbeae1722156df1a1efbadd73` and its status is `draft`; the builder cannot write anything else. Approved 3.2.0 is unchanged and stays pinned to `b84d1380b175a31aa4263532c0c1c354c7fc95f8`.

**Written for:** the founder and release owner. About three minutes.

## What this candidate is
An additive successor to 3.2.0: 169 files (108 managed, 61 starter files) and 25 skills, where 3.2.0 had 166 files and 24 skills. The three new files are the explanation skill and the two files of the daily routine's helper and reference. Nothing is removed, no file moves and the folder layout is unchanged, so a 3.2.0 workspace upgrades in the ordinary way. The earliest release that can upgrade is still 2.6.0.

## What a learner gets that 3.2.0 lacks
| New | What it means for a learner |
|---|---|
| **`/explain-from-the-ground-up`** (new skill) | Explains an unfamiliar topic or decision from the background up before anyone is asked to judge it: why it exists, each term in plain words, one mapped metaphor with the place it stops being accurate, what is established versus unknown, and what each choice changes, including doing nothing. It explains the question; it never decides it or approves anything. It is adapted from an existing skill, whose source hash is recorded in the file, with a generic trigger. |
| **The daily routine, client edition** (`/start-my-day`, `/wrap-up`, `START_HERE.md`) | The start and end of a session now begin by reading where your work stands, including work that exists only on this computer, and never move, stash, switch or delete unsaved work. `/wrap-up` saves and names your local-only work and pushes your branch only when you say so, never as a backup. A bundled read-only helper inventories the folders you name and writes a private receipt; nothing is scanned unless you name it, and nothing is scheduled. `START_HERE.md` no longer promises a blanket sync, cleanup or push, or that nothing can be broken. |
| **The company-repositories explanation and the reviewer-wording corrections** (already on `main` from #63, not new in this candidate) | The README's four-repository explanation and routing examples, the three wording corrections 3.2.0 deferred, and the completed `pr_review` contract. The README is a starter file, so existing workspaces keep their own copy. |
| **Setup order in the onboarding wizard** (already on `main` from #64, not new in this candidate) | Step 2 now puts the local tools (git, Python 3, Node.js) and the GitHub CLI sign-in before the approved-release install, matching the getting-started steps. Only those three lines of the wizard change. |

## How an existing workspace finds the new skill
- **`CLAUDE.md` is a starter file.** A new install gets the new text, which names the skill. An existing workspace keeps its own `CLAUDE.md`, byte for byte, so that file will not list the skill. This release does not add a seed line or touch it.
- **The skill file, the skills README, `AGENTS.md`, `START_HERE.md`, the two routine skills and the helper and reference are managed.** An upgrade installs the skill at `.claude/skills/explain-from-the-ground-up/SKILL.md`, adds the two new routine files and replaces the others, so the skill sits where Claude Code looks for skills, and the skills README lists it, even when the workspace's `CLAUDE.md` is the client's own edited copy.
- **What is and is not shown.** The Starter's verified scope for Claude Code is the file layout and the hook contract, tested with simulated input; no live session is recorded. Codex does not register Claude-folder skills: its instructions tell it to open the file by hand, and the skill's own text says so. A plain-language fallback request is in the skill for anyone with neither.

## Not claimed, not approved
- **No release payload, tag, install or learner adoption is approved or done.** Approval needs an independent review of this exact pin, a real eligible approving review, and the founder's own words.
- No other approved record is touched.
- The daily routine is in this candidate as a client edition only. It creates no scheduler, and no cadence is proposed or enabled; a client who wants one sets it up with a tool that supports it and reads back its real configuration.
- The certification lesson that teaches this skill is a separate source change in the certification drafts; adopting it goes through the existing certification update route.

## Evidence
The writer returns the evidence on the working unit (03a #244, with the teaching side on #305), not in this tree: the built manifest holds the new file as a managed file, and a bounded install, upgrade, rollback and refusal check on synthetic private workspaces, including an upgrade in which the client's own edited and committed `CLAUDE.md` stays byte for byte, the new skill is installed and findable, rollback removes it, and a file the client already has at that path is refused and not overwritten. The public-tree and protected-text checks and the adapter check pass on this pin.
