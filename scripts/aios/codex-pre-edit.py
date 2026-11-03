#!/usr/bin/env python3
"""Adapt native Codex patches to the existing founder-lane policy; never apply a patch."""
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))


def deny(reason):
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def patch_paths(command):
    """Extract native patch headers, refusing grammar we cannot safely account for."""
    if not isinstance(command, str) or "\0" in command:
        raise ValueError("patch must be text without NUL bytes")
    lines = command.splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("expected a complete native patch")
    paths, i = [], 1
    while i < len(lines) - 1:
        header = re.fullmatch(r"\*\*\* (Add|Update|Delete) File: (.+)", lines[i])
        if not header:
            raise ValueError("unsupported patch header")
        operation, path = header.groups()
        paths.append(path)
        i += 1
        if operation == "Update" and lines[i].startswith("*** Move to: "):
            paths.append(lines[i][len("*** Move to: "):])
            i += 1
        body_start = i
        while i < len(lines) - 1 and not re.match(r"\*\*\* (?:Add|Update|Delete) File: ", lines[i]):
            line = lines[i]
            if operation == "Delete":
                raise ValueError("delete header must not have a body")
            if operation == "Add":
                valid = line.startswith("+")
            else:
                valid = (line.startswith((" ", "+", "-", "@@ ")) or
                         line in ("@@", "*** End of File"))
            if not valid:
                raise ValueError("unsupported patch body")
            i += 1
        if operation == "Update" and i == body_start:
            raise ValueError("update must have a patch body")
    return paths


def inside(root, path):
    return os.path.commonpath([str(root), os.path.realpath(path)]) == str(root)


def decision(event, root=None, identify=None):
    if isinstance(event, dict):
        if isinstance(event.get("hook_event_name"), str) and event["hook_event_name"] and event["hook_event_name"] != "PreToolUse":
            return None
        if isinstance(event.get("tool_name"), str) and event["tool_name"] and event["tool_name"] != "apply_patch":
            return None
    if (not isinstance(event, dict) or event.get("hook_event_name") != "PreToolUse" or
            event.get("tool_name") != "apply_patch" or not isinstance(event.get("tool_input"), dict)):
        return deny("Codex edit safety input is malformed; no edit was authorized.")
    try:
        from aioslib import boundary
        root = Path(root or ROOT).resolve()
        cwd = event.get("cwd")
        if not isinstance(cwd, str) or not os.path.isabs(cwd) or not os.path.isdir(cwd) or not inside(root, cwd):
            raise ValueError("patch working directory is outside this workspace or unavailable")
        paths = []
        for path in patch_paths(event["tool_input"].get("command")):
            if (path != path.strip() or not path or "\\" in path or os.path.isabs(path) or
                    re.match(r"^[A-Za-z]:", path) or ".." in path.split("/")):
                raise ValueError("patch path is absolute, ambiguous or contains traversal")
            full = os.path.join(cwd, path)
            if not inside(root, full) or os.path.realpath(full) == str(root):
                raise ValueError("patch path resolves outside this workspace")
            paths.append(full)
        # Validate the whole patch before any role/identity lookup.
        for path in paths:
            allowed, reason = boundary.check_edit(str(root), "Edit", {"file_path": path}, identify=identify)
            if not allowed:
                return deny(reason)
        return None
    except (ValueError, OSError) as exc:
        return deny("Codex edit refused: %s. No edit was authorized." % exc)
    except Exception:
        return deny("Codex role check is unavailable; no edit was authorized. Repair the workspace policy or hook dependency.")


def main():
    try:
        result = decision(json.load(sys.stdin))
    except Exception:
        result = deny("Codex edit safety input is invalid; no edit was authorized.")
    if result:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
