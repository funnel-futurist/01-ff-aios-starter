"""The bounded compatible package contract: installing a `life-os-release-1` package with `install --package`.

The source is a synthetic repository shaped like a Life OS Release 1 package (a `release1/` folder with its
MANIFEST.json, computed here), built in a temporary directory; no real package is read.
"""

import hashlib
import json
import os
import subprocess
import unittest

import harness
from harness import run_git, write

from aioslib import install as install_mod, packages, util  # noqa: E402

POLICY = {
    "package": "life-os-release-1",
    "protected_paths": ["tools/**", ".aios/roles.json", "MANIFEST.json"],
    "operator_may_write": ["notes/**", ".aios/config.json"],
    "never_read": [".env", ".env.*"],
}
FILES = {  # path: (class, content)
    "tools/check.mjs": ("managed", "export const ok = true;\n"),
    "tools/run.sh": ("managed", "#!/bin/sh\necho ok\n"),
    ".aios/roles.json": ("managed", json.dumps(POLICY, indent=2) + "\n"),
    ".aios/config.json": ("seed", '{"time_zone": null}\n'),
    "CLAUDE.md": ("seed", "# Your Life OS\n"),
    "notes/README.md": ("seed", "Your notes.\n"),
}


def build_manifest(pkg_root):
    files = []
    for rel in sorted(FILES):
        full = os.path.join(pkg_root, rel)
        with open(full, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        files.append({"path": rel, "class": FILES[rel][0],
                      "mode": "0755" if os.stat(full).st_mode & 0o111 else "0644", "sha256": sha})
    return {"package": "life-os-release-1", "files": files}


def make_lifeos_repo(root, mutate=None):
    """A git repo with release1/ and its manifest; `mutate(pkg_root, manifest)` may change either before the commit."""
    os.makedirs(root)
    run_git(root, "init", "-q")
    run_git(root, "config", "user.email", "test@example.invalid")
    run_git(root, "config", "user.name", "test")
    pkg = os.path.join(root, "release1")
    for rel, (_cls, content) in FILES.items():
        write(pkg, rel, content)
    os.chmod(os.path.join(pkg, "tools/run.sh"), 0o755)
    write(root, "README.md", "outside the package\n")
    manifest = build_manifest(pkg)
    if mutate:
        mutate(pkg, manifest)
    write(pkg, "MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", "release 1")
    return subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"]).decode().strip()


class LifeOSPackage(harness.Sandbox):

    def setUp(self):
        super().setUp()
        # No identity is checked: the package's policy has no roles to check one against.
        self.lifeos = os.path.join(self.tmp, "lifeos")

    def install(self, rev, target=None, *extra):
        return self.cli("install", "--package", "life-os-release-1", "--repo", self.lifeos, "--rev", rev,
                        "--target", target or self.target, *extra)

    def test_installs_and_writes_the_record(self):
        rev = make_lifeos_repo(self.lifeos)
        code, out, err = self.install(rev)
        self.assertEqual(code, 0, out + err)
        record = install_mod.load_record(self.target)
        self.assertEqual(record["package"], "life-os-release-1")
        self.assertEqual(record["schema"], install_mod.INSTALL_SCHEMA)
        self.assertEqual(record["release"]["git_rev"], rev)
        manifest = json.loads(subprocess.check_output(
            ["git", "-C", self.lifeos, "show", "%s:release1/MANIFEST.json" % rev]))
        want = {f["path"]: f["sha256"] for f in manifest["files"] if f["class"] == "managed"}
        self.assertEqual({e["path"]: e["sha256"] for e in record["managed"]}, want)
        self.assertEqual({e["path"] for e in record["seeded"]},
                         {p for p, (c, _) in FILES.items() if c == "seed"})
        self.assertTrue(next(e for e in record["managed"] if e["path"] == "tools/run.sh")["exec"])
        self.assertFalse(os.path.exists(os.path.join(self.target, "MANIFEST.json")))
        self.assertFalse(os.path.exists(os.path.join(self.target, "README.md")))
        problems, _ = install_mod.verify(self.target, source_repo=self.lifeos)
        self.assertEqual(problems, [])

    def test_seeds_are_kept_on_a_second_install(self):
        rev = make_lifeos_repo(self.lifeos)
        write(self.target, "CLAUDE.md", "mine\n")
        write(self.target, ".aios/config.json", '{"time_zone": "UTC"}\n')
        code, out, err = self.install(rev)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.target, "CLAUDE.md")) as fh:
            self.assertEqual(fh.read(), "mine\n")
        with open(os.path.join(self.target, ".aios/config.json")) as fh:
            self.assertEqual(fh.read(), '{"time_zone": "UTC"}\n')
        # A re-run refuses (there's a record) and changes nothing.
        code, _out, err = self.install(rev)
        self.assertNotEqual(code, 0)
        self.assertIn("already has an install record", err)
        with open(os.path.join(self.target, "CLAUDE.md")) as fh:
            self.assertEqual(fh.read(), "mine\n")

    def test_tampered_managed_file_is_refused_before_any_write(self):
        def tamper(pkg, manifest):
            write(pkg, "tools/check.mjs", "export const ok = false;\n")
        rev = make_lifeos_repo(self.lifeos, tamper)
        code, _out, err = self.install(rev)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("does not match the manifest: tools/check.mjs", err)
        self.assertFalse(os.path.exists(os.path.join(self.target, ".aios", "install.json")))
        self.assertFalse(os.path.exists(os.path.join(self.target, "CLAUDE.md")))

    def test_edited_managed_file_fails_verify(self):
        rev = make_lifeos_repo(self.lifeos)
        self.assertEqual(self.install(rev)[0], 0)
        write(self.target, "tools/check.mjs", "edited\n")
        problems, _ = install_mod.verify(self.target)
        self.assertTrue(any("modified managed file: tools/check.mjs" in p for p in problems), problems)

    def test_unlisted_file_and_unsafe_paths_are_refused(self):
        def extra(pkg, manifest):
            write(pkg, "tools/extra.mjs", "x\n")
            manifest["files"].append({"path": "../escape", "class": "seed", "mode": "0644", "sha256": "0" * 64})
            manifest["files"].append({"path": ".aios/install.json", "class": "seed", "mode": "0644",
                                      "sha256": "0" * 64})
        rev = make_lifeos_repo(self.lifeos, extra)
        code, _out, err = self.install(rev)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("tools/extra.mjs is in the package but not in its manifest", err)
        self.assertIn("unsafe path '../escape'", err)
        self.assertIn(".aios/install.json is the installer's own path", err)
        self.assertFalse(os.path.exists(self.target) and os.listdir(self.target))

    def test_link_in_the_package_is_refused(self):
        def link(pkg, manifest):
            os.symlink("/etc/hosts", os.path.join(pkg, "notes", "hosts"))
        rev = make_lifeos_repo(self.lifeos, link)
        code, _out, err = self.install(rev)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("holds links", err)

    def test_policy_must_not_contradict_the_manifest(self):
        def contradict(pkg, manifest):
            manifest["files"] = [dict(f, **{"class": "managed"}) if f["path"] == "notes/README.md"
                                 else dict(f, **{"class": "seed"}) if f["path"] == "tools/check.mjs" else f
                                 for f in manifest["files"]]
        rev = make_lifeos_repo(self.lifeos, contradict)
        code, _out, err = self.install(rev)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("lets the operator write managed file notes/README.md", err)
        self.assertIn("protects seed file tools/check.mjs", err)

    def test_unknown_package_is_refused(self):
        rev = make_lifeos_repo(self.lifeos)
        code, _out, err = self.cli("install", "--package", "some-other-package", "--repo", self.lifeos,
                                   "--rev", rev, "--target", self.target)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("isn't one this installer accepts", err)
        self.assertFalse(os.path.exists(os.path.join(self.target, ".aios")))

    def test_manifest_naming_another_package_is_refused(self):
        def rename(pkg, manifest):
            manifest["package"] = "ff-aios-starter"
        rev = make_lifeos_repo(self.lifeos, rename)
        code, _out, err = self.install(rev)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("not life-os-release-1", err)

    def test_needs_a_commit_not_the_working_copy(self):
        make_lifeos_repo(self.lifeos)
        code, _out, err = self.cli("install", "--package", "life-os-release-1", "--repo", self.lifeos,
                                   "--target", self.target)
        self.assertEqual(code, util.EXIT_PACKAGE, err)
        self.assertIn("--rev", err)
        code, _out, err = self.install("--output=/tmp/x")
        self.assertEqual(code, util.EXIT_PACKAGE, err)

    def test_record_validator_accepts_exactly_the_two_packages(self):
        self.assertEqual(packages.COMPATIBLE, ("ff-aios-starter", "life-os-release-1"))
        base = {"schema": install_mod.INSTALL_SCHEMA, "release": {}}
        for name in packages.COMPATIBLE:
            self.assertFalse([p for p in install_mod._record_shape_problems(dict(base, package=name))
                              if "package" in p])
        self.assertTrue([p for p in install_mod._record_shape_problems(dict(base, package="other"))
                         if "package" in p])


if __name__ == "__main__":
    unittest.main()
