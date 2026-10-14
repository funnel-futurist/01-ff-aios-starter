"""The shipped operator core is the exact file its manifest pins, and only the client edition.

The core is vendored from its canonical source and edited in three declared places (see
`.aios/operator_core/manifest.json`). Nothing tied the manifest to the bytes until 1.2.0, so a
hand edit or a half-applied re-vendor could ship under the old pins and nobody would notice.
"""

import hashlib
import json
import os
import sys
import unittest

import harness

sys.path.insert(0, harness.AIOS_DIR)

from aioslib import release  # noqa: E402

ROOT = harness.REPO_ROOT
CORE_REL = ".aios/operator_core/OPERATOR_CORE.md"
MANIFEST_REL = ".aios/operator_core/manifest.json"


def read(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


class OperatorCorePins(unittest.TestCase):

    def setUp(self):
        self.core = read(CORE_REL)
        self.manifest = json.loads(read(MANIFEST_REL))
        self.lines = self.core.decode("utf-8").splitlines()

    def test_manifest_pins_the_shipped_bytes(self):
        self.assertEqual(hashlib.sha256(self.core).hexdigest(), self.manifest["sha256"])

    def test_version_marker_title_and_manifest_agree(self):
        version = self.manifest["version"]
        self.assertEqual(self.lines[0], "<!-- aios-operator-core v%s -->" % version)
        self.assertEqual(self.lines[2], "# AIOS Operator Core v%s" % version)

    def test_it_is_the_declared_client_edition(self):
        self.assertEqual(self.manifest["edition"], "client")
        self.assertTrue(self.lines[1].startswith("<!-- Client edition."), self.lines[1])
        self.assertEqual(len(self.manifest["differences"]), 3)

    def test_the_writing_standard_points_at_files_the_client_has(self):
        text = self.core.decode("utf-8")
        for rel in ("03_Quality_Control/qc_preferences.md", ".claude/skills/humanize/SKILL.md"):
            self.assertIn(rel, text)
            self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), rel)
        # The source edition's section 9 names a repository clients can't open.
        self.assertNotIn("ff-creation-system", text)
        self.assertNotIn("anti-ai-human-writing", text)

    def test_core_and_manifest_ship_as_managed_and_the_import_line_is_declared(self):
        spec = json.loads(read("release/package_spec.json"))
        self.assertEqual(release.classify(spec, CORE_REL), "managed")
        self.assertEqual(release.classify(spec, MANIFEST_REL), "managed")
        self.assertIn({"path": "CLAUDE.md", "line": self.manifest["import_line"]},
                      spec["seed_lines"])
        claude = read("CLAUDE.md").decode("utf-8").splitlines()
        self.assertEqual(claude.count(self.manifest["import_line"]), 1)


if __name__ == "__main__":
    unittest.main()
