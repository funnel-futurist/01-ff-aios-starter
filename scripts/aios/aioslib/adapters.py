"""Tool adapters: which shipped files work with only one AI tool, and which with any.

The Starter's behaviour (instructions, skills, hooks, safety settings, the AI reviewer) is
built on Claude Code. `release/adapters.json` says so, file by file, and says honestly where
nothing else is supported. This module checks that the declaration and the tree agree:

* a file in a tool-specific location (`.claude/*`, `CLAUDE.md`, `AGENTS.md`, `.cursor/*` ...)
  that is not declared for that tool is a problem, so a new tool-specific file cannot arrive
  unnoticed;
* a declared file that no longer exists is a problem;
* a tool is `verified` only when it names evidence, and each piece of evidence must resolve to
  a real test. Every other tool is `not verified`, and declares no evidence.

What "verified" means here, and does not: the named tests exercise the file layout and the
hook contract (simulated hook input, the real hook command). They are not a recording of a
live session in that tool. The manifest says which.

Python 3.9+, standard library only.
"""

import json
import os
import re

from . import util
from .util import EXIT_PACKAGE, Refusal

SCHEMA = "ff-aios-starter/adapters@1"
MANIFEST_PATH = "release/adapters.json"
STATUSES = ("verified", "not verified")

AGENTS_PATH = "AGENTS.md"
CLAUDE_PATH = "CLAUDE.md"
NATIVE_CODEX_SKILLS = (
    "start", "start-my-day", "context_load", "grill_me", "onboard_wizard",
    "project_management", "wrap-up", "review-queue",
)

# Codex loads this bootstrap, then uses its read tools for the client's current constitution.
# A generated snapshot of the template's CLAUDE.md would hide later client customizations.
AGENTS_HEADER = """\
<!-- Managed Starter bootstrap. An approved upgrade replaces it; verify reports a hand edit. Client context stays in CLAUDE.md and the files it imports. -->
# Instructions for Codex and other tools that read AGENTS.md

## Load the current workspace context before working

At the start of every session, use your available read tools to read `CLAUDE.md` at this repository's root. Then read the context files it imports with `@path` syntax, resolving each path relative to the file containing it. Follow nested context imports too. Apply the current constitution, Operator Core and routing from those actual reads before doing the requested workspace task.

Read only this workspace's permitted context. If a required file is missing, unreadable, outside this workspace or is a credential file, stop workspace actions and report the exact context problem for its owner to repair. Do not substitute a template snapshot, cached company context, guessed routing or a guessed core version. When read tools are unavailable, report context NOT LOADED and stop; this bootstrap does not automatically inline or import that context.

This startup read is a tool action instructed by AGENTS.md, not native Codex support for Claude's `@` imports or a runtime security hook. Keep company rules and customization in the client-owned `CLAUDE.md` and its permitted context files. Do not copy them here or regenerate this file to customize the business.

- Codex discovers eight Starter workflows under `.agents/skills/`; invoke them as `$start`, `$start-my-day`, `$context_load`, `$grill_me`, `$onboard_wizard`, `$project_management`, `$wrap-up` or `$review-queue`. Their canonical instructions and resources remain under `.claude/skills/`. Other workflows still require opening their canonical `SKILL.md`.
- Normal Codex instruction hierarchy still applies: a root override can replace this bootstrap, and nested AGENTS.md files can add folder-specific instructions. Those files do not grant permissions or prove this startup read happened.
"""


def render_agents_md(repo):
    """The managed bootstrap never reads, snapshots or overwrites client context.

    `repo` remains part of the authoring interface; live context is read by the session,
    not by this renderer. That also keeps client rules out of a shared generated file.
    """
    return AGENTS_HEADER


def agents_md_problem(repo):
    """None when AGENTS.md is exactly what `render_agents_md` produces for this tree."""
    path = os.path.join(repo, AGENTS_PATH)
    if not os.path.isfile(path):
        return "%s is missing: run `python3 scripts/aios/aios.py adapters render`" % AGENTS_PATH
    try:
        expected = render_agents_md(repo)
    except Refusal as exc:
        return "%s can't be rendered: %s" % (AGENTS_PATH, exc.message)
    with open(path, encoding="utf-8") as fh:
        if fh.read() != expected:
            return ("%s is not the managed bootstrap: run "
                    "`python3 scripts/aios/aios.py adapters render`" % AGENTS_PATH)
    return None


def render_codex_skills(repo):
    """Thin native entries, with discovery metadata from the one workflow source.

    Only these eight workflows are currently supported. Validate every source before the
    authoring command writes anything; missing or unsupported metadata is not a blank skill.
    The supported scalar subset is quoted text or single-line plain text beginning with a
    letter. Other YAML forms must be quoted as text or are refused, never coerced to strings.
    """
    rendered = {}
    for name in NATIVE_CODEX_SKILLS:
        source = ".claude/skills/%s/SKILL.md" % name
        path = ".agents/skills/%s/SKILL.md" % name
        for rel in (source, path):
            here = os.path.abspath(repo)
            for part in rel.split("/"):
                here = os.path.join(here, part)
                if os.path.islink(here):
                    raise Refusal(EXIT_PACKAGE, "linked skill path refused: %s" % rel)
        destination = os.path.join(repo, path)
        if os.path.lexists(destination) and not os.path.isfile(destination):
            raise Refusal(EXIT_PACKAGE, "native skill destination is not a file: %s" % path)
        full = os.path.join(repo, source)
        if not os.path.isfile(full) or os.path.islink(full):
            raise Refusal(EXIT_PACKAGE, "canonical skill is missing or linked: %s" % source)
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
        metadata = {}
        for key in ("name", "description"):
            values = re.findall(r"^%s:[ \t]*(.+)$" % key, front[1] if front else "", re.M)
            if len(values) != 1 or values[0].strip() in ("|", ">", "|-", ">-"):
                raise Refusal(EXIT_PACKAGE, "%s needs one single-line %s" % (source, key))
            value = values[0].strip()
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except ValueError:
                    raise Refusal(EXIT_PACKAGE, "%s has invalid quoted %s" % (source, key))
            elif value.startswith("'"):
                if not re.fullmatch(r"'(?:[^']|'')*'", value):
                    raise Refusal(EXIT_PACKAGE, "%s has invalid quoted %s" % (source, key))
                value = value[1:-1].replace("''", "'")
            elif (not value or not value[0].isalpha() or
                  value.casefold() in ("null", "true", "false", "yes", "no", "on", "off") or
                  re.search(r"(?:^|\s)#|:\s", value) or
                  re.search(r"^%s:[^\n]*\n[ \t]+[^#\s]" % key, front[1], re.M)):
                raise Refusal(EXIT_PACKAGE, "%s needs a supported string scalar for %s; quote literal text" % (source, key))
            if not isinstance(value, str) or not value.strip():
                raise Refusal(EXIT_PACKAGE, "%s has empty %s" % (source, key))
            metadata[key] = value
        if metadata["name"] != name:
            raise Refusal(EXIT_PACKAGE, "canonical skill name differs from its directory: %s" % source)
        rendered[path] = (
            "---\nname: %s\ndescription: %s\n---\n\n"
            "<!-- Generated by `aios adapters render-skills`; edit the canonical workflow. -->\n\n"
            "Read `%s` from the repository root and follow that workflow for this request. "
            "Resolve its relative references and scripts from `.claude/skills/%s/`, "
            "not from this native entry. The canonical workflow owns permissions, refusals "
            "and outputs; this entry adds Codex discovery only.\n"
        ) % (name, json.dumps(metadata["description"].replace("\u2014", ","), ensure_ascii=False), source, name)
    return rendered


def codex_skill_problems(repo, declared):
    """Check only declared native entries; small manifest fixtures need not ship them."""
    native = [p for p in declared if p.startswith(".agents/skills/")]
    if not native:
        return []
    try:
        expected = render_codex_skills(repo)
    except Refusal as exc:
        return [exc.message]
    out = []
    for path, text in expected.items():
        full = os.path.join(repo, path)
        if path not in native:
            out.append("native Codex entry is undeclared: %s" % path)
        elif not os.path.isfile(full) or os.path.islink(full):
            out.append("native Codex entry is missing or linked: %s" % path)
        else:
            with open(full, encoding="utf-8") as fh:
                if fh.read() != text:
                    out.append("%s is stale: run `aios adapters render-skills`" % path)
    return out


def load(repo):
    path = os.path.join(repo, MANIFEST_PATH)
    if not os.path.isfile(path):
        raise Refusal(EXIT_PACKAGE, "no adapter manifest at %s" % MANIFEST_PATH,
                      ["it lives in the Starter's own repository; an installed workspace does not carry it"])
    data = util.read_json(path)
    if data.get("schema") != SCHEMA:
        raise Refusal(EXIT_PACKAGE, "%s is not a %s file" % (MANIFEST_PATH, SCHEMA))
    return data


def _evidence_problem(repo, ref):
    """None if `path` or `path::Class::method` names something that exists."""
    parts = ref.split("::")
    path = parts[0]
    full = os.path.join(repo, path)
    if not os.path.isfile(full):
        return "evidence %r: no such file" % ref
    if len(parts) == 1:
        return None
    if len(parts) != 3:
        return "evidence %r: use path or path::Class::method" % ref
    with open(full, encoding="utf-8") as fh:
        text = fh.read()
    cls = re.search(r"^class %s\b.*?(?=^class |\Z)" % re.escape(parts[1]), text, re.S | re.M)
    if not cls:
        return "evidence %r: no class %s" % (ref, parts[1])
    if not re.search(r"^\s+def %s\(" % re.escape(parts[2]), cls.group(0), re.M):
        return "evidence %r: no test %s in %s" % (ref, parts[2], parts[1])
    return None


def problems(repo, files):
    """Every way the manifest and the tree disagree. `files` = repo-relative tracked paths."""
    manifest = load(repo)
    out = []
    tools = manifest.get("tools") or {}
    if not tools:
        return ["the manifest declares no tools"]
    fileset = set(files)
    owner = {}

    for name, tool in sorted(tools.items()):
        status = tool.get("status")
        if status not in STATUSES:
            out.append("%s: status must be one of %s, got %r" % (name, STATUSES, status))
        evidence = tool.get("evidence") or []
        if status == "verified":
            if not evidence:
                out.append("%s is marked verified but names no test that proves it" % name)
            for ref in evidence:
                bad = _evidence_problem(repo, ref)
                if bad:
                    out.append("%s: %s" % (name, bad))
        elif evidence:
            out.append("%s is 'not verified' but lists evidence: either it is verified or it is not" % name)

        declared = tool.get("files") or []
        for path in declared:
            if path in owner:
                out.append("%s is declared for both %s and %s" % (path, owner[path], name))
            owner[path] = name
            if path not in fileset:
                out.append("%s declares %s, which does not exist: remove the entry" % (name, path))
        for path in sorted(fileset):
            if util.match_any(tool.get("signatures"), path) and path not in declared:
                out.append("%s is tool-specific to %s (matches its signatures) but is not declared in "
                           "release/adapters.json" % (path, name))

    neutral = manifest.get("tool_neutral") or []
    for pattern in neutral:
        hits = [p for p in fileset if util.match_pattern(pattern, p)]
        if not hits:
            out.append("tool_neutral %r matches no file: remove or fix the entry" % pattern)
        for p in hits:
            if p in owner:
                out.append("%s is declared tool-specific (%s) and tool-neutral" % (p, owner[p]))

    for entry in manifest.get("mixed") or []:
        if entry.get("path") not in fileset:
            out.append("mixed entry %r does not exist" % entry.get("path"))
        if not (entry.get("tool_specific_part") and entry.get("neutral_part")):
            out.append("mixed entry %r must say which part is tool-specific and which is neutral"
                       % entry.get("path"))

    if AGENTS_PATH in fileset:
        stale = agents_md_problem(repo)
        if stale:
            out.append(stale)
    out.extend(codex_skill_problems(repo, tools.get("codex", {}).get("files") or []))
    return out
