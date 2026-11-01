#!/usr/bin/env python3
"""Read-only inventory of the git repositories under explicitly named roots.

It answers one question for the start and end of a work day: what exists locally, on which branch, how far from its
upstream, and what is dirty, untracked or ignored. It reads git metadata only. It never reads a file's contents, a
remote URL, a git config value or a credential, and it never runs a git command that writes (no add, commit, push,
fetch, checkout, stash, clean, gc). Nested repositories and linked worktrees are separate entries.

    reconcile_local.py --root DIR [--root DIR ...] --out-dir DIR [--exclude DIR ...] [--max-depth N]
                       [--max-dirs N] [--max-repos N] [--timeout S] [--git-timeout S] [--names-limit N]

Exit 0: every repository was read. Exit 1: the run finished but coverage is incomplete (a limit was hit, a timeout
fired or a repository failed), and the receipt says which. Exit 2: refused before scanning anything.

The receipt is a new private file in --out-dir (mode 0600, directory 0700). --out-dir may not sit inside any git
repository, so a receipt can never be staged by accident. Names of credential-like paths are never recorded.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".cache", ".Trash"}
CREDENTIAL_LIKE = re.compile(r"(^|[._/-])(env|secret|secrets|token|tokens|credential|credentials|password|passwd|"
                             r"apikey|api_key|private_key|id_rsa|id_ed25519|keychain)([._/-]|$)|\.(pem|p12|pfx|key|kdbx)$",
                             re.IGNORECASE)
SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT")


class Refusal(Exception):
    """A request refused before anything is scanned."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_env() -> dict:
    env = {k: os.environ[k] for k in SAFE_ENV_KEYS if k in os.environ}
    env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0",
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    return env


def run_git(repo: str, args: list, timeout: float):
    """Run one read-only git command. Returns (returncode, stdout) or raises subprocess.TimeoutExpired."""
    proc = subprocess.run(["git", "-C", repo, "-c", "core.fsmonitor=false", "-c", "core.quotepath=off"] + args,
                          capture_output=True, timeout=timeout, env=git_env(), check=False)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def inside_git_repo(path: str) -> bool:
    cur = os.path.realpath(path)
    while True:
        if os.path.lexists(os.path.join(cur, ".git")):
            return True
        parent = os.path.dirname(cur)
        if parent == cur:
            return False
        cur = parent


def under(path: str, ancestor: str) -> bool:
    return path == ancestor or path.startswith(ancestor.rstrip(os.sep) + os.sep)


def validate(args) -> tuple:
    if not args.root:
        raise Refusal("name at least one --root; nothing is scanned by default")
    home = os.path.realpath(os.path.expanduser("~"))
    roots = []
    for raw in args.root:
        real = os.path.realpath(os.path.expanduser(raw))
        if not os.path.isdir(real):
            raise Refusal("root is not a directory: " + raw)
        if real in (home, os.sep):
            raise Refusal("root may not be the home directory or the filesystem root: " + raw)
        if real not in roots:
            roots.append(real)
    excludes = [os.path.realpath(os.path.expanduser(e)) for e in args.exclude]
    for real in roots:
        for ex in excludes:
            if under(real, ex):
                raise Refusal("root is inside an excluded path: " + real)
    for name in ("max_depth", "max_dirs", "max_repos", "timeout", "git_timeout", "names_limit"):
        if getattr(args, name) < 0 or (name != "names_limit" and getattr(args, name) == 0):
            raise Refusal("--%s must be positive" % name.replace("_", "-"))
    if not args.out_dir:
        raise Refusal("--out-dir is required: the receipt is a new private file")
    out = os.path.realpath(os.path.expanduser(args.out_dir))
    if inside_git_repo(out):
        raise Refusal("--out-dir sits inside a git repository; receipts live outside Git")
    for real in roots:
        if under(out, real):
            raise Refusal("--out-dir sits inside a scanned root")
    return roots, excludes, out


def note_unreadable(notes: dict, path: str) -> None:
    """A traversal failure makes coverage incomplete; keep its evidence (a capped, credential-filtered path list)."""
    notes["unreadable_dirs"] += 1
    if len(notes["unreadable_paths"]) < 20:
        notes["unreadable_paths"].append(safe_name(path))
    else:
        notes["unreadable_paths_truncated"] = True


def discover(roots: list, excludes: list, max_depth: int, max_dirs: int, max_repos: int, deadline: float) -> tuple:
    """Walk the roots without following symlinks. Returns (repo paths, coverage notes)."""
    repos, notes = [], {"dirs_visited": 0, "symlinks_skipped": 0, "unreadable_dirs": 0, "depth_cut": 0,
                        "truncated_dirs": False, "truncated_repos": False, "timed_out": False,
                        "loose_files_outside_repos": 0, "loose_files_listed": False,
                        "unreadable_paths": [], "unreadable_paths_truncated": False}
    seen = set()
    for root in roots:
        stack = [(root, 0)]
        while stack:
            path, depth = stack.pop()
            if time.monotonic() > deadline:
                notes["timed_out"] = True
                return repos, notes
            if path in seen:
                continue
            seen.add(path)
            if notes["dirs_visited"] >= max_dirs:
                notes["truncated_dirs"] = True
                return repos, notes
            notes["dirs_visited"] += 1
            if os.path.lexists(os.path.join(path, ".git")):
                if len(repos) >= max_repos:
                    notes["truncated_repos"] = True
                    return repos, notes
                repos.append(path)
            try:
                entries = sorted(os.scandir(path), key=lambda e: e.name)
            except OSError:
                note_unreadable(notes, path)
                continue
            if not any(under(path, r) for r in repos):
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            notes["loose_files_outside_repos"] += 1
                    except OSError:
                        note_unreadable(notes, entry.path)
            for entry in entries:
                try:
                    if entry.is_symlink():
                        notes["symlinks_skipped"] += 1
                        continue
                    if not entry.is_dir(follow_symlinks=False) or entry.name in SKIP_DIRS:
                        continue
                except OSError:
                    note_unreadable(notes, entry.path)
                    continue
                real = os.path.realpath(entry.path)
                if any(under(real, ex) for ex in excludes):
                    continue
                if depth + 1 > max_depth:
                    notes["depth_cut"] += 1
                    continue
                stack.append((entry.path, depth + 1))
    return repos, notes


def safe_name(path: str) -> str:
    return "<credential-like name>" if CREDENTIAL_LIKE.search(path) else path


def parse_status(raw: str, nested: set, names_limit: int) -> dict:
    """Counts and a capped, credential-filtered name list from `git status --porcelain=v1 -z`."""
    counts = {"modified": 0, "staged": 0, "untracked": 0, "ignored": 0, "conflicted": 0, "nested_repos": 0}
    names = {"untracked": [], "ignored": [], "changed": []}
    parts = raw.split("\0")
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        xy, path = entry[:2], entry[3:]
        if xy[0] in "RC":
            i += 1
        bare = path.rstrip("/")
        if xy == "??":
            if bare in nested:
                counts["nested_repos"] += 1
                continue
            counts["untracked"] += 1
            bucket = "untracked"
        elif xy == "!!":
            counts["ignored"] += 1
            bucket = "ignored"
        else:
            if "U" in xy or xy in ("AA", "DD"):
                counts["conflicted"] += 1
            if xy[0] not in " ?!":
                counts["staged"] += 1
            if xy[1] not in " ?!":
                counts["modified"] += 1
            bucket = "changed"
        if len(names[bucket]) < names_limit:
            names[bucket].append(safe_name(path))
    return {"counts": counts, "names": names, "names_truncated": any(
        counts[k] > len(names[b]) for k, b in (("untracked", "untracked"), ("ignored", "ignored")))}


FILTER_KEY = re.compile(r"^filter\..+\.(clean|smudge|process)$", re.IGNORECASE)


def inspect_repo(repo: str, nested_rel: set, git_timeout: float, names_limit: int, deadline: float) -> dict:
    info = {"path": repo, "ok": True, "problems": [], "deadline_hit": False}

    def git(args, label):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            info["ok"] = False
            info["deadline_hit"] = True
            if not any("deadline" in p for p in info["problems"]):
                info["problems"].append("whole-run deadline reached; remaining commands not run")
            return None
        try:
            code, out = run_git(repo, args, min(git_timeout, remaining))
        except subprocess.TimeoutExpired:
            info["ok"] = False
            info["problems"].append(label + ": timed out")
            if deadline - time.monotonic() <= 0:
                info["deadline_hit"] = True
                info["problems"].append("whole-run deadline reached; remaining commands not run")
            return None
        except OSError as exc:
            info["ok"] = False
            info["problems"].append(label + ": " + exc.__class__.__name__)
            return None
        return code, out

    r = git(["rev-parse", "--git-dir", "--git-common-dir", "--is-bare-repository"], "layout")
    if r is None or r[0] != 0:
        info["ok"] = False
        info["problems"].append("not readable as a git repository")
        return info
    gd, gcd, bare = (r[1].split("\n") + ["", "", ""])[:3]
    base = os.path.realpath(repo)
    info["linked_worktree"] = os.path.realpath(os.path.join(base, gd)) != os.path.realpath(os.path.join(base, gcd))
    info["bare"] = bare.strip() == "true"
    if info["bare"]:
        return info
    r = git(["symbolic-ref", "--short", "-q", "HEAD"], "branch")
    info["branch"] = r[1].strip() if r and r[0] == 0 else None
    info["detached"] = bool(r) and r[0] != 0
    r = git(["rev-parse", "-q", "--verify", "HEAD"], "head")
    info["head"] = r[1].strip() if r and r[0] == 0 else None
    if info["head"] is None and info["ok"]:
        info["problems"].append("no commits yet")
    r = git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], "upstream")
    info["upstream"] = r[1].strip() if r and r[0] == 0 else None
    info["ahead"] = info["behind"] = None
    if info["upstream"]:
        r = git(["rev-list", "--left-right", "--count", "@{upstream}...HEAD"], "ahead_behind")
        if r and r[0] == 0 and len(r[1].split()) == 2:
            info["behind"], info["ahead"] = (int(x) for x in r[1].split())
    info["upstream_as_of"] = "last fetch (this run never fetches)"
    # `git status` runs a repository's configured clean filter on a changed tracked file, and that program can write.
    # Read only the NAMES of config keys (never values); if a content filter is configured, or the keys cannot be
    # listed, do not run status for this repository and say so in coverage.
    # A parent's status would otherwise recurse into a registered submodule and run the child's filter before the child's
    # own row is checked, so status ignores submodules and each child is observed (or refused) through its own row.
    info["submodules_inspected_by_this_status"] = False
    names = git(["config", "--list", "--name-only"], "config_names")
    filters = [n for n in names[1].split("\n") if FILTER_KEY.match(n.strip())] if names and names[0] == 0 else None
    if names is None or names[0] != 0:
        info["status_skipped"] = "could not tell whether the repository configures a content filter"
        r = None
    elif filters:
        info["status_skipped"] = "the repository configures a content filter that status could run, and it could write"
        r = None
    else:
        r = git(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching",
                "--ignore-submodules=all"], "status")
    if "status_skipped" in info:
        info["ok"] = False
        info["problems"].append("status not run: " + info["status_skipped"])
        info["dirty"] = None
    elif r and r[0] == 0:
        st = parse_status(r[1], nested_rel, names_limit)
        info.update(st)
        c = st["counts"]
        info["dirty"] = bool(c["modified"] or c["staged"] or c["untracked"] or c["conflicted"])
    else:
        info["dirty"] = None
        info["ok"] = False
    if info["linked_worktree"]:
        info["stash_entries"] = None  # the stash belongs to the whole repository; read it on the primary checkout
    else:
        r = git(["rev-list", "-g", "--count", "refs/stash"], "stash_count")
        info["stash_entries"] = int(r[1].strip()) if r and r[0] == 0 and r[1].strip().isdigit() else 0
    return info


def write_receipt(out_dir: str, receipt: dict) -> str:
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    os.chmod(out_dir, 0o700)
    name = "reconcile_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = os.path.join(out_dir, name)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read-only inventory of git repositories under named roots.")
    ap.add_argument("--root", action="append", default=[], help="a directory to scan (repeat; nothing is scanned by default)")
    ap.add_argument("--exclude", action="append", default=[], help="a directory never entered (repeat)")
    ap.add_argument("--out-dir", help="private directory for the new receipt file; must be outside every git repository")
    ap.add_argument("--max-depth", type=int, default=4)
    ap.add_argument("--max-dirs", type=int, default=20000)
    ap.add_argument("--max-repos", type=int, default=200)
    ap.add_argument("--timeout", type=float, default=120.0, help="seconds for the whole run")
    ap.add_argument("--git-timeout", type=float, default=15.0, help="seconds for each git command")
    ap.add_argument("--names-limit", type=int, default=25, help="most path names listed per category (0 = counts only)")
    args = ap.parse_args(argv)
    try:
        roots, excludes, out = validate(args)
    except Refusal as why:
        print("REFUSED: " + str(why), file=sys.stderr)
        return 2
    started = utc_now()
    deadline = time.monotonic() + args.timeout
    repos, notes = discover(roots, excludes, args.max_depth, args.max_dirs, args.max_repos, deadline)
    rel = {os.path.realpath(r) for r in repos}
    entries = []
    for repo in repos:
        if time.monotonic() > deadline:
            notes["timed_out"] = True
            break
        mine = {os.path.relpath(o, repo) for o in rel if o != os.path.realpath(repo) and under(o, os.path.realpath(repo))}
        entries.append(inspect_repo(repo, mine, args.git_timeout, args.names_limit, deadline))
        if entries[-1]["deadline_hit"]:
            notes["timed_out"] = True
    failed = [e["path"] for e in entries if not e.get("ok")]
    unread = len(repos) - len(entries)
    skipped = [e["path"] for e in entries if "status_skipped" in e]
    incomplete = bool(failed or unread or notes["timed_out"] or notes["truncated_dirs"] or notes["truncated_repos"]
                      or notes["unreadable_dirs"])
    receipt = {"tool": "reconcile_local.py", "read_only": True, "started": started, "finished": utc_now(),
               "roots": roots, "excludes": excludes,
               "limits": {"max_depth": args.max_depth, "max_dirs": args.max_dirs, "max_repos": args.max_repos,
                          "timeout_s": args.timeout, "git_timeout_s": args.git_timeout, "names_limit": args.names_limit},
               "coverage": dict(notes, repos_found=len(repos), repos_read=len(entries) - len(failed),
                                repos_failed=failed, repos_status_skipped=skipped, repos_not_reached=unread,
                                complete=not incomplete),
               "repos": entries,
               "work_file_contents_returned": False, "network_used": False,
               "not_read": ["file contents", "remote URLs", "git config values", "credentials"],
               "limitations": ["a point-in-time observation, not a backup",
                               "git status may read tracked files internally; this tool returns none of their contents",
                               "an ignored directory can appear as one path; its contents and value are not assessed",
                               "upstream counts use the last fetched refs, so local-only or remote-only commits may be missing",
                               "files outside any repository are only counted (loose_files_outside_repos), never listed: an unversioned draft or original media there is not inventoried and not backup-safe",
                               "a repository that configures a content filter is not status-scanned (the filter could write), and is listed under repos_status_skipped",
                               "a directory that could not be read makes coverage incomplete and is listed under unreadable_paths",
                               "a repository's status does not look inside its registered submodules; a submodule appears only through its own row, so a dirty child is not shown on its parent",
                               "excluded directories and symlink targets are not inventoried"]}
    path = write_receipt(out, receipt)
    dirty = sum(1 for e in entries if e.get("dirty"))
    print("repos=%d dirty=%d failed=%d complete=%s receipt=%s" % (len(entries), dirty, len(failed), not incomplete, path))
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
