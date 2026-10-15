"""Install, verify, upgrade, rollback.

The whole design rests on one boundary:

* **managed** files belong to the release. The installer writes them, upgrade replaces them,
  rollback restores them, and `verify` re-hashes them. If you edit one, the workspace is
  *dirty* and upgrade refuses until you deal with it.
* **seed** files are yours the moment they land: `CLAUDE.md`, your foundations, your
  deliverables, your logs. Seeded once if absent, then **never touched again** by any
  lifecycle operation. This is what "upgrade preserves state" actually means.
* **everything else you create** is invisible to the installer. It is not in the manifest,
  so no operation can delete or overwrite it.

Verification is always **readback**: re-hash what is on disk and compare it to the manifest.
The installer reporting "done" proves nothing; the bytes on disk are the evidence.

Crash safety: every mutation runs inside a transaction that writes a journal *before*
touching anything and snapshots the managed files it is about to replace. A hard kill leaves
the journal on disk, and `rollback` uses it to put the workspace back. Recovery that has only
been tested against a clean exception is not recovery.
"""

import difflib
import json
import os
import re
import shutil
import stat
import time

from . import governance, hosting, layout as layout_mod, orgconfig, release as release_mod, roles, util
from .util import (EXIT_GOVERNANCE, EXIT_PACKAGE, EXIT_STATE, EXIT_VERIFY, Refusal, sha256_bytes,
                   sha256_file)

INSTALL_SCHEMA = "ff-aios-starter/install@1"
AIOS_DIR = ".aios"
INSTALL_PATH = os.path.join(AIOS_DIR, "install.json")
JOURNAL_PATH = os.path.join(AIOS_DIR, "txn.json")
BACKUP_DIR = os.path.join(AIOS_DIR, "backups")
LAYOUT_PLAN = "layout_plan.json"
LAYOUT_PROOF = "layout_proof.json"


# ─── records ────────────────────────────────────────────────────────────────

def install_record_path(target):
    return os.path.join(target, INSTALL_PATH)


def load_record(target):
    path = install_record_path(target)
    if not os.path.isfile(path):
        raise Refusal(EXIT_STATE, "no install record at %s; this workspace was never installed "
                                  "from a release" % path)
    return util.read_json_safe(path, "install record")


def journal_path(target):
    return os.path.join(target, JOURNAL_PATH)


LOCK_PATH = os.path.join(AIOS_DIR, "lock")


class _Lock(object):
    """An exclusive lock for the duration of a mutation.

    The journal already makes a half-finished upgrade recoverable, but it is written *after*
    the workspace has been verified clean. Two upgrades started in the same second would both
    pass verification and then interleave their writes. `O_CREAT | O_EXCL` is atomic on every
    filesystem worth supporting, so the second one refuses instead of racing.

    A stale lock (the holder was killed) is recoverable: the message says how, and `rollback`
    clears it, because a lock that can wedge a workspace forever is its own outage.
    """

    def __init__(self, target, op):
        self.target = target
        self.path = os.path.join(target, LOCK_PATH)
        self.op = op
        self.fd = None

    def __enter__(self):
        util.ensure_parent(self.path)
        # Taken under the workspace guard, so it can't land between a recovery's "this lock is
        # dead" and its removal (independent review, round 10).
        with _RecoveryGuard(self.target):
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except OSError:
                holder = ""
                try:
                    with open(self.path) as fh:
                        holder = fh.read().strip()
                except OSError:
                    pass
                raise Refusal(
                    EXIT_STATE,
                    "another %s is already running in this workspace" % self.op,
                    [("lock held by: %s" % holder) if holder else "lock file: %s" % self.path,
                     "if nothing is running, the previous attempt was killed: run `aios rollback`, "
                     "or delete %s once you are sure" % LOCK_PATH],
                )
            words = ("%s pid=%d at %s\n" % (self.op, os.getpid(), util.now_iso())).encode("utf-8")
            os.write(self.fd, words)
            st = os.fstat(self.fd)
            self.ident = (st.st_dev, st.st_ino, words)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.fd is not None:
                os.close(self.fd)
            # Only our own lock: if something replaced it, removing that would let a third
            # operation in alongside the one that holds it now (independent review). Checked and
            # removed under the guard, so nothing can take its place in between.
            with _RecoveryGuard(self.target):
                if _still_this_lock(self.path, getattr(self, "ident", None)):
                    os.remove(self.path)
        except (OSError, Refusal):
            pass
        return False


def _still_this_lock(path, ident):
    """Whether the lock at `path` is still the one identified as (device, inode, its words).

    The inode alone doesn't say: Linux hands a freed inode number to the next new file at once, so
    a lock replaced after we looked can carry the old one's inode (CI on Linux caught it). Its words
    (operation, pid, time) still differ."""
    if not ident:
        return False
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return False
    try:
        st = os.fstat(fd)
        return (st.st_dev, st.st_ino, os.read(fd, 4096)) == ident
    finally:
        os.close(fd)


def load_journal(target):
    path = journal_path(target)
    if os.path.isfile(path):
        return util.read_json_safe(path, "transaction journal")
    return None


# ─── verification ───────────────────────────────────────────────────────────

# Windows keeps no executable bit (git there doesn't either), so it is only compared where it exists.
_EXEC_BITS = os.name != "nt"

def verify(target, record=None, source_repo=None):
    """Readback. Returns (problems, summary).

    Two different questions, and it matters which one you asked:

    * without `source_repo`: "does this workspace still match **what was installed**?" The
      answer comes from `.aios/install.json`, which lives in the workspace.
    * with `source_repo`: "...and does that record still match **the pinned release**?" The
      hashes are re-derived from the git tree at the pinned commit.

    The first is circular against a determined local editor: change a managed file, change
    its hash in the record, and the readback agrees with itself. A review found exactly that.
    The record is not a security boundary - it is in the operator's own repo - so the fix is
    to make the stronger check available and to say plainly which one ran.
    """
    record = record or load_record(target)
    problems = []
    checked = 0
    summary_pin = None
    if source_repo:
        rel = record.get("release") or {}
        rev = rel.get("git_rev")
        if not rev or not util.rev_exists(source_repo, rev):
            problems.append("cannot cross-check: commit %s is not in %s" % (rev, source_repo))
        else:
            pinned, pinned_exec = {}, {}
            for path, mode, data in util.read_tree(source_repo, rev):
                pinned[path] = sha256_bytes(data)
                pinned_exec[path] = mode == "100755"
            for entry in record.get("managed") or []:
                want = pinned.get(entry["path"])
                if want is None:
                    problems.append("install record claims %s, which is not in the pinned "
                                    "release" % entry["path"])
                elif want != entry["sha256"]:
                    problems.append("install record for %s does not match the pinned release "
                                    "(record %s, release %s)"
                                    % (entry["path"], entry["sha256"][:12], want[:12]))
                elif _EXEC_BITS:
                    # The record's own exec field is the operator's to edit, like its hashes; the
                    # pinned tree is not (independent review).
                    full = os.path.join(target, entry["path"])
                    on_disk = (os.path.isfile(full) and not os.path.islink(full)
                               and bool(os.lstat(full).st_mode & 0o100))
                    if ("exec" in entry and entry["exec"] != pinned_exec[entry["path"]]) or (
                            os.path.isfile(full) and on_disk != pinned_exec[entry["path"]]):
                        problems.append("executable permission of %s does not match the pinned "
                                        "release" % entry["path"])
            # The record's list is the operator's to edit too: drop a file and its entry and the
            # per-entry checks above have nothing to say. The release's own file set at the pin
            # is the list (independent review).
            try:
                want_managed = {p for p, c, _m, _s in release_mod.select_files(
                    source_repo, rev, release_mod.load_spec(source_repo, rev)) if c == "managed"}
            except Refusal as exc:
                problems.append("cannot derive the release's files at %s: %s" % (rev[:12], exc.message))
                want_managed = None
            if want_managed is not None and record.get("adoption"):
                want_managed = {p for p in want_managed
                                if _adoption_class(record["adoption"], p) == "adopt"}
            if want_managed is not None:
                listed = {e["path"] for e in record.get("managed") or []}
                for path in sorted(want_managed - listed):
                    problems.append("the pinned release manages %s, but the install record doesn't "
                                    "list it" % path)
            # And the pin itself: the source's own record of this release names it.
            summary_pin = _pin_confirmation(source_repo, rel.get("release_id"), rev, problems)
    for entry in record.get("managed") or []:
        path = os.path.join(target, entry["path"])
        if not os.path.isfile(path):
            problems.append("missing managed file: %s" % entry["path"])
            continue
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            problems.append("managed file replaced by a link or something else: %s" % entry["path"])
            continue
        actual = sha256_file(path)
        checked += 1
        if actual != entry["sha256"]:
            problems.append("modified managed file: %s (on disk %s, release %s)"
                            % (entry["path"], actual[:12], entry["sha256"][:12]))
        # Permissions: only what git itself keeps (the executable bit), so a teammate's clone with
        # another umask still verifies; and never setuid, setgid or sticky (independent review).
        if st.st_mode & 0o7000:
            problems.append("managed file gained setuid, setgid or sticky permissions: %s" % entry["path"])
        elif _EXEC_BITS and "exec" in entry and bool(st.st_mode & 0o100) != entry["exec"]:
            problems.append("managed file's executable permission changed: %s" % entry["path"])
    for entry in record.get("rendered") or []:
        if not os.path.isfile(os.path.join(target, entry["path"])):
            problems.append("missing rendered file: %s" % entry["path"])
    for entry in record.get("seeded") or []:
        if not os.path.isfile(os.path.join(target, entry["path"])):
            # Seeds are yours, including the right to delete them. Report, never fail.
            pass
    summary = {
        "release_id": (record.get("release") or {}).get("release_id"),
        "version": (record.get("release") or {}).get("version"),
        "managed_checked": checked,
        "managed_total": len(record.get("managed") or []),
        "pin_confirmed_by": summary_pin,
    }
    return problems, summary


def _pin_confirmation(source_repo, release_id, rev, problems):
    """Where the source records this release's pin (the release's tag, then the checked-out
    tree), or None when it has no record of it. A record naming another pin is a problem: the
    install record's pin was edited, or it is not this release."""
    if not release_id or not re.match(r"^starter-[0-9][A-Za-z0-9.+-]*$", release_id):
        return None
    for ref in ("refs/tags/%s" % release_id, "HEAD"):
        text = util.git(source_repo, ["show", "%s:releases/%s.json" % (ref, release_id)], check=False)
        if not text:
            continue
        try:
            pin = (json.loads(text).get("created_from") or {}).get("git_rev")
        except ValueError:
            continue
        where = "%s:releases/%s.json" % ("tag " + release_id if ref != "HEAD" else "HEAD", release_id)
        if pin != rev:
            problems.append("the install record pins %s, but %s pins %s"
                            % ((rev or "?")[:12], where, (pin or "?")[:12]))
        return where
    return None


def require_verified(target, record=None, what="workspace"):
    problems, summary = verify(target, record)
    if problems:
        raise Refusal(EXIT_VERIFY, "%s does not match its installed release" % what, problems)
    return summary


def state_fingerprint(target):
    """Hash every file that is NOT owned by the release.

    Used by the tests to prove an upgrade and a rollback left state untouched: managed files
    change by design, everything else must be byte-identical afterwards.
    """
    record = load_record(target)
    managed = {e["path"] for e in record.get("managed") or []}
    out = {}
    skip_dirs = {".git", os.path.join(AIOS_DIR, "backups")}
    for root, dirs, files in os.walk(target):
        rel_root = os.path.relpath(root, target)
        rel_root = "" if rel_root == "." else rel_root
        dirs[:] = [d for d in dirs
                   if os.path.join(rel_root, d) not in skip_dirs and d != ".git"]
        for name in files:
            rel = os.path.normpath(os.path.join(rel_root, name)) if rel_root else name
            rel = rel.replace(os.sep, "/")
            if rel in managed or rel in (INSTALL_PATH, JOURNAL_PATH, LOCK_PATH):
                continue
            if rel.startswith(BACKUP_DIR.replace(os.sep, "/")):
                continue
            out[rel] = sha256_file(os.path.join(target, name) if not rel_root
                                   else os.path.join(target, rel))
    return out


# ─── transactions ───────────────────────────────────────────────────────────

def _backup(target, record, txn_id):
    """Snapshot the managed files and the install record before mutating either."""
    backup_root = os.path.join(target, BACKUP_DIR, txn_id)
    files_root = os.path.join(backup_root, "files")
    for entry in record.get("managed") or []:
        src = os.path.join(target, entry["path"])
        if not os.path.isfile(src):
            continue
        dst = os.path.join(files_root, entry["path"])
        util.ensure_parent(dst)
        shutil.copy2(src, dst)
    util.write_json(os.path.join(backup_root, "install.json"), record)
    return backup_root


def _identical_regular(src, dest):
    """Both regular files (lstat: a link never counts), same bytes, same permission bits."""
    try:
        a, b = os.lstat(src), os.lstat(dest)
    except OSError:
        return False
    return (stat.S_ISREG(a.st_mode) and stat.S_ISREG(b.st_mode)
            and stat.S_IMODE(a.st_mode) == stat.S_IMODE(b.st_mode)
            and sha256_file(src) == sha256_file(dest))


def _restore_preflight(target, backup_root, record_to_restore, remove_paths, expected=None):
    """Every refusal a restore can make, made before anything changes. Rollback runs it before
    writing its own journal, so a refusal leaves the workspace exactly as it was."""
    # Every path this restore writes OR removes: removing through a link would delete a file
    # outside the workspace (independent review, round 4).
    linked = _linked_paths(target, [e["path"] for e in record_to_restore.get("managed") or []]
                           + list(remove_paths))
    if linked:
        raise Refusal(EXIT_STATE, "restoring would go through %d link(s) or file(s) in the way"
                      % len(linked), linked[:20] + ["replace them with real folders, then run rollback again"])
    folders = [e["path"] for e in record_to_restore.get("managed") or []
               if os.path.isdir(os.path.join(target, e["path"]))
               and not os.path.islink(os.path.join(target, e["path"]))]
    if folders:  # copying onto a folder would put the file inside it
        raise Refusal(EXIT_STATE, "restoring would put %d file(s) where a folder now is" % len(folders),
                      folders[:20] + ["move those folders aside, then run rollback again"])
    if expected is not None:
        files_root = os.path.join(backup_root, "files")
        collisions = []
        for entry in record_to_restore.get("managed") or []:
            rel = entry["path"]
            dest = os.path.join(target, rel)
            if rel in expected or not os.path.lexists(dest):
                continue
            src = os.path.join(files_root, rel)
            if _identical_regular(src, dest):
                continue  # identical; restoring it changes nothing (and it isn't touched)
            collisions.append(rel)
        if collisions:
            raise Refusal(
                EXIT_STATE,
                "restoring would overwrite %d file(s) this workspace does not manage"
                % len(collisions),
                sorted(collisions)[:20]
                + ["these paths were freed by a later release and now hold your own work",
                   "move them aside, then run rollback again"],
            )


def _restore(target, backup_root, record_to_restore, remove_paths, expected=None,
             write_record=True, keep_dirs=None, provenance=None):
    """Put the backed-up managed files back.

    `write_record=False` leaves the install record to the caller, which writes it last, once every
    other reversal is done: a kill in between must leave the record still describing what's on
    disk. `keep_dirs`: folders that existed before the operation, never pruned. `provenance`
    ({path: [sha256, mode]}): files removed only if they're still exactly what was written.
    Returns notes about anything left alone.

    `expected` is the set of paths this restore is allowed to overwrite: what the current
    release manages, plus anything the interrupted operation created. Anything else at a
    restore path is the operator's, created after the release stopped owning that path, and
    overwriting it silently is state loss - so it is refused instead.
    """
    _restore_preflight(target, backup_root, record_to_restore, remove_paths, expected)
    notes = []
    provenance = provenance or {}
    for rel in remove_paths:
        if rel in provenance:
            sha, mode = provenance[rel]
            note = _remove_if_ours(target, rel, sha, mode)
            if note:
                notes.append(note)
            continue
        path = os.path.join(target, rel)
        if os.path.islink(path) or os.path.isfile(path):
            os.remove(path)
    files_root = os.path.join(backup_root, "files")
    for entry in record_to_restore.get("managed") or []:
        src = os.path.join(files_root, entry["path"])
        dst = os.path.join(target, entry["path"])
        if os.path.isfile(src):
            if expected is not None and entry["path"] not in expected and _identical_regular(src, dst):
                continue  # not ours now, and already exactly the release's copy: leave it be
            util.ensure_parent(dst)
            if os.path.islink(dst):
                os.remove(dst)  # copying onto a link would write wherever it points
            shutil.copy2(src, dst)
    if write_record:
        util.write_json(install_record_path(target), record_to_restore)
    _prune_parents(target, remove_paths, keep_dirs)
    return notes


def _linked_paths(target, rels):
    """Paths rollback would write whose way there runs through a link or a file (a client folder
    turned into a link after the upgrade would send the restored file outside the workspace).
    Checked before anything changes (independent review)."""
    out = []
    for rel in rels:
        parts = rel.replace(os.sep, "/").split("/")
        for i in range(1, len(parts)):
            full = os.path.join(target, *parts[:i])
            if os.path.islink(full) or (os.path.lexists(full) and not os.path.isdir(full)):
                out.append("/".join(parts[:i]))
                break
    return sorted(set(out))


def _remove_if_ours(target, rel, sha=None, mode=None):
    """Remove a file this operation wrote, and only if it still is what it wrote: a regular file
    (not a link) with the recorded bytes and mode. Anything else is left alone and reported: it
    may be the client's (independent review). Returns a note, or None."""
    full = os.path.join(target, rel)
    if not os.path.lexists(full):
        return None
    if os.path.islink(full) or not os.path.isfile(full):
        return "%s isn't the file the upgrade wrote (a link or a folder now), so it was left" % rel
    if sha and sha256_file(full) != sha:
        return "%s changed since the upgrade wrote it, so it was left for you" % rel
    if mode is not None and stat.S_IMODE(os.lstat(full).st_mode) != mode:
        return "%s changed permissions since the upgrade wrote it, so it was left for you" % rel
    os.remove(full)
    return None


def _prune_parents(target, paths, keep=None):
    """Remove the folders that removing `paths` left empty, deepest first.

    Only those, and never one in `keep` (folders that existed before the operation, even if
    empty: a client's own empty folder). Until 3.0 this walked the whole workspace and removed
    every empty folder in it, so a rollback could not restore them.
    """
    keep = set(keep or ())
    dirs = set()
    for rel in paths:
        parts = rel.replace(os.sep, "/").split("/")[:-1]
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    for d in sorted(dirs, key=lambda p: -p.count("/")):
        if d.split("/")[0] == ".git" or d in keep:
            continue
        full = os.path.join(target, d)
        try:
            if os.path.isdir(full) and not os.path.islink(full) and not os.listdir(full):
                os.rmdir(full)
        except OSError:
            pass


# ─── install ────────────────────────────────────────────────────────────────

def install(target, manifest, source_repo, config, aios_lookup=None, render_governance=True):
    """Install an approved, pinned release into a clean target. Verified by readback."""
    release_mod.require_consumable(manifest, source_repo, aios_lookup)
    orgconfig.require_valid(config)

    if os.path.lexists(install_record_path(target)):
        raise Refusal(EXIT_STATE, "this workspace already has an install record; use upgrade",
                      [install_record_path(target)])
    if load_journal(target):
        raise Refusal(EXIT_STATE, "a previous operation did not finish; run rollback first",
                      [journal_path(target)])

    files = {e["path"]: e for e in manifest.get("files") or []}
    managed_paths = [p for p, e in files.items() if e["class"] == "managed"]
    occupied = [p for p in managed_paths if os.path.lexists(os.path.join(target, p))]
    if occupied:
        raise Refusal(
            EXIT_STATE,
            "target is not a clean environment: %d managed path(s) already exist" % len(occupied),
            sorted(occupied)[:20],
        )

    creds = orgconfig.resolve(manifest.get("credentials"), config, target)
    orgconfig.require_resolved(creds)

    managed, seeded, rendered = [], [], []
    template_text = None
    # Everything that can refuse happens before the first write: rendering CODEOWNERS can refuse an
    # incomplete owners map, and must not leave a half-installed target (independent review).
    template_path = manifest.get("render_template") or "templates/governance/CODEOWNERS.template"
    owners_text = None
    if render_governance and (config.get("code_owners") or {}):
        for path, _mode, data in util.read_tree(source_repo, manifest["created_from"]["git_rev"]):
            if path == template_path and path in files:
                owners_text = governance.render(data.decode("utf-8"), config["repository"],
                                                config["code_owners"])
                break
    if owners_text is not None:
        # What GitHub would ignore must not install "successfully" (independent review).
        problems = governance.check_text(owners_text, ".github/CODEOWNERS", target,
                                         config["repository"], config)
        if problems:
            raise Refusal(EXIT_GOVERNANCE, "the rendered CODEOWNERS would not enforce anything",
                          problems)
        # The client's own CODEOWNERS is theirs: replacing it, or shadowing it from a location
        # GitHub reads first, would change who reviews what without a word.
        theirs = [rel for rel in governance.LOCATIONS if os.path.lexists(os.path.join(target, rel))]
        if theirs:
            raise Refusal(EXIT_STATE, "this workspace already has a CODEOWNERS file",
                          theirs + ["move it aside and install again, or install without "
                                    "code_owners in the config and keep yours"])
    config_path = orgconfig.default_config_path(target)
    if os.path.lexists(config_path):
        same = False
        if os.path.isfile(config_path) and not os.path.islink(config_path):
            try:
                same = util.read_json(config_path) == config
            except (ValueError, OSError, Refusal):
                same = False
        if not same:
            raise Refusal(EXIT_STATE, "this workspace already has a different organization config",
                          [config_path, "install with --config pointing at it, or move it aside"])
    written = [p for p, e in files.items() if e["class"] == "managed"
               or not os.path.lexists(os.path.join(target, p))]
    written += [".github/CODEOWNERS"] if owners_text is not None else []
    written += [os.path.relpath(config_path, target), os.path.relpath(install_record_path(target), target)]
    linked = _linked_paths(target, written)
    if linked:
        raise Refusal(EXIT_STATE, "install would write through a link or a file in a folder's place",
                      linked[:20])
    for path, mode, data in util.read_tree(source_repo,
                                           manifest["created_from"]["git_rev"]):
        entry = files.get(path)
        if entry is None:
            continue
        if entry["sha256"] != sha256_bytes(data):
            raise Refusal(EXIT_PACKAGE, "content at the pin does not match the manifest: %s" % path)
        if path == template_path:
            template_text = data.decode("utf-8")
        dest = os.path.join(target, path)
        if entry["class"] == "seed" and os.path.lexists(dest):
            # Yours already; never overwritten. Recorded as a seed, as an upgrade records one, so
            # the next upgrade knows it's yours rather than refusing it as a collision.
            seeded.append({"path": path, "sha256": sha256_file(dest)
                           if os.path.isfile(dest) and not os.path.islink(dest) else ""})
            continue
        sha = util.write_file(target, path, data, entry.get("mode", "100644"))
        rec = {"path": path, "sha256": sha}
        if entry["class"] == "managed":
            rec["exec"] = entry.get("mode") == "100755"
        (managed if entry["class"] == "managed" else seeded).append(rec)

    if render_governance and template_text and owners_text is not None:
        sha = util.write_file(target, os.path.join(".github", "CODEOWNERS"),
                              owners_text.encode("utf-8"), "100644")
        rendered.append({"path": ".github/CODEOWNERS", "sha256": sha})

    util.write_json(orgconfig.default_config_path(target), config)

    record = {
        "schema": INSTALL_SCHEMA,
        "package": manifest["package"],
        "release": {
            "release_id": manifest["release_id"],
            "version": manifest["version"],
            "git_rev": manifest["created_from"]["git_rev"],
            "status": manifest["status"],
            "approved_by": (manifest.get("approval") or {}).get("approved_by"),
            "approved_at": (manifest.get("approval") or {}).get("approved_at"),
            "min_upgrade_from": (manifest.get("compatibility") or {}).get("min_upgrade_from"),
        },
        "installed_at": util.now_iso(),
        "source": os.path.abspath(source_repo),
        "status": "installed",
        # References only, plus whether they resolved at install time. No values, ever.
        "credentials": [{"name": c["name"], "ref": c["ref"], "required": c["required"],
                         "resolved": c["resolved"]} for c in creds],
        "managed": sorted(managed, key=lambda e: e["path"]),
        "seeded": sorted(seeded, key=lambda e: e["path"]),
        "rendered": rendered,
        "previous": None,
    }
    if manifest.get("layout"):
        record["layout"] = layout_mod.version_of(manifest["layout"])
    if manifest.get("seed_lines"):
        # A fresh install seeds the file from the release, which the build proved carries the line.
        _kept, missing, settled = _seed_line_plan(target, {}, manifest)
        record["seed_lines"] = settled + [{k: v for k, v in e.items() if k != "appended"}
                                          for e in (dict(m, state="missing") for m in missing)]
    util.write_json(install_record_path(target), record)

    require_verified(target, record, "freshly installed workspace")
    return record, creds


# ─── upgrade ────────────────────────────────────────────────────────────────

def upgrade(target, manifest, source_repo, aios_lookup=None, no_vercel=False):
    """Replace managed files with a newer approved release. State is never touched.

    `no_vercel`: the founder's statement that this repository isn't deployed by Vercel, for a
    layout move made without a Vercel token (R-A). Recorded with the upgrade.
    """
    with _Lock(target, "upgrade"):
        return _upgrade_locked(target, manifest, source_repo, aios_lookup, no_vercel)


DRIFT_DIFF_LINES = 40


def _layout_preflight(target, record, manifest, files, old_managed, no_vercel=False):
    """The folder move this upgrade makes, if its release changes the layout: (plan, site rows,
    blocking problems). A plan that can't run safely refuses here, with nothing changed.

    Website folders are checked against Vercel before anything moves (founder requirement R-A):
    any problem in the third value blocks the upgrade.
    """
    new_layout = manifest.get("layout") or {}
    if not new_layout.get("moves") or layout_mod.version_of(new_layout) == (record.get("layout") or "2"):
        return None, [], []
    the_plan = layout_mod.plan(target, new_layout, set(old_managed),
                               {p: e["class"] for p, e in files.items()})
    found = layout_mod.sites(target, the_plan, new_layout)
    the_plan["sites"] = found
    slug = governance.target_repo_slug(target)
    rows, blocked = hosting.check(found, new_layout, slug, no_vercel=no_vercel,
                                  vercel_files=layout_mod.vercel_files(the_plan))
    return the_plan, rows, blocked


def founder_review_notice(target, retired_roots):
    """Lines telling the client to restore founder review at the new paths (R-C), or [] when
    CODEOWNERS names none of the retired folders."""
    rel, path = governance.find_file(target)
    roots = set(retired_roots)
    stale = []
    if path:
        with open(path, encoding="utf-8", errors="replace") as fh:
            stale = [pat for _n, pat, _o in governance.parse(fh.read())
                     if pat.lstrip("/").split("/", 1)[0] in roots]
    if path and not stale:
        return []
    return ["founder review: %s %s. GitHub stops asking a founder about the founder lane until "
            "it's restored at the new paths (card docs/human_steps/restore_founder_review.md); "
            "`aios instance check` fails until it's restored and enforced"
            % (rel or "CODEOWNERS", ("still guards %s" % ", ".join(stale)) if stale else "is missing")]


def _founder_review_after_move(target, record, manifest):
    new_layout = manifest.get("layout") or {}
    if not new_layout.get("moves") or layout_mod.version_of(new_layout) == (record.get("layout") or "2"):
        return []
    return founder_review_notice(target, new_layout.get("retired_roots") or [])


def upgrade_plan(target, manifest, source_repo, aios_lookup=None, no_vercel=False):
    """What `upgrade` would do, writing nothing: the same refusals, then the managed-file changes."""
    record, _version, _min_from, _creds, files, old_managed, old_seeded, manifest = _upgrade_preflight(
        target, manifest, source_repo, aios_lookup)
    managed = {p: e for p, e in files.items() if e["class"] == "managed"}
    the_plan, site_rows, blocked = _layout_preflight(target, record, manifest, files, old_managed,
                                                     no_vercel)
    move_keys = layout_mod.destinations(the_plan)
    seed_keys = _seed_keys(record, manifest, source_repo)
    return {
        "layout": None if not the_plan else {
            "from": the_plan["from"], "to": the_plan["to"],
            "moves": [(m["from"], m["to"]) for m in the_plan["moves"]],
            "set_aside": [q["from"] for q in the_plan["quarantine"]],
            "empty_folders": [(e["from"], e["to"]) for e in the_plan["empty_dirs"]],
            "sites": site_rows,
            "blocked": blocked,
            "founder_review": _founder_review_after_move(target, record, manifest),
        },
        "from": (record.get("release") or {}).get("version"),
        "to": manifest["version"],
        "changed": sorted(p for p, e in managed.items()
                          if p in old_managed and old_managed[p].get("sha256") != e["sha256"]),
        "added": sorted(p for p in managed if p not in old_managed),
        "removed": _to_drop(old_managed, files, manifest),
        "unchanged": sum(1 for p, e in managed.items()
                         if p in old_managed and old_managed[p].get("sha256") == e["sha256"]),
        "new_seeds": sorted(p for p, e in files.items() if e["class"] == "seed"
                            and layout_mod.key(p) not in seed_keys and layout_mod.key(p) not in move_keys
                            and not os.path.lexists(os.path.join(target, p))),
        "seed_lines": [{"path": e["path"], "line": e["line"]}
                       for e in _seed_line_plan(target, record, manifest, _moved_from(the_plan))[1]],
    }


def drift_recipe(target, record, source_repo, problems):
    """For each managed file edited by hand: what changed, and the two ways forward.

    A bare "modified managed file" refusal was a dead end (Chat Zero's 2.7.0 -> 2.7.1 upgrade test).
    """
    prefix = "modified managed file: "
    drifted = [p[len(prefix):].split(" (on disk", 1)[0] for p in problems if p.startswith(prefix)]
    if not drifted:
        return []
    release = record.get("release") or {}
    rev = release.get("git_rev") or ""
    pinned = {}
    if rev and util.rev_exists(source_repo, rev):
        pinned = {path: data for path, _mode, data in util.read_tree(source_repo, rev) if path in drifted}
    out = []
    for path in drifted:
        out.append("%s was edited after install. What changed (the installed %s, then yours):"
                   % (path, release.get("version")))
        if path in pinned:
            with open(os.path.join(target, path), "rb") as fh:
                mine = fh.read()
            diff = list(difflib.unified_diff(pinned[path].decode("utf-8", "replace").splitlines(),
                                             mine.decode("utf-8", "replace").splitlines(),
                                             "release/%s" % path, "workspace/%s" % path, lineterm=""))
            out += ["    %s" % line for line in diff[:DRIFT_DIFF_LINES]]
            if len(diff) > DRIFT_DIFF_LINES:
                out.append("    ... %d more lines: git -C %s log -p -- %s"
                           % (len(diff) - DRIFT_DIFF_LINES, target, path))
            out.append("to revert it: git -C %s show %s:%s > %s, then commit"
                       % (source_repo, rev[:12], path, os.path.join(target, path)))
        else:
            out.append("    (the installed release isn't in %s; see your edit with: git -C %s log -p -- %s)"
                       % (source_repo, target, path))
            out.append("to revert it: put back the installed release's copy of %s, then commit" % path)
        out.append("to keep it: move your change into a file the release doesn't manage (your own file, "
                   "or a seed file such as CLAUDE.md), revert this one, commit, and upgrade again")
        if path == ".claude/settings.json":
            out.append("for this file specifically: put your own permission rules or settings in "
                       ".claude/settings.local.json. Claude Code merges it over this one, and no upgrade, "
                       "rollback or verify ever touches it (docs/INSTALL_AND_UPGRADE.md, \"Your own settings\")")
    return out


def _seed_line_target(target, rel):
    """The seed file a declared line goes into, or None when it is a link or leaves the workspace.

    Following a link would append to wherever it points (independent review).
    """
    full = os.path.join(target, rel)
    if os.path.islink(full) or not os.path.isfile(full):
        return None
    real_root, real = os.path.realpath(target), os.path.realpath(full)
    return full if real.startswith(real_root + os.sep) else None


def _seed_line_plan(target, record, manifest, moved_from=None):
    """The declared seed lines this release adds, and the state of the ones it doesn't.

    A seed line is added once: never twice, never to a seed file the client deleted, never into a
    link, and never again after the client removed it. Returns (carried, add, settled): entries
    already recorded, entries this upgrade appends (with the exact bytes, so an undo removes only
    those), and new entries that need no write. Bytes throughout: the client's file may hold bytes
    that aren't UTF-8, and they must survive untouched.

    `moved_from` ({new path: old path}): a file the 3.0 move relocates is read where it is now,
    before the move; the line goes into it at its new path, after the move (independent review).
    """
    moved_from = moved_from or {}
    recorded = list(record.get("seed_lines") or [])
    done = {(e["path"], e["line"]) for e in recorded}
    add, settled = [], []
    pending = {}  # path -> bytes as they will be once the earlier lines in this upgrade are added
    for sl in manifest.get("seed_lines") or []:
        if (sl["path"], sl["line"]) in done:
            continue
        entry = {"path": sl["path"], "line": sl["line"], "release": manifest["version"]}
        here = moved_from.get(sl["path"], sl["path"])
        full = os.path.join(target, here)
        if os.path.islink(full):
            settled.append(dict(entry, state="link"))  # never written through; reported instead
            continue
        if not os.path.isfile(full):
            settled.append(dict(entry, state="absent"))  # deleted by the client: theirs to keep deleted
            continue
        if _seed_line_target(target, here) is None:
            settled.append(dict(entry, state="link"))
            continue
        if sl["path"] not in pending:
            with open(full, "rb") as fh:
                pending[sl["path"]] = fh.read()
        data = pending[sl["path"]]
        line = sl["line"].encode("utf-8")
        if any(l.strip() == line for l in data.splitlines()):
            settled.append(dict(entry, state="present"))
            continue
        sep = b"" if data == b"" or data.endswith(b"\n") else b"\n"
        appended = sep + b"\n" + line + b"\n"
        pending[sl["path"]] = data + appended
        add.append(dict(entry, state="added", appended=appended.decode("utf-8")))
    return recorded, add, settled


def _replace_bytes(target, full, data):
    """Write a client file all at once: the old bytes or the new, never half of each. The
    temporary copy lives in the git-ignored backups folder, so a kill can't leave a stray file
    beside the client's own."""
    mode = stat.S_IMODE(os.lstat(full).st_mode)
    tmp = util.private_temp(target)
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, full)
    finally:
        if os.path.lexists(tmp):
            os.remove(tmp)


def _apply_seed_lines(target, adds):
    for e in adds:
        full = _seed_line_target(target, e["path"])
        if full is None:
            continue
        with open(full, "rb") as fh:
            data = fh.read()
        _replace_bytes(target, full, data + e["appended"].encode("utf-8"))


def _undo_seed_lines(target, adds):
    """Take back exactly what an upgrade appended, byte for byte. Safe to call again.

    Newest first: two lines appended by one upgrade (2.6.0 to 3.0 adds the core import and the
    folder-map line) only come off byte for byte in the reverse of the order they went on. Only
    the exact bytes recorded are removed: at the end of the file, or, if the client wrote after
    them, where they occur once. Anything less certain is left for the client and reported, never
    guessed (independent review). Returns notes for the person.
    """
    notes = []
    for e in reversed(list(adds)):
        full = _seed_line_target(target, e["path"])
        tail = (e.get("appended") or "").encode("utf-8")
        if full is None or not tail:
            continue
        with open(full, "rb") as fh:
            data = fh.read()
        if data.endswith(tail):
            _replace_bytes(target, full, data[:-len(tail)])
        elif data.count(tail) == 1:
            i = data.index(tail)
            _replace_bytes(target, full, data[:i] + data[i + len(tail):])
        elif e["line"].encode("utf-8") in data:
            notes.append("%s still has `%s`: it was edited around that line, so rollback left it for "
                         "you to remove" % (e["path"], e["line"]))
    return notes


def _moved_from(the_plan):
    return {m["to"]: m["from"] for m in (the_plan or {}).get("moves") or []}


_PINNED_SEEDS = {}


def _installed_release_seeds(record, source_repo):
    """Every seed of the installed release, from its pinned tree. A record written by a 2.x
    installer can leave some out (one the client already had at install, one absent at adopt),
    and those are the client's all the same (independent review). Empty when the source doesn't
    have the pin."""
    rev = (record.get("release") or {}).get("git_rev")
    if not source_repo or not rev or not util.FULL_SHA1_RE.match(rev):
        return set()
    cache_key = (os.path.abspath(source_repo), rev)
    if cache_key not in _PINNED_SEEDS:
        seeds = set()
        if util.rev_exists(source_repo, rev):
            try:
                seeds = {p for p, c, _m, _s in release_mod.select_files(
                    source_repo, rev, release_mod.load_spec(source_repo, rev)) if c == "seed"}
            except Refusal:
                seeds = set()
        _PINNED_SEEDS[cache_key] = seeds
    return _PINNED_SEEDS[cache_key]


def _seed_history(record, manifest, source_repo=None):
    """Every path a release has seeded into this workspace, under its old and its new name."""
    paths = ({e["path"] for e in record.get("seeded") or []} | set(record.get("seed_history") or [])
             | _installed_release_seeds(record, source_repo))
    rules = (manifest.get("layout") or {}).get("moves") or []
    if rules:
        paths |= {layout_mod.destination(p, rules) or p for p in paths}
    return paths


def _seed_keys(record, manifest, source_repo=None):
    """Every name a release has seeded into this workspace, as a Mac or Windows disk compares names.
    A seed the client deleted, under its old name or its new one, in this release or an earlier one,
    must not come back (independent review)."""
    return {layout_mod.key(p) for p in _seed_history(record, manifest, source_repo)}


def _upgrade_preflight(target, manifest, source_repo, aios_lookup=None):
    """Every check an upgrade makes before it writes anything. The dry run makes the same ones."""
    record = load_record(target)
    if load_journal(target):
        raise Refusal(EXIT_STATE, "a previous operation did not finish; run rollback first",
                      [journal_path(target)])

    release_mod.require_consumable(manifest, source_repo, aios_lookup)
    manifest = dict(manifest)
    manifest.pop("_adoption", None)  # only ever set below, in this process, never read from a file
    if record.get("adoption"):
        manifest = _adopted_upgrade_view(target, record, manifest)

    current_version = (record.get("release") or {}).get("version")
    cur = util.parse_semver(current_version or "")
    new = util.parse_semver(manifest["version"])
    if cur and new and new <= cur:
        raise Refusal(EXIT_PACKAGE,
                      "release %s is not newer than the installed %s; use rollback to go back"
                      % (manifest["version"], current_version))
    min_from = (manifest.get("compatibility") or {}).get("min_upgrade_from")
    if min_from:
        mf = util.parse_semver(min_from)
        if cur and mf and cur < mf:
            raise Refusal(EXIT_PACKAGE,
                          "release %s cannot upgrade from %s (min_upgrade_from %s)"
                          % (manifest["version"], current_version, min_from))

    # Dirty or partial state is refused, never silently overwritten. An edited managed file comes
    # with its diff and the two ways forward.
    problems, _summary = verify(target, record)
    if problems:
        raise Refusal(EXIT_VERIFY, "workspace does not match its installed release",
                      problems + drift_recipe(target, record, source_repo, problems))
    if util.worktree_dirty(target):
        raise Refusal(EXIT_STATE,
                      "the workspace has uncommitted git changes; commit or stash them so the "
                      "upgrade is a reviewable diff and git gives you a second way back")

    config = orgconfig.load(target)
    creds = orgconfig.resolve(manifest.get("credentials"), config, target)
    orgconfig.require_resolved(creds)

    files = {e["path"]: e for e in manifest.get("files") or []}
    old_managed = {e["path"]: e for e in record.get("managed") or []}
    old_seeded = {e["path"] for e in record.get("seeded") or []}

    # A path that was ever the client's seed can't become the release's: the upgrade would overwrite
    # it, and only release files are backed up. "Ever": a seed an older release stopped shipping
    # and the client then deleted is still theirs to recreate (independent review).
    # Compared as a Mac or Windows disk sees names: `Notes/Plan.md` and `notes/plan.md` are one file.
    seed_keys = _seed_keys(record, manifest, source_repo)
    reclassified = sorted(p for p, e in files.items()
                          if e["class"] == "managed" and layout_mod.key(p) in seed_keys)
    if reclassified:
        raise Refusal(EXIT_PACKAGE, "release %s would take over %d file(s) that are yours (seeded "
                      "by a release this workspace has had)" % (manifest["version"], len(reclassified)),
                      reclassified[:20] + ["a release must never make a seed file its own"])
    # A newly shipped path that already exists as something of yours is a collision. Refuse:
    # the alternative is silently eating a file the release never owned.
    collisions = []
    for path, entry in files.items():
        if path in old_managed or path in old_seeded:
            continue
        if entry["class"] == "seed" and layout_mod.key(path) in seed_keys:
            continue  # the client's seed under this name, or another spelling of it: kept as theirs
        if os.path.exists(os.path.join(target, path)):
            collisions.append(path)
    if collisions:
        raise Refusal(
            EXIT_STATE,
            "release %s ships %d path(s) that already exist in this workspace and are not "
            "managed by the installed release" % (manifest["version"], len(collisions)),
            sorted(collisions)[:20] + ["move or delete them, then upgrade again"],
        )
    return record, current_version, min_from, creds, files, old_managed, old_seeded, manifest


def _to_drop(old_managed, files, manifest):
    """Managed files an upgrade removes because the new release stopped shipping them. On an
    adopted instance, only those its plan still adopts: one the plan now calls the instance's, or
    excludes, or no longer lists, stays where it is (independent review, 3.1)."""
    dropped = set(old_managed) - set(files)
    adoption = manifest.get("_adoption")
    if adoption:
        shipped = set(adoption.get("shipped") or ())
        dropped = {p for p in dropped if p not in shipped and _adoption_class(adoption, p) == "adopt"}
    return sorted(dropped)


def _adopted_upgrade_view(target, record, manifest):
    """An adopted instance upgrades only what it adopted, as its plan says today: a path the new
    release ships that the plan doesn't classify exactly once refuses, with nothing changed."""
    info = record["adoption"]
    plan, plan_sha = load_adoption_plan(target, info.get("plan"))
    # The plan that decides an upgrade must be one git tracks: an ignored copy could say anything,
    # unseen by the clean-worktree check (independent review, 3.1 round 3).
    if not util.is_tracked(target, (info.get("plan") or ADOPTION_PLAN).replace(os.sep, "/")):
        raise Refusal(EXIT_STATE, "the adoption plan isn't committed any more",
                      [info.get("plan") or ADOPTION_PLAN, "commit it, then upgrade"])
    # Everything the adopted instance runs on stays committed: an ignored local copy would let the
    # upgrade succeed while the commit, and a fresh clone, lack it (independent review, 3.1 round 9).
    keep = [(info.get("plan") or ADOPTION_PLAN), os.path.relpath(orgconfig.default_config_path(target), target),
            roles.POLICY_PATH, os.path.relpath(install_record_path(target), target)]
    keep = [k.replace(os.sep, "/") for k in keep] + sorted(e["path"] for e in record.get("managed") or [])
    untracked = [k for k in keep if not util.is_tracked(target, k)]
    if untracked:
        raise Refusal(EXIT_STATE, "%d file(s) this adopted instance runs on aren't committed" % len(untracked),
                      untracked[:20] + ["commit them (un-ignore them first if needed), then upgrade"])
    entries = {e["path"]: e for e in manifest.get("files") or []}
    classes, problems = classify_adoption(plan, entries)
    if problems:
        raise Refusal(EXIT_STATE, "this instance's adoption plan doesn't classify every path release %s "
                      "ships exactly once" % manifest["version"],
                      problems[:30] + ["add each to adopt, instance_owned or exclude, then upgrade again"])
    old_managed = {e["path"] for e in record.get("managed") or []}
    ignored = util.ignored_paths(target, [p for p in sorted(classes)
                                          if classes[p] == "adopt" and p not in old_managed])
    if ignored:
        raise Refusal(EXIT_STATE, "%d path(s) this upgrade would create are ignored by this repository's git "
                      "rules" % len(ignored), ignored[:20] + ["un-ignore them, or exclude them in the plan"])
    _require_lifecycle_holder(roles.load_policy(target), orgconfig.load(target))
    missing = [p for p in sorted(classes) if classes[p] == "instance_owned"
               and not os.path.lexists(os.path.join(target, p))]
    seeds = [p for p in sorted(classes) if classes[p] == "adopt" and entries[p].get("class") != "managed"]
    if missing or seeds:
        raise Refusal(EXIT_STATE, "this instance's adoption plan doesn't fit release %s" % manifest["version"],
                      ["%s: the plan says it's the instance's, but it doesn't exist" % p for p in missing[:20]]
                      + ["%s: a seed can't be adopted (it would never be kept current)" % p for p in seeds[:20]])
    view = adopted_view(manifest, classes)
    view["_adoption"] = {"plan": info.get("plan"), "plan_sha256": plan_sha, "adopt": plan["adopt"],
                         "instance_owned": plan["instance_owned"], "exclude": plan["exclude"],
                         "shipped": sorted(classes)}
    return view


def _upgrade_locked(target, manifest, source_repo, aios_lookup=None, no_vercel=False):
    record, current_version, min_from, creds, files, old_managed, old_seeded, manifest = _upgrade_preflight(
        target, manifest, source_repo, aios_lookup)
    the_plan, site_rows, blocked = _layout_preflight(target, record, manifest, files, old_managed,
                                                     no_vercel)
    if blocked:
        raise Refusal(EXIT_STATE, "the folder move needs Vercel checked first (R-A); nothing was "
                                  "changed", blocked)
    move_keys = layout_mod.destinations(the_plan)
    seed_keys = _seed_keys(record, manifest, source_repo)
    seed_lines_kept, seed_lines_add, seed_lines_settled = _seed_line_plan(
        target, record, manifest, _moved_from(the_plan))

    # Folders that already exist on the way to anything this release writes. A rollback prunes
    # only the folders the upgrade made: an empty folder of the client's survives (independent review).
    pre_dirs = set()
    for p in files:
        parts = p.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            if os.path.isdir(os.path.join(target, d)):
                pre_dirs.add(d)
    pre_dirs = sorted(pre_dirs)

    txn_id = "%s-%s-to-%s" % (util.now_iso().replace(":", "").replace("-", ""),
                              current_version, manifest["version"])
    backup_root = _backup(target, record, txn_id)
    backup_rel = os.path.relpath(backup_root, target).replace(os.sep, "/")
    if the_plan:
        # The whole move, on disk before the first file moves. Rollback after a finished upgrade
        # reads it from here; recovery after a hard kill reads the journal's copy.
        util.write_json(os.path.join(backup_root, LAYOUT_PLAN), the_plan)
    util.write_json(journal_path(target), {
        "op": "upgrade", "txn": txn_id, "from_version": current_version,
        "to_version": manifest["version"], "backup": backup_rel,
        "phase": "applying", "started_at": util.now_iso(),
        # What this upgrade intends to ADD. A hard kill can stop anywhere, and the install
        # record on disk still describes the OLD release, so it cannot tell recovery about
        # files the aborted attempt already created. Without this, rollback leaves orphans.
        "adds": sorted({p for p, e in files.items()
                        if e["class"] == "managed" and p not in old_managed}),
        # The exact bytes and mode of each file this upgrade may write, so recovery removes a file
        # only while it is still that file, never a client's that appeared at the path later.
        "add_provenance": {p: [e["sha256"], 0o755 if e.get("mode") == "100755" else 0o644]
                           for p, e in files.items() if p not in old_managed},
        # Seeds this upgrade may create. A hard kill leaves them behind otherwise, and the
        # install record still describes the old release, so recovery cannot infer them.
        # Never a path a client file is moving to: recovery would delete the client's file.
        "seed_adds": sorted({p for p, e in files.items()
                             if e["class"] == "seed" and layout_mod.key(p) not in seed_keys
                             and layout_mod.key(p) not in move_keys
                             and not os.path.lexists(os.path.join(target, p))}),
        # The declared lines this upgrade appends to seed files, with their exact bytes, so a
        # recovery after a hard kill takes back only those.
        "seed_lines": seed_lines_add,
        # The folder move (3.0): every file, its hash and both paths, so recovery can put each
        # one back from any point of an interrupted move.
        "layout": the_plan,
        "pre_dirs": pre_dirs,
    })

    new_managed, new_seeded, created_seeds = [], [], []
    written = 0
    try:
        if the_plan:
            util.fault("layout.before_moves")
            layout_mod.apply(target, the_plan, backup_rel)
            problems = layout_mod.readback(target, the_plan, backup_rel)
            if problems:
                raise Refusal(EXIT_VERIFY, "the folder move did not keep every file's bytes",
                              problems[:20])
        util.fault("upgrade.before_write")
        for path, mode, data in util.read_tree(source_repo, manifest["created_from"]["git_rev"]):
            entry = files.get(path)
            if entry is None:
                continue
            if entry["sha256"] != sha256_bytes(data):
                raise Refusal(EXIT_PACKAGE,
                              "content at the pin does not match the manifest: %s" % path)
            if entry["class"] == "seed":
                dest = os.path.join(target, path)
                if os.path.lexists(dest):
                    # Already here: the client's own copy, or their file moved here by the layout
                    # move. Seeds are written once, never refreshed: the client's bytes win.
                    new_seeded.append({"path": path, "sha256": sha256_file(dest)
                                       if os.path.isfile(dest) else ""})
                elif layout_mod.key(path) in seed_keys:
                    # Seeded once already and the operator deleted it. "Written once, then
                    # never touched again" has to include not resurrecting it: an upgrade
                    # that undoes a deletion has not preserved state, whatever it reports.
                    # That holds under its new name after a folder move too.
                    new_seeded.append({"path": path, "sha256": ""})
                else:
                    sha = util.write_file(target, path, data, entry.get("mode", "100644"))
                    created_seeds.append(path)
                    new_seeded.append({"path": path, "sha256": sha})
                continue
            previous = old_managed.get(path)
            sha = util.write_file(target, path, data, entry.get("mode", "100644"))
            new_managed.append({"path": path, "sha256": sha, "exec": entry.get("mode") == "100755"})
            if previous and previous.get("sha256") != sha:
                # Fire only after a file that genuinely CHANGED. Crashing after writing a
                # byte-identical file leaves a workspace that still verifies clean, which
                # would make the recovery test pass without recovering anything.
                written += 1
                if written == 1:
                    util.fault("upgrade.mid_write")

        # Managed files the new release dropped. On an adopted instance, a file the release still
        # ships but the plan no longer adopts stays where it is and becomes the instance's: only a
        # file the release stopped shipping goes.
        dropped = _to_drop(old_managed, files, manifest)
        for path in dropped:
            full = os.path.join(target, path)
            if os.path.isfile(full):
                os.remove(full)
        _prune_parents(target, dropped)
        if the_plan:
            layout_mod.remove_emptied(target, the_plan, also=dropped)
            left = layout_mod.leftovers(target, the_plan)
            if left:
                raise Refusal(EXIT_STATE, "the folder move left %d thing(s) in the old folders"
                              % len(left), left[:20])
        _apply_seed_lines(target, seed_lines_add)
        util.fault("upgrade.before_record")

        new_record = dict(record)
        new_record["release"] = {
            "release_id": manifest["release_id"],
            "version": manifest["version"],
            "git_rev": manifest["created_from"]["git_rev"],
            "status": manifest["status"],
            "approved_by": (manifest.get("approval") or {}).get("approved_by"),
            "approved_at": (manifest.get("approval") or {}).get("approved_at"),
            "min_upgrade_from": min_from,
        }
        new_record["managed"] = sorted(new_managed, key=lambda e: e["path"])
        new_record["seeded"] = sorted(new_seeded, key=lambda e: e["path"])
        if manifest.get("_adoption"):  # the plan as it stands now; set only by the preflight, in-process
            new_record["adoption"] = dict(record.get("adoption") or {},
                                          **{k: v for k, v in manifest["_adoption"].items() if k != "shipped"})
        new_record["seed_history"] = sorted(_seed_history(record, manifest, source_repo)
                                            | {p for p, e in files.items() if e["class"] == "seed"})
        if seed_lines_kept or seed_lines_add or seed_lines_settled:
            new_record["seed_lines"] = seed_lines_kept + seed_lines_settled + seed_lines_add
        new_record["credentials"] = [{"name": c["name"], "ref": c["ref"],
                                      "required": c["required"], "resolved": c["resolved"]}
                                     for c in creds]
        # Seeds this upgrade wrote, with their bytes, so rollback removes the ones still untouched
        # and the workspace goes back to exactly what it was.
        new_record["created_seeds"] = [{"path": p, "sha256": sha256_file(os.path.join(target, p)),
                                        "mode": stat.S_IMODE(os.lstat(os.path.join(target, p)).st_mode)}
                                       for p in sorted(created_seeds)]
        new_record["pre_existing_dirs"] = pre_dirs
        if manifest.get("layout"):
            new_record["layout"] = layout_mod.version_of(manifest["layout"])
        new_record.pop("layout_migration", None)
        if the_plan:
            proof_rel = "%s/%s" % (backup_rel, LAYOUT_PROOF)
            util.write_json(os.path.join(target, proof_rel),
                            layout_mod.proof(target, the_plan, backup_rel))
            new_record["layout_migration"] = {
                "from": the_plan["from"], "to": the_plan["to"],
                "moved": len(the_plan["moves"]), "set_aside": len(the_plan["quarantine"]),
                "empty_folders": len(the_plan["empty_dirs"]),
                "plan": "%s/%s" % (backup_rel, LAYOUT_PLAN), "proof": proof_rel,
                "sites": site_rows,
                "vercel": "checked with Vercel" if not no_vercel or os.environ.get(hosting.ENV_TOKEN)
                          else "not checked: the founder stated this repository isn't deployed by Vercel",
                # Reported, never rewritten: the client's own files that still name an old folder.
                "stale_references": layout_mod.stale_references(
                    target, manifest["layout"],
                    skip_paths={e["path"] for e in new_managed} | {INSTALL_PATH} | set(created_seeds)),
            }
        new_record["upgraded_at"] = util.now_iso()
        new_record["status"] = "installed"
        new_record["previous"] = {
            "release_id": (record.get("release") or {}).get("release_id"),
            "version": current_version,
            "backup": backup_rel,
        }
        util.write_json(install_record_path(target), new_record)
        require_verified(target, new_record, "upgraded workspace")
    except BaseException as exc:
        # Any failure puts the workspace back where it started, then re-raises.
        #
        # Remove only MANAGED paths the new release introduced. An earlier version of this
        # line removed `set(files) - set(old_managed)`, which includes every *seed* path -
        # so a failed upgrade deleted CLAUDE.md, the foundations and the logs while
        # reporting a clean rollback. The state-fingerprint test caught it.
        new_managed_paths = {p for p, e in files.items() if e["class"] == "managed"}
        # Seed files this attempt created are part of what it changed, so they come out too.
        # Without this the workspace "rolled back" while carrying new files, and still
        # verified clean - the rollback reported a state it had not restored.
        removable = sorted(p for p in (new_managed_paths - set(old_managed)) | set(created_seeds)
                           if layout_mod.key(p) not in move_keys)
        _restore(target, backup_root, record, remove_paths=removable,
                 expected=set(old_managed) | new_managed_paths | set(created_seeds),
                 write_record=False, keep_dirs=pre_dirs,
                 provenance={p: [e["sha256"], 0o755 if e.get("mode") == "100755" else 0o644]
                             for p, e in files.items() if p not in old_managed})
        # The reverse of the order they happened: declared lines come off while their file is
        # still where the upgrade put it, then the folders go back (independent review, round 3).
        _undo_seed_lines(target, seed_lines_add)
        if the_plan:
            layout_mod.reverse(target, the_plan, backup_rel)
        util.write_json(install_record_path(target), record)
        problems, _ = verify(target, record)
        if problems:  # the journal stays: `rollback` can finish the job
            raise Refusal(EXIT_VERIFY,
                          "upgrade failed AND the automatic rollback did not restore cleanly",
                          [str(exc)] + problems + ["run `aios rollback` to finish restoring"])
        if os.path.isfile(journal_path(target)):
            os.remove(journal_path(target))
        if isinstance(exc, Refusal):
            exc.details = list(exc.details) + ["workspace was rolled back to %s and verified"
                                               % current_version]
            raise
        raise Refusal(EXIT_VERIFY,
                      "upgrade failed and the workspace was rolled back to %s (verified)"
                      % current_version, [str(exc)])

    os.remove(journal_path(target))
    return new_record


# ─── rollback ───────────────────────────────────────────────────────────────

def _holder_alive(text):
    """Is the process named in a lock file still running on this machine? A lock that names no
    process (empty: its holder may be writing it this instant) counts as alive: it is never
    reclaimed automatically (independent review)."""
    m = re.search(r"pid=(\d+)", text or "")
    if not m:
        return True
    try:
        os.kill(int(m.group(1)), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # running, as somebody else
    except OSError:
        return False
    return True


def rollback(target):
    """Restore the previous release. Works after a clean upgrade, a hard kill, or a killed rollback."""
    # A killed holder leaves its lock behind. Recovery is exactly when you need to get in, so
    # rollback clears a stale lock. A LIVE holder's lock is never taken: two operations at once
    # would interleave their writes (independent review).
    with _RecoveryGuard(target):  # one recovery at a time decides about a stale lock
        stale_lock = _reclaim_stale_lock(os.path.join(target, LOCK_PATH))
    return _rollback_after_reclaim(target, stale_lock)


try:
    import fcntl as _fcntl
except ImportError:  # Windows
    _fcntl = None
try:
    import msvcrt as _msvcrt
except ImportError:  # everywhere but Windows
    _msvcrt = None

# In the installer's own git-ignored backups folder, which every release since 2.6 reserves, so it
# can never be a file of the client's (independent review, round 12).
GUARD_PATH = os.path.join(BACKUP_DIR, "guard")


def _guard_path(target):
    """Where the guard lives: inside git's own folder when the workspace is a git repository, where
    git status never sees it (so a guard Windows can't delete never shows as a change, before or
    after an adoption; independent review, 3.1 round 7), else in the reserved backups folder."""
    git_dir = util.git(target, ["rev-parse", "--absolute-git-dir"], check=False) \
        if os.path.isdir(target) else ""
    if git_dir and os.path.isdir(git_dir):
        return os.path.join(git_dir, "aios-guard")
    return os.path.join(target, GUARD_PATH)


class _RecoveryGuard(object):
    """An OS-held lock around every decision about the workspace lock: taking it, releasing it,
    and judging and clearing a stale one. So two recoveries can't both clear it (independent
    review, round 3), and no new holder can take the lock between a recovery's "this one is dead"
    and its removal (round 10).

    flock on macOS and Linux; on Windows, msvcrt's lock on the file's first byte, which holds
    across processes the same way (round 11). A system with neither is refused rather than left
    unguarded. The file exists only while held: the holder deletes it before letting go, and a
    waiter that then gets the lock checks the name still means the file it locked, or starts
    again. So no file is left behind, not even after a refusal. (Windows can't delete an open
    file, so there it stays, in the git-ignored backups folder.) A killed holder's lock goes with
    its process."""

    def __init__(self, target):
        self.path = _guard_path(target)
        self.in_backups = self.path == os.path.join(target, GUARD_PATH)
        self.fd = None

    def __enter__(self):
        if _fcntl is None and _msvcrt is None:
            raise Refusal(EXIT_STATE, "this system has no file lock the installer can use, so it won't "
                                      "change anything", ["run it on macOS, Linux or Windows"])
        if self.in_backups:
            backups = os.path.dirname(self.path)
            for part in (os.path.dirname(backups), backups):  # .aios, .aios/backups: real folders
                if os.path.islink(part) or (os.path.lexists(part) and not os.path.isdir(part)):
                    raise Refusal(EXIT_STATE, "%s is a link or a file, not a folder" % part)
            os.makedirs(backups, exist_ok=True)
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        while True:
            # Made by this run, or already there (left on Windows, or a file of the repository's own,
            # which only a reserved path being taken could explain). Only one this run made is ever
            # deleted (independent review, 3.1 round 5).
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_RDWR | nofollow, 0o644)
                created = True
            except FileExistsError:
                try:
                    fd = os.open(self.path, os.O_RDWR | nofollow)
                except FileNotFoundError:
                    continue  # its holder deleted it a moment ago: make one
                created = False
            try:
                _os_lock(fd)
                held = os.fstat(fd)
                try:
                    named = os.lstat(self.path)
                except OSError:
                    named = None
            except BaseException:
                os.close(fd)
                raise
            if named is not None and (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino):
                self.fd, self.created = fd, created
                return self
            _os_unlock(fd)  # the holder before us deleted it: lock the file that's there now
            os.close(fd)

    def __exit__(self, *exc):
        if self.fd is not None:
            if getattr(self, "created", False):
                try:
                    # Only if the name still means the very file this run holds: never a file that
                    # replaced it meanwhile (independent review, 3.1 round 6). While still held, so no
                    # one can be locking it as it goes.
                    held, named = os.fstat(self.fd), os.lstat(self.path)
                    if (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino):
                        os.remove(self.path)
                except OSError:
                    pass  # gone already, or Windows (an open file can't be deleted; it stays, ignored)
            _os_unlock(self.fd)
            os.close(self.fd)
            self.fd = None
        return False


def _os_lock(fd):
    if _fcntl is not None:
        _fcntl.flock(fd, _fcntl.LOCK_EX)
        return
    os.lseek(fd, 0, os.SEEK_SET)
    while True:  # LK_LOCK gives up after 10 s; a holder may legitimately take longer
        try:
            _msvcrt.locking(fd, _msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            time.sleep(0.05)


def _os_unlock(fd):
    if _fcntl is not None:
        return  # closing the file releases flock
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        _msvcrt.locking(fd, _msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


def _reclaim_stale_lock(stale):
    """Clear a lock whose holder is dead. True if one was cleared."""
    if not os.path.exists(stale):
        return False
    text = ""
    ident = None
    try:
        fd = os.open(stale, os.O_RDONLY)
        try:
            st = os.fstat(fd)
            words = os.read(fd, 4096)
            ident = (st.st_dev, st.st_ino, words)
            text = words.decode("utf-8", "replace")
        finally:
            os.close(fd)
    except OSError:
        return False
    if _holder_alive(text):
        raise Refusal(EXIT_STATE, "another operation is still running in this workspace",
                      ["lock held by: %s" % text.strip(),
                       "let it finish, or stop that process, then run rollback. If you're sure "
                       "nothing is running, delete %s" % LOCK_PATH])
    try:
        if _still_this_lock(stale, ident):  # still the lock we judged dead
            os.remove(stale)
            return True
    except OSError:
        pass
    return False


def _rollback_after_reclaim(target, stale_lock):
    with _Lock(target, "rollback"):
        journal = load_journal(target)
        if stale_lock and not journal and not os.path.isfile(install_record_path(target)):
            # Killed before its journal, with no release ever pinned here (an adoption that hadn't
            # started writing): nothing changed, so there is nothing to undo (independent review,
            # 3.1 round 8).
            result = (None, dict(NO_RELEASE_SUMMARY, unchanged=True), "an interrupted operation had not changed "
                      "anything; cleared its lock, nothing to roll back")
        elif stale_lock and not journal:
            # A killed upgrade or rollback with no journal either never changed anything (the
            # journal is written before the first change) or had already finished. Rolling back now
            # would undo the PREVIOUS release, which nobody asked for (found by the 3.0 rehearsal's
            # real SIGKILLs).
            record = load_record(target)
            problems, summary = verify(target, record)
            if problems:
                raise Refusal(EXIT_VERIFY, "an interrupted operation left no journal, but the workspace "
                              "doesn't match its release", problems)
            result = (record, summary, "an interrupted operation had either not changed anything yet or "
                                       "had finished; cleared its lock, rolled nothing back")
        elif journal and journal.get("op") == "adopt-existing":
            notes = _undo_adoption(target, journal.get("adoption") or {}, journal.get("pending"))
            os.remove(journal_path(target))
            result = (None, dict(NO_RELEASE_SUMMARY), "an interrupted adoption was undone: every file it "
                      "created and left unchanged is gone" + "".join("; " + n for n in notes))
        elif (journal and journal.get("op") == "adopt-undo") or (not journal and _completed_adoption(target)):
            if not journal:
                # Journaled before the first removal, so a kill partway through is finished by the
                # next rollback, not left half-undone (independent review, 3.1).
                record = load_record(target)
                journal = {"op": "adopt-undo", "phase": "undoing", "started_at": util.now_iso(),
                           "adoption": record["adoption"],
                           "config": orgconfig.load(target) if os.path.isfile(
                               orgconfig.default_config_path(target)) else None}
                util.write_json(journal_path(target), journal)
            if journal.get("phase") != "complete":
                util.fault("adopt.undo_before")
                notes = _undo_adoption(target, journal.get("adoption") or {})
                journal["phase"] = "complete"
                journal["notes"] = notes
                util.write_json(journal_path(target), journal)
            result = (None, dict(NO_RELEASE_SUMMARY), "the adoption was undone: every file it created and "
                      "left unchanged is gone, and the workspace is no longer pinned to a release"
                      + "".join("; " + n for n in journal.get("notes") or []))
        elif journal and journal.get("op") == "rollback" and journal.get("phase") == "complete":
            record = load_record(target)
            problems, summary = verify(target, record)
            if problems:  # (independent review, round 3) never report success over drift
                raise Refusal(EXIT_VERIFY, "the previous rollback had finished, but the workspace no "
                              "longer matches its release", problems)
            result = (record, summary, "the previous rollback had finished; cleared what it left, "
                                       "rolled nothing further back")
        else:
            result = _rollback_locked(target, journal)
    # A finished rollback keeps its journal, marked complete, until its lock is gone: a kill in
    # between must not make the next rollback go back one release too far (independent review).
    done = load_journal(target)
    if done and done.get("op") in ("rollback", "adopt-undo") and done.get("phase") == "complete":
        os.remove(journal_path(target))
    return result


def clear_dead_lock(target):
    """A dead holder's lock, when there is nothing at all to roll back: no journal, no install
    record. It never takes a live holder's lock. True if one was cleared."""
    if load_journal(target) or os.path.lexists(install_record_path(target)):
        return False
    with _RecoveryGuard(target):
        return _reclaim_stale_lock(os.path.join(target, LOCK_PATH))


NO_RELEASE_SUMMARY = {"release_id": None, "version": None, "managed_checked": 0, "managed_total": 0}


def _completed_adoption(target):
    """An adopted instance with nothing before the adoption to go back to: rollback undoes it."""
    if not os.path.isfile(install_record_path(target)):
        return False
    record = load_record(target)
    return bool(record.get("adoption")) and not record.get("previous")


def _rollback_locked(target, journal):
    record_path = install_record_path(target)
    current = None
    if os.path.isfile(record_path):
        try:
            current = util.read_json(record_path)
        except ValueError:
            # A kill mid-write used to leave unparseable JSON here and the recovery command
            # died on it - the crash handler crashing is the worst possible failure mode.
            # The journal and the backup are enough to recover without it.
            if not journal:
                raise Refusal(
                    EXIT_STATE,
                    "the install record is corrupt and there is no journal to recover from",
                    [record_path, "restore .aios/install.json from a snapshot under "
                                  ".aios/backups/ and run verify"],
                )
            current = None

    if journal and journal.get("op") == "rollback":
        return _finish_rollback(target, journal, resumed=True)

    if journal:
        backup_root = os.path.join(target, journal["backup"])
        prior = util.read_json(os.path.join(backup_root, "install.json"))
        the_plan = journal.get("layout")
        if the_plan:
            # Checked before anything changes: a refusal here leaves the workspace as it was.
            blocked = layout_mod.reverse_conflicts(target, the_plan, journal["backup"])
            if blocked:
                raise Refusal(EXIT_STATE, "putting the folders back would overwrite %d file(s)"
                              % len(blocked), sorted(blocked)[:20]
                              + ["move those aside, then run rollback again"])
        move_keys = layout_mod.destinations(the_plan)
        # A hard kill can land anywhere, so remove every path the new release owns that the
        # old one did not, rather than trusting how far the write loop got. Never a path a
        # client file was moving to: that file goes back to its old path below.
        prior_paths = {e["path"] for e in prior.get("managed") or []}
        current_paths = {e["path"] for e in (current or {}).get("managed") or []}
        journal_adds = set(journal.get("adds") or []) | set(journal.get("seed_adds") or [])
        remove = sorted(p for p in (current_paths | journal_adds) - prior_paths
                        if layout_mod.key(p) not in move_keys)
        if the_plan:
            linked = _linked_paths(target, [m["from"] for m in the_plan["moves"]]
                                   + [m["to"] for m in the_plan["moves"]]
                                   + [layout_mod.quarantine_path(journal["backup"], q["from"])
                                      for q in the_plan["quarantine"]]
                                   + [e["from"] + "/x" for e in the_plan["empty_dirs"]])
            if linked:
                raise Refusal(EXIT_STATE, "putting the folders back would go through %d link(s)"
                              % len(linked), linked[:20] + ["replace them with real folders, then run rollback again"])
        notes = _restore(target, backup_root, prior, remove, expected=current_paths | journal_adds,
                         write_record=False, keep_dirs=journal.get("pre_dirs"),
                         provenance=journal.get("add_provenance"))
        notes += _undo_seed_lines(target, journal.get("seed_lines") or [])
        if the_plan:
            layout_mod.reverse(target, the_plan, journal["backup"])
        util.write_json(install_record_path(target), prior)
        problems, summary = verify(target, prior)
        if problems:  # the journal stays, so this can be run again
            raise Refusal(EXIT_VERIFY, "rollback did not restore a verifiable workspace", problems)
        os.remove(journal_path(target))
        return prior, summary, "; ".join(["recovered an interrupted %s" % journal.get("op", "operation")]
                                         + notes)

    if not current:
        raise Refusal(EXIT_STATE, "nothing to roll back: no install record and no journal")
    previous = current.get("previous")
    if not previous:
        raise Refusal(EXIT_STATE, "nothing to roll back: this is the first installed release")

    backup_root = os.path.join(target, previous["backup"])
    if not os.path.isdir(backup_root):
        raise Refusal(EXIT_STATE,
                      "the snapshot for %s is gone, so rollback cannot restore it"
                      % previous.get("version"),
                      [backup_root, "re-install the previous release from its pin instead"])
    migration = current.get("layout_migration") or {}
    if migration:
        plan_path = os.path.join(target, migration.get("plan") or "")
        if not os.path.isfile(plan_path):
            raise Refusal(EXIT_STATE, "the folder-move plan for %s is gone, so rollback can't put "
                          "the folders back" % previous.get("version"),
                          [plan_path, "re-install the previous release from its pin instead"])
        blocked = layout_mod.reverse_conflicts(target, util.read_json(plan_path), previous["backup"])
        if blocked:
            raise Refusal(EXIT_STATE, "putting the folders back would overwrite %d file(s)"
                          % len(blocked), sorted(blocked)[:20]
                          + ["those old paths now hold something else: move it aside, then run "
                             "rollback again"])
    # Seeds the upgrade wrote come out too, unless the client has made them their own since.
    prior_record = util.read_json(os.path.join(backup_root, "install.json"))
    created = [e for e in current.get("created_seeds") or []
               if os.path.lexists(os.path.join(target, e["path"]))]
    current_paths = {e["path"] for e in current.get("managed") or []}
    # Before the journal, so any refusal changes nothing.
    _restore_preflight(target, backup_root, prior_record,
                       sorted(current_paths - {e["path"] for e in prior_record.get("managed") or []})
                       + [e["path"] for e in created],
                       expected=current_paths | {e["path"] for e in created})
    if migration:
        moved = util.read_json(os.path.join(target, migration["plan"]))
        linked = _linked_paths(target, [m["from"] for m in moved["moves"]]
                               + [m["to"] for m in moved["moves"]]
                               + [layout_mod.quarantine_path(previous["backup"], q["from"])
                                  for q in moved["quarantine"]]
                               + [e["from"] + "/x" for e in moved["empty_dirs"]])
        if linked:
            raise Refusal(EXIT_STATE, "putting the folders back would go through %d link(s) or file(s)"
                          % len(linked), linked[:20] + ["replace them with real folders, then run rollback again"])
    # Written before the first change, so a kill during the rollback itself is recoverable: the
    # next `rollback` reads this and finishes the job (independent review).
    journal = {"op": "rollback", "backup": previous["backup"], "started_at": util.now_iso(),
               "from_version": (current.get("release") or {}).get("version"),
               "to_version": previous.get("version"), "current_record": current, "created": created}
    util.write_json(journal_path(target), journal)
    return _finish_rollback(target, journal)


def _finish_rollback(target, journal, resumed=False):
    """Undo a finished upgrade, from its rollback journal. Every step can be repeated, so a
    rollback killed partway runs again from the start and lands in the same place. The install
    record is written last; the journal goes only after the result verifies."""
    current = journal["current_record"]
    backup_root = os.path.join(target, journal["backup"])
    prior = util.read_json(os.path.join(backup_root, "install.json"))
    migration = current.get("layout_migration") or {}
    the_plan = util.read_json(os.path.join(target, migration["plan"])) if migration else None
    current_paths = {e["path"] for e in current.get("managed") or []}
    prior_paths = {e["path"] for e in prior.get("managed") or []}
    created = journal.get("created") or []
    remove = sorted(current_paths - prior_paths) + [e["path"] for e in created]
    util.fault("rollback.before_restore")
    # A starter file the upgrade created comes out only if it is still exactly what it wrote; one
    # the client has changed (bytes or permissions) or replaced is theirs now (independent review).
    notes = _restore(target, backup_root, prior, remove, expected=current_paths | {e["path"] for e in created},
                     write_record=False, keep_dirs=current.get("pre_existing_dirs"),
                     provenance={e["path"]: [e["sha256"], e.get("mode")] for e in created})
    util.fault("rollback.after_restore")
    version = (current.get("release") or {}).get("version")
    notes += _undo_seed_lines(target, [e for e in current.get("seed_lines") or []
                                       if e.get("state") == "added" and e.get("release") == version])
    if the_plan:
        layout_mod.reverse(target, the_plan, journal["backup"])
    util.fault("rollback.after_reverse")
    util.write_json(install_record_path(target), prior)
    problems, summary = verify(target, prior)
    if problems:  # the journal stays, so this can be run again
        raise Refusal(EXIT_VERIFY, "rollback did not restore a verifiable workspace", problems)
    util.write_json(journal_path(target), dict(journal, phase="complete", completed_at=util.now_iso()))
    how = ("finished an interrupted rollback to %s" if resumed else "rolled back to %s") \
        % prior["release"]["version"]
    return prior, summary, "; ".join([how] + notes)


# ─── adopt ──────────────────────────────────────────────────────────────────

# ─── adopting into an existing instance (3.1, G81) ──────────────────────────
#
# Phoenix, 2026-10-14 (ai-os #532): "safe Starter adoption into FF's existing AIOS with NO
# OVERWRITE. ... Implement approved components/explicit overrides with rehearsal and rollback; do not
# infer existing adoption works already." So: the instance's own plan names every path the release
# ships as adopted, the instance's own, or excluded; nothing is inferred; adoption only ever creates
# files; an existing instance never gets a folder move or a seed line.

ADOPTION_SCHEMA = "ff-aios-starter/adoption@1"
ADOPTION_PLAN = os.path.join(AIOS_DIR, "adoption.json")
ADOPTION_CLASSES = ("adopt", "instance_owned", "exclude")
# Paths no real plan names, in every shape: top level, nested, dotted, with and without an extension.
CATCH_ALL_PROBES = ("aios-probe-7f3a", "aios-probe-7f3a.md", ".aios-probe-7f3a", "aios-probe-7f3a/x",
                    "aios-probe-7f3a/x/y.z", ".aios-probe-7f3a/.x/y")


def load_adoption_plan(target, rel=None):
    """(plan, sha256) of the instance's own adoption plan: a file the instance commits and owns."""
    rel = (rel or ADOPTION_PLAN).replace(os.sep, "/")
    if not util.safe_relpath(rel):
        raise Refusal(EXIT_STATE, "the adoption plan must be a path inside the workspace: %s" % rel)
    full = os.path.join(target, rel)
    linked = _linked_paths(target, [rel])
    if linked or os.path.islink(full) or not os.path.isfile(full):
        raise Refusal(EXIT_STATE, "no adoption plan at %s" % rel,
                      ["an existing instance names every path the release ships as adopt, "
                       "instance_owned or exclude (docs/INSTALL_AND_UPGRADE.md)"])
    plan = util.read_json_safe(full, "adoption plan")
    problems = []
    if not isinstance(plan, dict) or plan.get("schema") != ADOPTION_SCHEMA:
        problems.append("schema is %r, expected %r" % ((plan or {}).get("schema") if isinstance(plan, dict)
                                                      else None, ADOPTION_SCHEMA))
    else:
        for cls in ADOPTION_CLASSES:
            items = plan.get(cls)
            if not isinstance(items, list) or not all(isinstance(x, str) and x.strip() for x in items):
                problems.append("%s must be a list of paths or patterns" % cls)
                continue
            # Judged by what the patterns match, not by how they're spelt (`***`, `?*` and `*` with
            # `*/**` all match everything): a list that covers every kind of path at once is refused.
            if all(util.match_any(items, probe) for probe in CATCH_ALL_PROBES):
                problems.append("%s would classify every path at once (%s); name what it covers "
                                "(independent review, 3.1)" % (cls, ", ".join(repr(i) for i in items[:5])))
    if problems:
        raise Refusal(EXIT_STATE, "the adoption plan %s isn't usable" % rel, problems)
    return plan, sha256_file(full)


def classify_adoption(plan, paths):
    """({path: class}, problems). Every path in exactly one list: unlisted or twice-listed refuses."""
    classes, problems = {}, []
    for path in sorted(paths):
        hits = [c for c in ADOPTION_CLASSES if util.match_any(plan.get(c), path)]
        if len(hits) == 1:
            classes[path] = hits[0]
        elif not hits:
            problems.append("%s: not in the plan (adopt it, keep it as the instance's, or exclude it)" % path)
        else:
            problems.append("%s: in more than one list (%s)" % (path, ", ".join(hits)))
    return classes, problems


def _adoption_class(info, path):
    hits = [c for c in ADOPTION_CLASSES if util.match_any((info or {}).get(c), path)]
    return hits[0] if len(hits) == 1 else None


def adopted_view(manifest, classes):
    """The release as an adopted instance has it: only its adopted files, and never a folder move or
    a seed line (an existing instance keeps its own folders and its own CLAUDE.md)."""
    view = json.loads(json.dumps(manifest))
    view["files"] = [e for e in view.get("files") or [] if classes.get(e["path"]) == "adopt"]
    view.pop("layout", None)
    view.pop("seed_lines", None)
    return view


def _config_text(config):
    return (json.dumps(config, indent=2, sort_keys=True) + "\n").encode("utf-8")


def adopt_existing(target, manifest, source_repo, config, plan_rel=None, aios_lookup=None):
    """Adopt an approved release into an instance that already exists: create-only, as its plan says.

    Refuses, with nothing changed, unless every path the release ships is classified exactly once;
    every adopted path is absent and reachable without a link; every path declared the instance's
    exists; the instance has its own role policy (rollback and upgrade read it); and the workspace
    is committed. Journaled before the first write, so `rollback` undoes even a killed adoption.
    """
    # Before the lock, which itself writes: the installer's own paths must be free, or be a guard
    # it left (empty, untracked), so a repository that was never a Starter keeps every file it has.
    problems = _reserved_before_adoption(target)
    if problems:
        raise Refusal(EXIT_STATE, "the installer's own paths aren't free in this workspace; nothing was "
                                  "changed", problems)
    with _Lock(target, "adopt"):
        return _adopt_existing_locked(target, manifest, source_repo, config, plan_rel, aios_lookup)


def _reserved_before_adoption(target):
    out = []
    for rel in (LOCK_PATH, os.path.relpath(journal_path(target), target)):
        if os.path.lexists(os.path.join(target, rel)):
            out.append("%s exists: another operation is running, or one was interrupted "
                       "(`aios rollback` clears it)" % rel.replace(os.sep, "/"))
    backups = os.path.join(target, BACKUP_DIR)
    if os.path.lexists(backups):
        rel = BACKUP_DIR.replace(os.sep, "/")
        if os.path.islink(backups) or not os.path.isdir(backups):
            out.append("%s is a link or a file of this repository's own; the installer needs that folder" % rel)
        elif os.listdir(backups):
            # The installer's own backups folder holding anything already would mix the repository's
            # files with the installer's records (independent review, 3.1 round 7).
            out.append("%s already holds files of this repository's own; the installer needs that folder "
                       "empty" % rel)
    return out


def _adopt_existing_locked(target, manifest, source_repo, config, plan_rel, aios_lookup):
    release_mod.require_consumable(manifest, source_repo, aios_lookup)
    orgconfig.require_valid(config)
    if os.path.lexists(install_record_path(target)):
        raise Refusal(EXIT_STATE, "this workspace already has an install record; use upgrade",
                      [install_record_path(target)])
    if load_journal(target):
        raise Refusal(EXIT_STATE, "a previous operation did not finish; run rollback first",
                      [journal_path(target)])
    if not util.is_git_repo(target):
        raise Refusal(EXIT_STATE, "this isn't a git repository; adopting into an existing instance needs "
                                  "one, so the plan is committed and git gives a second way back")
    if util.worktree_dirty(target):
        raise Refusal(EXIT_STATE, "the workspace has uncommitted git changes; commit them first, so the "
                                  "adoption is one reviewable diff")
    policy_path = os.path.join(target, roles.POLICY_PATH)
    try:
        roles.load_policy(target)
    except Refusal as exc:
        raise Refusal(EXIT_STATE, "this instance has no usable role policy of its own (%s)" % exc.message,
                      ["write %s first: upgrade and rollback read it, so without it an adoption "
                       "couldn't be rolled back" % roles.POLICY_PATH])
    if os.path.islink(policy_path):
        raise Refusal(EXIT_STATE, "%s is a link, not the instance's own file" % roles.POLICY_PATH)
    _require_lifecycle_holder(roles.load_policy(target), config)

    plan_rel = (plan_rel or ADOPTION_PLAN).replace(os.sep, "/")
    plan, plan_sha = load_adoption_plan(target, plan_rel)
    untracked = [rel for rel in (plan_rel, roles.POLICY_PATH.replace(os.sep, "/"))
                 if not util.is_tracked(target, rel)]
    if untracked:
        raise Refusal(EXIT_STATE, "the plan and the role policy must be committed, not just on disk",
                      untracked + ["git add them and commit, then adopt"])
    entries = {e["path"]: e for e in manifest.get("files") or []}
    classes, problems = classify_adoption(plan, entries)
    if problems:
        raise Refusal(EXIT_STATE, "the adoption plan doesn't classify every path release %s ships exactly "
                      "once" % manifest["version"], problems[:30] + ["%d problem(s) in all" % len(problems)])
    adopt = [entries[p] for p in sorted(entries) if classes[p] == "adopt"]
    seeds = [e["path"] for e in adopt if e.get("class") != "managed"]
    if seeds:
        raise Refusal(EXIT_STATE, "the plan adopts %d seed file(s); a seed is written once and is then the "
                      "instance's, so it can't be kept current" % len(seeds),
                      seeds[:20] + ["exclude them, or copy one in yourself and keep it as instance_owned"])
    if not adopt:
        raise Refusal(EXIT_STATE, "the plan adopts no path release %s ships, so there is nothing to adopt"
                      % manifest["version"])
    present = [e["path"] for e in adopt if os.path.lexists(os.path.join(target, e["path"]))]
    if present:
        raise Refusal(EXIT_STATE, "%d path(s) the plan adopts already exist; adoption never overwrites"
                      % len(present), present[:20] + ["keep them as the instance's (instance_owned) or "
                                                       "exclude them"])
    missing = [p for p in sorted(entries) if classes[p] == "instance_owned"
               and not os.path.lexists(os.path.join(target, p))]
    if missing:
        raise Refusal(EXIT_STATE, "%d path(s) the plan says are the instance's don't exist" % len(missing),
                      missing[:20] + ["adopt them, exclude them, or restore the instance's own file"])
    config_path = orgconfig.default_config_path(target)
    config_rel = os.path.relpath(config_path, target).replace(os.sep, "/")
    config_created = not os.path.lexists(config_path)
    if not config_created:
        same = False
        if os.path.isfile(config_path) and not os.path.islink(config_path):
            try:
                same = util.read_json(config_path) == config
            except (ValueError, OSError, Refusal):
                same = False
        if not same:
            raise Refusal(EXIT_STATE, "this workspace already has a different organization config",
                          [config_path, "adopt with --config pointing at it, or move it aside"])
        if not util.is_tracked(target, config_rel):
            # An ignored or uncommitted people map would never reach the commit, and a fresh clone
            # couldn't tell who may run upgrades or approve the founder lane (independent review, 3.1
            # round 8).
            raise Refusal(EXIT_STATE, "the organization config already here isn't committed",
                          [config_rel, "commit it (it holds references, never secrets), or move it aside"])
    record_rel = os.path.relpath(install_record_path(target), target).replace(os.sep, "/")
    ignored = util.ignored_paths(target, [e["path"] for e in adopt] + [record_rel]
                                 + ([config_rel] if config_created else []))
    if ignored:
        # Written but ignored, it would never reach the commit, and a fresh clone would lack it
        # (independent review, 3.1 round 7).
        raise Refusal(EXIT_STATE, "%d path(s) adoption would create are ignored by this repository's git "
                      "rules" % len(ignored), ignored[:20] + ["un-ignore them, or exclude them in the plan"])
    linked = _linked_paths(target, [e["path"] for e in adopt] + [config_rel, record_rel])
    if linked:
        raise Refusal(EXIT_STATE, "adoption would write through a link or a file in a folder's place",
                      linked[:20])
    creds = orgconfig.resolve(manifest.get("credentials"), config, target)
    orgconfig.require_resolved(creds)

    pre_dirs = set()
    for rel in [e["path"] for e in adopt] + [config_rel, record_rel]:
        parts = rel.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            if os.path.isdir(os.path.join(target, d)):
                pre_dirs.add(d)
    info = {
        "plan": plan_rel, "plan_sha256": plan_sha,
        "adopt": plan["adopt"], "instance_owned": plan["instance_owned"], "exclude": plan["exclude"],
        "created": [], "pre_dirs": sorted(pre_dirs),
    }
    journal = {
        "op": "adopt-existing", "phase": "writing", "started_at": util.now_iso(),
        "release_id": manifest["release_id"], "to_version": manifest["version"], "adoption": info,
        # The file being created right now, and its temporary copy: until it's recorded below,
        # rollback removes it only if it's still that very copy (same inode), never a file that
        # merely matches (independent review, 3.1).
        "pending": None,
        # The people map rollback checks the operator against, if a kill comes before it lands.
        # References only: an org config never carries a credential value.
        "config": config if config_created else None,
    }
    util.write_json(journal_path(target), journal)
    util.fault("adopt.after_journal")

    def create(rel, data, mode, provenance=True):
        def pending(tmp):
            journal["pending"] = {"path": rel, "temp": os.path.relpath(tmp, target).replace(os.sep, "/"),
                                  "sha256": sha256_bytes(data), "mode": stat.S_IMODE(os.lstat(tmp).st_mode)}
            util.write_json(journal_path(target), journal)
        tmp = util.create_new(target, rel, data, mode, pending)
        if provenance:
            st = os.lstat(os.path.join(target, rel))
            # The mode as the disk keeps it, so rollback compares like with like on every system.
            info["created"].append({"path": rel, "sha256": sha256_bytes(data),
                                    "mode": stat.S_IMODE(st.st_mode)})
            util.write_json(journal_path(target), journal)
        util.fault("adopt.after_link")
        # The temporary copy goes before `pending` is cleared, so a kill in between still names it
        # and rollback removes it (independent review, 3.1 round 2).
        os.remove(tmp)
        journal["pending"] = None
        util.write_json(journal_path(target), journal)

    try:
        if config_created:  # first, so a rollback after any later kill can tell who is asking
            create(config_rel, _config_text(config), "100644")
        managed, seeded, written = [], [], 0
        for path, _mode, data in util.read_tree(source_repo, manifest["created_from"]["git_rev"]):
            entry = entries.get(path)
            if entry is None or classes[path] != "adopt":
                continue
            if entry["sha256"] != sha256_bytes(data):
                raise Refusal(EXIT_PACKAGE, "content at the pin does not match the manifest: %s" % path)
            create(path, data, entry.get("mode", "100644"))
            written += 1
            if written == 1:
                util.fault("adopt.mid_write")
            rec = {"path": path, "sha256": entry["sha256"]}
            if entry["class"] == "managed":
                rec["exec"] = entry.get("mode") == "100755"
                managed.append(rec)
            else:
                seeded.append(rec)
        bad = [e["path"] for e in adopt if not _same_bytes_and_mode(target, e)]
        if bad:
            raise Refusal(EXIT_VERIFY, "the adopted files did not read back as the release", bad[:20])
        util.fault("adopt.before_record")
        record = {
            "schema": INSTALL_SCHEMA,
            "package": manifest["package"],
            "release": {
                "release_id": manifest["release_id"], "version": manifest["version"],
                "git_rev": manifest["created_from"]["git_rev"], "status": manifest["status"],
                "approved_by": (manifest.get("approval") or {}).get("approved_by"),
                "approved_at": (manifest.get("approval") or {}).get("approved_at"),
                "min_upgrade_from": (manifest.get("compatibility") or {}).get("min_upgrade_from"),
            },
            "installed_at": util.now_iso(),
            "source": os.path.abspath(source_repo),
            "status": "installed",
            "credentials": [{"name": c["name"], "ref": c["ref"], "required": c["required"],
                             "resolved": c["resolved"]} for c in creds],
            "managed": sorted(managed, key=lambda e: e["path"]),
            "seeded": sorted(seeded, key=lambda e: e["path"]),
            "seed_history": sorted(e["path"] for e in seeded),
            "rendered": [],
            "previous": None,
            "adoption": info,
        }
        # Its own entry can't be inside it; rollback knows it by the plan's hash instead.
        create(record_rel, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"), "100644",
               provenance=False)
    except Refusal:
        _undo_adoption(target, info, journal.get("pending"))
        if os.path.isfile(journal_path(target)):
            os.remove(journal_path(target))
        raise
    os.remove(journal_path(target))
    require_verified(target, record, "adopted workspace")
    return record


def _require_lifecycle_holder(policy, config):
    """Someone in the people map holds a role the instance's own policy lets both upgrade and roll back:
    otherwise an adoption, or an upgrade of one, could never be rolled back (independent review, 3.1
    rounds 9 and 10)."""
    able = {name for name, role in (policy.get("roles") or {}).items()
            if {"upgrade", "rollback"} <= set(role.get("lifecycle") or [])}
    if not any(p.get("role") in able for p in (config or {}).get("people") or []):
        raise Refusal(EXIT_STATE, "nobody in the people map holds a role the instance's policy lets upgrade "
                      "and roll back", ["give a role in %s the lifecycle actions upgrade and rollback, and "
                                        "someone in the people map that role" % roles.POLICY_PATH])


def _same_bytes_and_mode(target, entry):
    full = os.path.join(target, entry["path"])
    try:
        st = os.lstat(full)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode) or sha256_file(full) != entry["sha256"]:
        return False
    return not _EXEC_BITS or bool(st.st_mode & 0o100) == (entry.get("mode") == "100755")


def _undo_adoption(target, info, pending=None):
    """Take back exactly what an adoption created: the files it recorded, while each is still the
    bytes and mode it wrote, and a file it was creating when killed only if it is still that very
    copy (same inode as its temporary file). Returns notes about anything left. Never removes the
    journal: the caller does, last."""
    notes = []
    created = [c["path"] for c in info.get("created") or []]
    for i, c in enumerate(info.get("created") or []):
        note = _remove_if_ours(target, c["path"], c["sha256"], c.get("mode"))
        if note:
            notes.append(note)
        if i == 0:
            util.fault("adopt.undo_mid")
    if pending:
        dest = os.path.join(target, pending["path"])
        tmp = os.path.join(target, pending["temp"])
        if os.path.lexists(tmp):
            if os.path.lexists(dest) and os.path.samestat(os.lstat(dest), os.lstat(tmp)):
                # The very copy this run made (the same inode), and still the bytes and mode it wrote:
                # an edit after a kill changes the shared inode, and is the instance's then
                # (independent review, 3.1 round 10).
                st = os.lstat(dest)
                if sha256_file(dest) == pending.get("sha256") and stat.S_IMODE(st.st_mode) == pending.get("mode"):
                    os.remove(dest)
                    created.append(pending["path"])
                else:
                    notes.append("%s changed after an interrupted adoption made it, so it was left for you"
                                 % pending["path"])
            os.remove(tmp)
    record_full = install_record_path(target)
    if os.path.isfile(record_full) and not os.path.islink(record_full):
        try:
            if (util.read_json(record_full).get("adoption") or {}).get("plan_sha256") == info.get("plan_sha256"):
                os.remove(record_full)
        except (ValueError, OSError):
            notes.append("the install record couldn't be read, so it was left")
    record_rel = os.path.relpath(record_full, target).replace(os.sep, "/")
    _prune_parents(target, created + [record_rel], keep=info.get("pre_dirs"))
    return notes


def adopt(target, manifest, source_repo, config, aios_lookup=None):
    """Pin an existing workspace that matches a release byte for byte.

    The "Use this template" button copies mutable `main`, which is the one thing founder
    ruling D3 forbids. Adopt is the way back onto the contract without reinstalling: it
    proves the tree on disk *is* an approved release, then writes the pin.
    """
    release_mod.require_consumable(manifest, source_repo, aios_lookup)
    orgconfig.require_valid(config)
    if os.path.isfile(install_record_path(target)):
        raise Refusal(EXIT_STATE, "this workspace already has an install record")

    managed, seeded, mismatches = [], [], []
    for entry in manifest.get("files") or []:
        path = os.path.join(target, entry["path"])
        if entry["class"] == "seed":
            # Every seed, present or not: one the client deleted before adopting is still theirs,
            # and an upgrade must not bring it back (independent review).
            seeded.append({"path": entry["path"], "sha256": sha256_file(path)
                           if os.path.isfile(path) and not os.path.islink(path) else ""})
            continue
        if not os.path.lexists(path):
            mismatches.append("missing: %s" % entry["path"])
            continue
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            mismatches.append("not a regular file: %s" % entry["path"])
            continue
        actual = sha256_file(path)
        if actual != entry["sha256"]:
            mismatches.append("differs: %s" % entry["path"])
            continue
        # The bytes are not the whole file: a hook without its executable bit never runs
        # (independent review). Pinned like an install pins it, so verify keeps checking it.
        want_exec = entry.get("mode") == "100755"
        if st.st_mode & 0o7000 or (_EXEC_BITS and bool(st.st_mode & 0o100) != want_exec):
            mismatches.append("permissions differ: %s" % entry["path"])
            continue
        managed.append({"path": entry["path"], "sha256": actual, "exec": want_exec})
    if mismatches:
        raise Refusal(
            EXIT_VERIFY,
            "this workspace does not match release %s, so it cannot be pinned to it"
            % manifest["release_id"],
            mismatches[:20] + ["%d difference(s) total" % len(mismatches)],
        )

    creds = orgconfig.resolve(manifest.get("credentials"), config, target)
    orgconfig.require_resolved(creds)
    util.write_json(orgconfig.default_config_path(target), config)
    record = {
        "schema": INSTALL_SCHEMA,
        "package": manifest["package"],
        "release": {
            "release_id": manifest["release_id"], "version": manifest["version"],
            "git_rev": manifest["created_from"]["git_rev"], "status": manifest["status"],
            "approved_by": (manifest.get("approval") or {}).get("approved_by"),
            "approved_at": (manifest.get("approval") or {}).get("approved_at"),
            "min_upgrade_from": (manifest.get("compatibility") or {}).get("min_upgrade_from"),
        },
        "installed_at": util.now_iso(),
        "adopted": True,
        "source": os.path.abspath(source_repo),
        "status": "installed",
        "credentials": [{"name": c["name"], "ref": c["ref"], "required": c["required"],
                         "resolved": c["resolved"]} for c in creds],
        "managed": sorted(managed, key=lambda e: e["path"]),
        "seeded": sorted(seeded, key=lambda e: e["path"]),
        "rendered": [],
        "previous": None,
    }
    util.write_json(install_record_path(target), record)
    require_verified(target, record, "adopted workspace")
    return record
