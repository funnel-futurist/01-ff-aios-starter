"""Folder layout moves: Starter 2.x's numbered folders to the 3.0 instance layout.

The map is part of the release (`layout` in release/package_spec.json, copied into the release
record by `release build`), so a founder approves the exact moves with the release.

What it promises:

* **Paths change, bytes never do.** A move is a hard link to the new path, then removing the old
  name. The file's content, mode and timestamps are the same inode before and after. Nothing is
  ever copied, rewritten or merged, so an edited starter file stays exactly as the client left it.
* **Nothing is overwritten.** The plan refuses, with nothing changed, if any destination already
  exists, if two files would land on one path once case and Unicode normalization are ignored
  (macOS and Windows disks treat `Plan.md` and `plan.md` as one file), or if a moved file would
  land on a path the new release ships. The link step itself can't overwrite either: creating a
  link onto an existing name fails.
* **Refused, with the file named:** a symlink, a nested repository or submodule (`.git`), a
  device or pipe, a file on a different disk, or a disk that can't make hard links.
* **Planned before anything moves.** Every file's source, destination, sha256, size and mode,
  every empty folder, and every folder that already existed go into the journal first. A hard
  kill at any instant leaves enough on disk for `rollback` to put each file back.
* **Read back.** After the moves every destination is re-hashed against the plan; any mismatch
  rolls the whole upgrade back.
* **Operating-system junk** (`.DS_Store`, `Thumbs.db`, `desktop.ini`, and only those names) is
  set aside in the upgrade's backup instead of moved, and put back by rollback.
* **References are reported, never edited.** The client's own files that still name an old
  folder are listed after the upgrade. Rewriting them would change the client's bytes.
"""

import os
import re
import stat
import unicodedata

from . import util
from .util import EXIT_STATE, Refusal

DEFAULT_JUNK = (".DS_Store", "Thumbs.db", "desktop.ini")
TEXT_SUFFIXES = (".md", ".txt", ".json", ".yaml", ".yml")
# Folders inside a site that are build output or dependencies, never a site of their own.
SITE_SKIP_DIRS = ("node_modules", ".next", ".vercel", "dist", "build", ".output", ".git")
SITE_MARKERS = ("vercel.json", "package.json", "netlify.toml", "next.config.js", "next.config.mjs",
                "next.config.ts", "astro.config.mjs", "vite.config.js", "vite.config.ts")
# A bare index.html is a site only where the 2.x guide told people to keep sites.
HTML_SITE_ROOTS = ("11_Projects/",)


def version_of(layout):
    return str((layout or {}).get("version") or "2")


def key(rel):
    """The name a case-insensitive, normalization-insensitive disk sees."""
    return unicodedata.normalize("NFC", rel).casefold()


def destination(rel, moves):
    """The new path for one old path (file, or folder ending in '/'), or None. Longest rule wins."""
    best = None
    for move in moves:
        src = move["from"]
        if src.endswith("/"):
            if (rel + "/").startswith(src) and (best is None or len(src) > len(best["from"])):
                best = move
        elif rel == src and (best is None or len(src) > len(best["from"])):
            best = move
    if best is None:
        return None
    src, dst = best["from"], best["to"]
    if not src.endswith("/"):
        return dst
    rest = (rel + "/")[len(src):]
    return (dst + rest).rstrip("/")


def junk_names(layout):
    return tuple(n.casefold() for n in (layout.get("quarantine") or DEFAULT_JUNK))


# ─── scanning ────────────────────────────────────────────────────────────────

def _scan(target, root_rel, dev, problems):
    """Every entry under one old folder: [(rel, kind, lstat)]. kind: file, empty_dir, dir."""
    out = []
    stack = [root_rel]
    while stack:
        d = stack.pop()
        full = os.path.join(target, d)
        try:
            children = sorted(os.scandir(full), key=lambda e: e.name)
        except OSError as exc:
            problems.append("%s: cannot be read (%s)" % (d, exc.strerror or exc))
            continue
        if not children:
            out.append((d, "empty_dir", None))  # the old folder itself, if the client emptied it
        for entry in children:
            rel = d + "/" + entry.name
            st = os.lstat(entry.path)
            if entry.name == ".git":
                problems.append("%s: a nested repository or submodule. Move it out of the old "
                                "folder yourself (it has its own history), commit, then upgrade again"
                                % rel)
                continue
            if stat.S_ISLNK(st.st_mode):
                problems.append("%s: a symbolic link. The move won't follow or recreate links; "
                                "replace it with the real file or remove it, commit, then upgrade again"
                                % rel)
                continue
            if st.st_dev != dev:
                problems.append("%s: on a different disk from the workspace, so it can't be moved "
                                "without copying" % rel)
                continue
            if stat.S_ISDIR(st.st_mode):
                out.append((rel, "dir", st))
                stack.append(rel)
            elif stat.S_ISREG(st.st_mode):
                out.append((rel, "file", st))
            else:
                problems.append("%s: not a regular file (a pipe, socket or device)" % rel)
    return out


def _unsafe_component(target, rel):
    """The first existing component on the way to `rel` that isn't a real folder (a symbolic link
    or a file), or None. A link there would send the moved file outside the workspace."""
    parts = rel.split("/")[:-1]
    for i in range(1, len(parts) + 1):
        full = os.path.join(target, *parts[:i])
        if os.path.islink(full) or (os.path.lexists(full) and not os.path.isdir(full)):
            return "/".join(parts[:i])
    return None


def _case_twins(target, rel):
    """Existing names that a case-insensitive disk would confuse with some component of `rel`."""
    out = []
    parts = rel.split("/")
    for i in range(len(parts)):
        parent = os.path.join(target, *parts[:i]) if i else target
        if not os.path.isdir(parent):
            break
        want = key(parts[i])
        try:
            names = os.listdir(parent)
        except OSError:
            break
        for name in names:
            if name != parts[i] and key(name) == want:
                out.append("/".join(parts[:i] + [name]))
        if parts[i] not in names:
            break
    return out


def link_probe(target):
    """Can this disk make a hard link inside the workspace? Moves depend on it."""
    # Inside the backups folder, which git ignores: a kill mid-probe must not leave a stray file
    # that makes the next upgrade refuse for "uncommitted changes". Every folder it makes is
    # removed again, so a dry run or a refusal leaves nothing behind (independent review).
    backups = os.path.join(target, ".aios", "backups")
    made_backups = not os.path.isdir(backups)
    probe_dir = os.path.join(backups, ".link-probe-%d" % os.getpid())
    os.makedirs(probe_dir, exist_ok=True)
    a = os.path.join(probe_dir, ".link-probe-a")
    b = os.path.join(probe_dir, ".link-probe-b")
    for p in (a, b):
        if os.path.lexists(p):
            os.remove(p)
    try:
        with open(a, "wb") as fh:
            fh.write(b"probe")
        os.link(a, b)
        return True
    except OSError:
        return False
    finally:
        for p in (a, b):
            try:
                os.remove(p)
            except OSError:
                pass
        for d in ([probe_dir, backups] if made_backups else [probe_dir]):
            try:
                os.rmdir(d)
            except OSError:
                pass


# ─── planning ────────────────────────────────────────────────────────────────

def plan(target, layout, old_managed, new_paths):
    """The whole move, decided before anything changes. Refuses, naming every problem.

    old_managed: paths the installed release owns (the release replaces or retires them itself).
    new_paths: {path: class} the new release ships. A moved file may land where the release ships
      a seed (the moved file wins: seeds are only written when absent), never where it ships a
      managed file.
    """
    target = os.path.abspath(target)
    dev = os.lstat(target).st_dev
    moves_rules = layout.get("moves") or []
    junk = junk_names(layout)
    problems = []
    entries = []
    for root in layout.get("retired_roots") or []:
        full = os.path.join(target, root)
        if os.path.islink(full):
            problems.append("%s: the old folder itself is a symbolic link" % root)
            continue
        if not os.path.isdir(full):
            if os.path.lexists(full):
                problems.append("%s: expected a folder, found a file" % root)
            continue
        entries.extend(_scan(target, root, dev, problems))

    managed_keys = {key(p) for p in old_managed}
    new_managed_keys = {key(p): p for p, cls in new_paths.items() if cls == "managed"}
    moves, quarantine, empty_dirs, uncovered = [], [], [], []
    for rel, kind, st in entries:
        if kind == "dir":
            continue
        if kind == "empty_dir":
            dst = destination(rel, moves_rules)
            if dst is None:
                uncovered.append(rel + "/")
            else:
                empty_dirs.append({"from": rel, "to": dst})
            continue
        if key(rel) in managed_keys:
            continue
        name = rel.rsplit("/", 1)[-1]
        rec = {"from": rel, "sha256": util.sha256_file(os.path.join(target, rel)),
               "size": st.st_size, "mode": stat.S_IMODE(st.st_mode)}
        if name.casefold() in junk:
            rec["to"] = rel  # kept under the backup's quarantine/ at the same relative path
            quarantine.append(rec)
            continue
        dst = destination(rel, moves_rules)
        if dst is None:
            uncovered.append(rel)
            continue
        rec["to"] = dst
        moves.append(rec)

    # Destinations: unique once case and normalization are ignored, not already on disk in any
    # spelling, and not a path the release itself ships as a managed file.
    seen = {}
    for m in moves:
        k = key(m["to"])
        if k in seen:
            problems.append("%s and %s would both become %s (a Mac or Windows disk sees one name). "
                            "Rename one, commit, then upgrade again" % (seen[k], m["from"], m["to"]))
            continue
        seen[k] = m["from"]
        bad = _unsafe_component(target, m["to"])
        if bad:
            problems.append("%s would move to %s, but %s is a symbolic link or a file, not a folder. "
                            "Replace it with a real folder, commit, then upgrade again" % (m["from"], m["to"], bad))
            continue
        # The spelling on disk first: a case-insensitive disk also answers "exists" for a twin,
        # and the person needs the name they'll actually see.
        twins = _case_twins(target, m["to"])
        if twins:
            problems.append("%s would move to %s, but %s already exists and differs only in "
                            "capital letters or accents. Nothing is ever overwritten: rename one "
                            "of them, commit, then upgrade again" % (m["from"], m["to"], twins[0]))
            continue
        if os.path.lexists(os.path.join(target, m["to"])):
            problems.append("%s would move to %s, which already exists. Nothing is ever "
                            "overwritten: move or rename one of them, commit, then upgrade again"
                            % (m["from"], m["to"]))
            continue
        if k in new_managed_keys:
            problems.append("%s would move to %s, where the new release ships its own file"
                            % (m["from"], m["to"]))
    for e in empty_dirs:
        bad = _unsafe_component(target, e["to"] + "/x")
        if bad:
            problems.append("empty folder %s would become %s, but %s is a symbolic link or a file"
                            % (e["from"], e["to"], bad))
            continue
        twins = _case_twins(target, e["to"])
        full = os.path.join(target, e["to"])
        if os.path.lexists(full) and not os.path.isdir(full):
            problems.append("empty folder %s would become %s, which is a file" % (e["from"], e["to"]))
        elif twins:
            problems.append("empty folder %s would become %s, but %s already exists"
                            % (e["from"], e["to"], twins[0]))
    if uncovered:
        problems.extend("%s: no rule in the folder map says where it goes" % u for u in uncovered)
    if (moves or quarantine) and not link_probe(target):
        problems.append("this disk can't make hard links, so files can't be moved without copying "
                        "them. Move the workspace to the computer's main disk, then upgrade again")
    if problems:
        raise Refusal(EXIT_STATE, "the 2.x to 3.0 folder move can't run safely; nothing was changed",
                      problems[:40] + (["... %d more" % (len(problems) - 40)] if len(problems) > 40
                                       else []))

    # Every folder a move could create, and whether it already exists, so rollback removes only
    # what the move made.
    pre_dirs = set()
    for path in [m["to"] for m in moves] + [e["to"] + "/x" for e in empty_dirs]:
        parts = path.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            if os.path.isdir(os.path.join(target, d)):
                pre_dirs.add(d)
    return {
        "from": "2",
        "to": version_of(layout),
        "retired_roots": [r for r in layout.get("retired_roots") or []
                          if os.path.isdir(os.path.join(target, r))],
        "moves": moves,
        "quarantine": quarantine,
        "empty_dirs": empty_dirs,
        "pre_dirs": sorted(pre_dirs),
    }


def destinations(the_plan):
    return {key(m["to"]) for m in (the_plan or {}).get("moves") or []}


# ─── applying, reading back, reversing ───────────────────────────────────────

def _same_regular(a, b):
    """Both regular files (not links) and the same inode: the one state a kill between link and
    unlink leaves. `samefile` follows links, so a link pointing at the other name would pass it
    (independent review, round 3)."""
    try:
        sa, sb = os.lstat(a), os.lstat(b)
    except OSError:
        return False
    return (stat.S_ISREG(sa.st_mode) and stat.S_ISREG(sb.st_mode)
            and (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino))


def _link_move(target, src, dst):
    """Give the file its new name, then drop the old one. Never overwrites: link() fails on an
    existing name. Safe to repeat after a kill between the two steps. Never through a link on
    either side: that could reach, or unlink, a file outside the workspace."""
    full_src, full_dst = os.path.join(target, src), os.path.join(target, dst)
    if _unsafe_component(target, src):
        raise Refusal(EXIT_STATE, "the way to %s runs through a link or a file" % src)
    if os.path.lexists(full_dst):
        if os.path.lexists(full_src) and _same_regular(full_src, full_dst):
            os.unlink(full_src)  # killed between link and unlink last time
            return
        if not os.path.lexists(full_src):
            return  # already moved
        raise Refusal(EXIT_STATE, "%s appeared at the destination of %s during the move" % (dst, src))
    if os.path.islink(full_src) or not os.path.isfile(full_src):
        raise Refusal(EXIT_STATE, "%s isn't a regular file any more, so it isn't moved" % src)
    parent = os.path.dirname(full_dst)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    # Checked again at the moment of the move, not only in the plan.
    real_root, real_parent = os.path.realpath(target), os.path.realpath(parent)
    if _unsafe_component(target, dst) or (real_parent != real_root
                                           and not real_parent.startswith(real_root + os.sep)):
        raise Refusal(EXIT_STATE, "the way to %s leaves the workspace or runs through a link" % dst)
    os.link(full_src, full_dst)
    if not os.path.samefile(full_src, full_dst):
        raise Refusal(EXIT_STATE, "linking %s to %s did not produce the same file" % (src, dst))
    util.fault("layout.linked_not_unlinked")  # the one instant both names exist
    os.unlink(full_src)


def quarantine_path(backup_rel, rel):
    return os.path.join(backup_rel, "quarantine", rel).replace(os.sep, "/")


def apply(target, the_plan, backup_rel):
    """Carry out a plan. Every step can be reversed from the plan alone."""
    for i, m in enumerate(the_plan["moves"]):
        _link_move(target, m["from"], m["to"])
        if i == 0:
            util.fault("layout.after_first_move")
        if i == len(the_plan["moves"]) // 2:
            util.fault("layout.mid_moves")
    for q in the_plan["quarantine"]:
        _link_move(target, q["from"], quarantine_path(backup_rel, q["from"]))
    for e in the_plan["empty_dirs"]:
        os.makedirs(os.path.join(target, e["to"]), exist_ok=True)
    remove_emptied(target, the_plan)
    util.fault("layout.after_moves")


def remove_emptied(target, the_plan, also=()):
    """Remove the old folders once empty, deepest first. A folder that still holds anything stays,
    and the leftovers check fails the upgrade. `also`: other files just removed under them."""
    olds = set()
    for path in [rec["from"] for rec in the_plan["moves"] + the_plan["quarantine"]] + list(also):
        parts = path.split("/")[:-1]
        olds.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    for e in the_plan["empty_dirs"]:
        parts = e["from"].split("/")
        olds.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    for d in sorted(olds, key=lambda p: -p.count("/")):
        full = os.path.join(target, d)
        try:
            if os.path.isdir(full) and not os.path.islink(full) and not os.listdir(full):
                os.rmdir(full)
        except OSError:
            pass


def _pairs(the_plan, backup_rel):
    """(record, where it is after the move) for every moved and set-aside file."""
    return ([(m, m["to"]) for m in the_plan["moves"]]
            + [(q, quarantine_path(backup_rel, q["from"])) for q in the_plan["quarantine"]])


def readback(target, the_plan, backup_rel):
    """Re-hash every moved file at its new path. Returns problems; empty means the bytes held."""
    problems = []
    for rec, dst in _pairs(the_plan, backup_rel):
        full = os.path.join(target, dst)
        if not os.path.isfile(full) or os.path.islink(full):
            problems.append("%s is missing after the move (from %s)" % (dst, rec["from"]))
            continue
        st = os.lstat(full)
        if st.st_size != rec["size"] or stat.S_IMODE(st.st_mode) != rec["mode"]:
            problems.append("%s changed size or mode in the move" % dst)
            continue
        if util.sha256_file(full) != rec["sha256"]:
            problems.append("%s does not hash to what %s held" % (dst, rec["from"]))
        if os.path.lexists(os.path.join(target, rec["from"])):
            problems.append("%s is still at its old path after the move" % rec["from"])
    for e in the_plan["empty_dirs"]:
        if not os.path.isdir(os.path.join(target, e["to"])):
            problems.append("empty folder %s was not recreated as %s" % (e["from"], e["to"]))
    return problems


def leftovers(target, the_plan):
    """Anything still under an old folder after the moves and the release's own removals."""
    out = []
    for root in the_plan.get("retired_roots") or []:
        base = os.path.join(target, root)
        if not os.path.lexists(base):
            continue
        here = []
        for dirpath, dirnames, filenames in os.walk(base):
            for name in filenames + [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]:
                here.append(os.path.relpath(os.path.join(dirpath, name), target).replace(os.sep, "/"))
        out.extend(here or [root + "/ (an empty folder the move couldn't remove)"])
    return sorted(out)


def reverse_conflicts(target, the_plan, backup_rel):
    """Old paths that something else now occupies. Checked before rollback changes anything."""
    out = []
    for rec, dst in _pairs(the_plan, backup_rel):
        full_src, full_dst = os.path.join(target, rec["from"]), os.path.join(target, dst)
        if os.path.islink(full_src) or os.path.islink(full_dst):
            out.append(rec["from"] if os.path.islink(full_src) else dst)  # never act through a link
        elif os.path.lexists(full_src) and os.path.lexists(full_dst) \
                and not _same_regular(full_src, full_dst):
            out.append(rec["from"])
    # An empty folder comes back as a folder: a file at its old path, or at any folder on the way
    # to it, would stop that halfway through the rollback (independent review, round 1).
    for e in the_plan.get("empty_dirs") or []:
        parts = e["from"].split("/")
        for i in range(1, len(parts) + 1):
            full = os.path.join(target, *parts[:i])
            if os.path.islink(full) or (os.path.lexists(full) and not os.path.isdir(full)):
                out.append("/".join(parts[:i]))
                break
    for rec, _dst in _pairs(the_plan, backup_rel):
        bad = _unsafe_component(target, rec["from"])  # a link on the way counts: never follow one
        if bad:
            out.append(bad)
    return sorted(set(out))


def reverse(target, the_plan, backup_rel):
    """Put every moved file back at its old path, from any point of an interrupted move or after
    a finished one. A file the client edited since goes back with their edits; one they deleted
    stays deleted; one whose old path is now occupied is refused before anything changes."""
    blocked = reverse_conflicts(target, the_plan, backup_rel)
    if blocked:
        raise Refusal(EXIT_STATE, "putting the folders back would overwrite %d file(s)" % len(blocked),
                      sorted(blocked)[:20] + ["move those aside, then run rollback again"])
    for e in the_plan["empty_dirs"]:
        os.makedirs(os.path.join(target, e["from"]), exist_ok=True)
    for q in reversed(the_plan["quarantine"]):
        if os.path.lexists(os.path.join(target, quarantine_path(backup_rel, q["from"]))):
            _link_move(target, quarantine_path(backup_rel, q["from"]), q["from"])
    for m in reversed(the_plan["moves"]):
        if os.path.lexists(os.path.join(target, m["to"])):
            _link_move(target, m["to"], m["from"])
        # else: back already, or the client deleted it after the upgrade: deleted stays deleted
    # Folders the move created, now empty again. A folder the client has since put work in stays.
    pre = set(the_plan.get("pre_dirs") or [])
    made = set()
    for path in [m["to"] for m in the_plan["moves"]] + [e["to"] + "/x" for e in the_plan["empty_dirs"]]:
        parts = path.split("/")[:-1]
        made.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    for d in sorted(made - pre, key=lambda p: -p.count("/")):
        full = os.path.join(target, d)
        try:
            if os.path.isdir(full) and not os.listdir(full):
                os.rmdir(full)
        except OSError:
            pass


def proof(target, the_plan, backup_rel):
    """What the client can check: each file's old path, new path and the hash it kept."""
    return {
        "schema": "ff-aios-starter/layout-proof@1",
        "layout": {"from": the_plan["from"], "to": the_plan["to"]},
        "statement": "every file below kept its exact bytes (sha256), size and mode; only its path "
                     "changed. Junk files were set aside in the backup, not moved.",
        "moved": [{"from": m["from"], "to": m["to"], "sha256": m["sha256"], "size": m["size"]}
                  for m in the_plan["moves"]],
        "set_aside": [{"from": q["from"], "kept_at": quarantine_path(backup_rel, q["from"]),
                       "sha256": q["sha256"]} for q in the_plan["quarantine"]],
        "empty_folders": the_plan["empty_dirs"],
        "readback": "every destination re-hashed after the move: %d of %d matched"
                    % (len(the_plan["moves"]) + len(the_plan["quarantine"]),
                       len(the_plan["moves"]) + len(the_plan["quarantine"])),
    }


# ─── reporting ───────────────────────────────────────────────────────────────

def stale_references(target, layout, skip_paths=()):
    """The client's own text files that still name an old folder. Reported, never rewritten."""
    roots = layout.get("retired_roots") or []
    if not roots:
        return []
    pattern = re.compile(r"\b(%s)\b" % "|".join(re.escape(r) for r in roots))
    skip = set(skip_paths)
    out = []
    for dirpath, dirnames, filenames in os.walk(target):
        rel_dir = os.path.relpath(dirpath, target).replace(os.sep, "/")
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")
                       and not (rel_dir == "." and d == ".aios")]
        for name in filenames:
            if not name.endswith(TEXT_SUFFIXES):
                continue
            rel = os.path.normpath(os.path.join(rel_dir, name)).replace(os.sep, "/")
            if rel in skip:
                continue
            try:
                with open(os.path.join(target, rel), encoding="utf-8", errors="replace") as fh:
                    if pattern.search(fh.read()):
                        out.append(rel)
            except OSError:
                continue
    return sorted(out)


def sites(target, the_plan, layout):
    """Folders the move relocates that look like a deployed website: [{from, to, vercel}].

    `vercel` is the folder's `.vercel/project.json` link ({projectId, orgId}) when it has one.
    """
    marked = set()
    for rec in the_plan["moves"]:
        parts = rec["from"].split("/")
        if any(p in SITE_SKIP_DIRS for p in parts[:-1]):
            if not (len(parts) >= 3 and parts[-2] == ".vercel" and parts[-1] == "project.json"):
                continue
        name = parts[-1]
        folder = "/".join(parts[:-1])
        if name in SITE_MARKERS:
            marked.add(folder)
        elif name == "index.html" and any(rec["from"].startswith(r) for r in HTML_SITE_ROOTS):
            marked.add(folder)
        elif name == "project.json" and len(parts) >= 3 and parts[-2] == ".vercel":
            marked.add("/".join(parts[:-2]))
    marked.discard("")
    outer = sorted(f for f in marked if not any(f.startswith(o + "/") for o in marked if o != f))
    out = []
    for folder in outer:
        to = destination(folder, layout.get("moves") or [])
        link = None
        pj = os.path.join(target, folder, ".vercel", "project.json")
        if os.path.isfile(pj):
            try:
                data = util.read_json(pj)
                link = {"projectId": data.get("projectId"), "orgId": data.get("orgId")}
            except (OSError, ValueError):
                link = {"projectId": None, "orgId": None}
        out.append({"from": folder, "to": to, "vercel": link})
    return out


def vercel_files(the_plan):
    """Files in the moving folders that show Vercel deploys from here (vercel.json, .vercel/)."""
    return sorted(m["from"] for m in the_plan["moves"]
                  if m["from"].rsplit("/", 1)[-1] == "vercel.json" or "/.vercel/" in "/" + m["from"])


# ─── the instance contract (workspace kind) ─────────────────────────────────

DOMAIN_FOLDERS = ("00_AIOS", "01_Creation", "02_Team_Ops", "03_RevOps", "04_Attention",
                  "05_Jobs", "99_Archive")
OLD_FOLDERS = ("01_Foundations", "02_Deliverables", "03_Quality_Control", "04_Customer_Journey",
               "05_Assets", "06_Communication", "07_Setup", "08_Automations", "09_Archive",
               "10_Departments", "11_Projects")
BASELINE = (  # control id, path, what it is
    ("B1", "README.md", "the quick start"),
    ("B2", "CLAUDE.md", "the instructions Claude reads"),
    ("B3", "estate.yaml", "this repository's registry row"),
    ("B4", ".github/CODEOWNERS", "who reviews the founder-only files"),
    ("B5", "SETUP.md", "setup: access, secrets, reviewer, hosting, first-run checks"),
    ("B11", "REPO_CONTEXT.md", "what this repository is and why it's separate"),
)


def instance_checks(target):
    """The workspace-kind controls that can be checked from the files alone.

    Returns [(control, status, detail)], status PASS / FAIL / FLAG / INFO. Read-only.
    Founder review (whether GitHub enforces it at the new paths) is a separate check, because it
    needs GitHub: governance.founder_review.
    """
    out = []
    for control, rel, what in BASELINE:
        ok = os.path.isfile(os.path.join(target, rel))
        out.append((control, "PASS" if ok else "FAIL",
                    "%s (%s)%s" % (rel, what, "" if ok else ": missing")))
    decisions = os.path.join(target, "docs", "decisions")
    has_adr = os.path.isdir(decisions) and any(n.endswith(".md") for n in os.listdir(decisions))
    out.append(("B11", "PASS" if has_adr else "FAIL", "docs/decisions/ holds the decision notes"))
    row = os.path.join(target, "estate.yaml")
    if os.path.isfile(row):
        with open(row, encoding="utf-8") as fh:
            text = fh.read()
        kind_ok = re.search(r'^kind_target:\s*"?instance"?', text, re.M) is not None
        named = re.search(r'^repo:\s*"?([^"\s#]+)', text, re.M)
        out.append(("B3", "PASS" if kind_ok else "FAIL", "estate.yaml says kind_target: instance"))
        out.append(("B3", "PASS" if named else "FLAG",
                    "estate.yaml names this repository" if named
                    else "estate.yaml has no repo name yet: fill it in (SETUP.md step 2)"))
    pointer = os.path.join(target, ".ff", "system.json")
    out.append(("B3", "PASS" if os.path.isfile(pointer) else "INFO",
                ".ff/system.json (the registry pointer)" if os.path.isfile(pointer)
                else ".ff/system.json not present: the provider's bootstrap writes it when the "
                     "repository is registered"))
    missing = [d for d in DOMAIN_FOLDERS if not os.path.isdir(os.path.join(target, d))]
    out.append(("workspace", "FAIL" if missing else "PASS",
                "the seven domain folders" + (": missing %s" % ", ".join(missing) if missing else "")))
    old = [d for d in OLD_FOLDERS if os.path.lexists(os.path.join(target, d))]
    out.append(("workspace", "FAIL" if old else "PASS",
                "no Starter 2.x folders left" + (": %s still there" % ", ".join(old) if old else "")))
    out.append(("workspace", "INFO", "only this company's material is here: a person or the "
                "boundary review confirms it; the files alone can't prove it"))
    return out
