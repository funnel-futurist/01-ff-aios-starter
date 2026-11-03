<!-- Managed Starter bootstrap. An approved upgrade replaces it; verify reports a hand edit. Client context stays in CLAUDE.md and the files it imports. -->
# Instructions for Codex and other tools that read AGENTS.md

## Load the current workspace context before working

At the start of every session, use your available read tools to read `CLAUDE.md` at this repository's root. Then read the context files it imports with `@path` syntax, resolving each path relative to the file containing it. Follow nested context imports too. Apply the current constitution, Operator Core and routing from those actual reads before doing the requested workspace task.

Read only this workspace's permitted context. If a required file is missing, unreadable, outside this workspace or is a credential file, stop workspace actions and report the exact context problem for its owner to repair. Do not substitute a template snapshot, cached company context, guessed routing or a guessed core version. When read tools are unavailable, report context NOT LOADED and stop; this bootstrap does not automatically inline or import that context.

This startup read is a tool action instructed by AGENTS.md, not native Codex support for Claude's `@` imports or a runtime security hook. Keep company rules and customization in the client-owned `CLAUDE.md` and its permitted context files. Do not copy them here or regenerate this file to customize the business.

- Codex discovers eight Starter workflows under `.agents/skills/`; invoke them as `$start`, `$start-my-day`, `$context_load`, `$grill_me`, `$onboard_wizard`, `$project_management`, `$wrap-up` or `$review-queue`. Their canonical instructions and resources remain under `.claude/skills/`. Other workflows still require opening their canonical `SKILL.md`.
- Normal Codex instruction hierarchy still applies: a root override can replace this bootstrap, and nested AGENTS.md files can add folder-specific instructions. Those files do not grant permissions or prove this startup read happened.
