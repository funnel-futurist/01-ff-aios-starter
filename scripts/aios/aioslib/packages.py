"""The bounded compatible package contract: which packages this installer may install, and how each is read.

Exactly two, by name. Anything else is refused; there is no generic "any package" path.

* `ff-aios-starter`: this repository's own releases (a release manifest from `release build`, approved and
  pinned; see release.py). Unchanged.
* `life-os-release-1`: a Life OS Release 1 package. Its files live under `release1/` of the source
  repository, listed by `release1/MANIFEST.json` (package, then files with path, class managed or seed,
  mode 0644 or 0755, sha256). The installer reads it from a pinned commit, never the working copy, and
  checks the manifest against the bytes at that commit both ways: every listed file is there with its
  sha256, and every file under `release1/` is listed. Its role policy (`release1/.aios/roles.json`) is read
  from the same commit and must not contradict the manifest: it protects no seed and opens no managed file to the operator.
"""

import json
import re

from . import util
from .util import EXIT_PACKAGE, Refusal

STARTER = "ff-aios-starter"
LIFEOS_R1 = "life-os-release-1"
COMPATIBLE = (STARTER, LIFEOS_R1)

LIFEOS_R1_ROOT = "release1"
LIFEOS_R1_MANIFEST = "MANIFEST.json"
LIFEOS_R1_POLICY = ".aios/roles.json"
LIFEOS_SEED_CONFIG = ".aios/config.json"
_MODES = {"0644": "100644", "0755": "100755"}
_SHA = re.compile(r"^[0-9a-f]{64}$")


def require_compatible(package):
    if package not in COMPATIBLE:
        raise Refusal(EXIT_PACKAGE, "package %r isn't one this installer accepts; nothing was read or written"
                      % (package,), ["compatible packages: %s" % ", ".join(COMPATIBLE)])
    return package


def resolve_pin(repo, rev):
    """The full commit sha `rev` names in `repo`, refusing what isn't a commit there."""
    if util._is_option(rev) or not util.rev_exists(repo, rev):
        raise Refusal(EXIT_PACKAGE, "%r isn't a commit in %s; nothing was read or written" % (rev, repo))
    return util.git(repo, ["rev-parse", "--verify", "%s^{commit}" % rev])


def lifeos_r1(repo, rev):
    """(manifest, policy, prefix) for Life OS Release 1 at the pinned commit `rev`.

    `manifest` is in the shape install() takes (paths relative to the target, git modes, the pin in
    created_from.git_rev); `prefix` is the folder the files sit under in the source tree. Refuses any
    disagreement between the manifest and the bytes at the pin, any unsafe or reserved path, and any link."""
    pin = resolve_pin(repo, rev)
    prefix = LIFEOS_R1_ROOT + "/"
    tree, links = {}, []
    for path, mode, data in util.read_tree(repo, pin, include_links=True):
        if not path.startswith(prefix):
            continue
        rel = path[len(prefix):]
        if mode not in ("100644", "100755"):
            links.append(rel)
        else:
            tree[rel] = (mode, data)
    if links:
        raise Refusal(EXIT_PACKAGE, "the %s package holds links; nothing was written" % LIFEOS_R1, sorted(links)[:20])
    if LIFEOS_R1_MANIFEST not in tree:
        raise Refusal(EXIT_PACKAGE, "no %s%s at %s; this isn't a %s package" % (prefix, LIFEOS_R1_MANIFEST, pin[:12],
                                                                              LIFEOS_R1))
    try:
        raw = json.loads(tree[LIFEOS_R1_MANIFEST][1].decode("utf-8"))
    except ValueError:
        raise Refusal(EXIT_PACKAGE, "%s%s isn't JSON" % (prefix, LIFEOS_R1_MANIFEST))
    if not isinstance(raw, dict) or raw.get("package") != LIFEOS_R1:
        got = raw.get("package") if isinstance(raw, dict) else None
        require_compatible(got)
        raise Refusal(EXIT_PACKAGE, "%s%s names package %r, not %s" % (prefix, LIFEOS_R1_MANIFEST, got, LIFEOS_R1))
    listed = raw.get("files")
    if not isinstance(listed, list) or not listed:
        raise Refusal(EXIT_PACKAGE, "%s%s lists no files" % (prefix, LIFEOS_R1_MANIFEST))

    problems, files, seen = [], [], set()
    for i, e in enumerate(listed):
        if not isinstance(e, dict):
            problems.append("files[%d] isn't an object" % i)
            continue
        path, cls, mode, sha = e.get("path"), e.get("class"), e.get("mode"), e.get("sha256")
        if not isinstance(path, str) or not util.safe_relpath(path) or path != path.strip():
            problems.append("files[%d]: unsafe path %r" % (i, path))
            continue
        if path in seen:
            problems.append("%s is listed twice" % path)
            continue
        seen.add(path)
        # The one exception: Life OS ships its learner settings at .aios/config.json as a seed. This install
        # writes no organization config there, so a seed (created only when absent) takes nothing of the installer's.
        if path == LIFEOS_R1_MANIFEST or (util.is_reserved(path) and not (path == LIFEOS_SEED_CONFIG and cls == "seed")):
            problems.append("%s is the installer's own path; no package may ship it" % path)
        if cls not in ("managed", "seed"):
            problems.append("%s: class %r isn't managed or seed" % (path, cls))
        if mode not in _MODES:
            problems.append("%s: mode %r isn't 0644 or 0755" % (path, mode))
        if not isinstance(sha, str) or not _SHA.match(sha):
            problems.append("%s: sha256 %r isn't 64 hex characters" % (path, sha))
            continue
        at = tree.get(path)
        if at is None:
            problems.append("%s is listed but not in %s at %s" % (path, prefix, pin[:12]))
        elif util.sha256_bytes(at[1]) != sha:
            problems.append("content at the pin does not match the manifest: %s" % path)
        elif mode in _MODES and _MODES[mode] != at[0]:
            problems.append("%s: mode at the pin isn't %s" % (path, mode))
        files.append({"path": path, "class": cls, "mode": _MODES.get(mode, "100644"), "sha256": sha})
    unlisted = sorted(set(tree) - seen - {LIFEOS_R1_MANIFEST})
    problems += ["%s%s is in the package but not in its manifest" % (prefix, p) for p in unlisted]

    policy = None
    if LIFEOS_R1_POLICY not in tree:
        problems.append("the package ships no %s, so no policy can be checked" % LIFEOS_R1_POLICY)
    else:
        try:
            policy = json.loads(tree[LIFEOS_R1_POLICY][1].decode("utf-8"))
        except ValueError:
            policy = None
        if not isinstance(policy, dict) or policy.get("package") != LIFEOS_R1 or not all(
                isinstance(policy.get(k), list) for k in ("protected_paths", "operator_may_write")):
            problems.append("%s isn't the %s policy shape (package, protected_paths, operator_may_write)"
                            % (LIFEOS_R1_POLICY, LIFEOS_R1))
        else:
            # The policy and the manifest must not contradict each other: a seed is the learner's, so the policy
            # can't protect it; a managed file is the release's, so the policy can't open it to the operator.
            for f in files:
                if f["class"] == "seed" and util.lane_match(policy["protected_paths"], f["path"]):
                    problems.append("the policy protects seed file %s, which is the learner's" % f["path"])
                if f["class"] == "managed" and util.lane_match(policy["operator_may_write"], f["path"]):
                    problems.append("the policy lets the operator write managed file %s" % f["path"])
    if problems:
        raise Refusal(EXIT_PACKAGE, "the %s package at %s may not be installed; nothing was written"
                      % (LIFEOS_R1, pin[:12]), problems[:40])

    manifest = {
        "package": LIFEOS_R1,
        "release_id": "%s@%s" % (LIFEOS_R1, pin[:12]),
        "version": None,
        "status": "pinned",
        "created_from": {"git_rev": pin},
        "files": sorted(files, key=lambda f: f["path"]),
        "credentials": [],
    }
    return manifest, policy, prefix
