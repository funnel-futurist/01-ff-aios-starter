"""AGENTS.md: the instructions other tools read, generated so they can't drift from CLAUDE.md.

Codex reads AGENTS.md as plain text and, per its docs, concatenates files rather than following
links or `@` imports. So the shipped file is CLAUDE.md with each imported file (the operator
core) inlined, the same way Claude Code inlines it, and it must equal that rendering byte for
byte. It ships as a managed file, so `verify` reports a hand edit in a client workspace.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

import harness

sys.path.insert(0, harness.AIOS_DIR)

from aioslib import adapters, release  # noqa: E402
from aioslib.util import Refusal  # noqa: E402

ROOT = harness.REPO_ROOT
CORE = ".aios/operator_core/OPERATOR_CORE.md"


def read(rel, root=ROOT):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


class Rendering(unittest.TestCase):

    def test_the_shipped_file_is_the_rendering_of_claude_md_and_its_imports(self):
        self.assertEqual(read("AGENTS.md"), adapters.render_agents_md(ROOT))

    def test_the_operator_core_is_inlined_and_no_import_line_survives(self):
        text = read("AGENTS.md")
        self.assertIn(read(CORE).rstrip("\n"), text)
        self.assertNotIn("\n@.aios/", text)
        version = json.loads(read(".aios/operator_core/manifest.json"))["version"]
        self.assertIn("# AIOS Operator Core v%s" % version, text)

    def test_it_stays_inside_codex_default_instruction_budget(self):
        # Codex stops adding instruction files at project_doc_max_bytes, 32 KiB by default.
        self.assertLess(len(read("AGENTS.md").encode("utf-8")), 32 * 1024)


class Drift(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for rel in ("CLAUDE.md", CORE, "00_AIOS/routing.md", "AGENTS.md"):
            dst = os.path.join(self.tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), dst)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_a_copy_of_the_tree_is_in_sync(self):
        self.assertIsNone(adapters.agents_md_problem(self.tmp))

    def test_changing_claude_md_without_rendering_is_reported(self):
        with open(os.path.join(self.tmp, "CLAUDE.md"), "a", encoding="utf-8") as fh:
            fh.write("\n- a new rule\n")
        self.assertIn("not the rendering", adapters.agents_md_problem(self.tmp))

    def test_a_new_core_version_without_rendering_is_reported(self):
        with open(os.path.join(self.tmp, CORE), "a", encoding="utf-8") as fh:
            fh.write("- one more rule\n")
        self.assertIn("not the rendering", adapters.agents_md_problem(self.tmp))

    def test_a_broken_import_is_reported_not_raised_by_the_check(self):
        with open(os.path.join(self.tmp, "CLAUDE.md"), "a", encoding="utf-8") as fh:
            fh.write("\n@missing.md\n")
        self.assertIn("can't be rendered", adapters.agents_md_problem(self.tmp))

    def test_an_import_outside_the_tree_is_refused(self):
        with open(os.path.join(self.tmp, "CLAUDE.md"), "a", encoding="utf-8") as fh:
            fh.write("\n@../outside.md\n")
        with self.assertRaises(Refusal):
            adapters.render_agents_md(self.tmp)


class Declared(unittest.TestCase):

    def test_agents_md_ships_managed_and_is_declared_for_codex(self):
        spec = json.loads(read("release/package_spec.json"))
        self.assertEqual(release.classify(spec, "AGENTS.md"), "managed")
        codex = json.loads(read("release/adapters.json"))["tools"]["codex"]
        self.assertIn("AGENTS.md", codex["files"])


if __name__ == "__main__":
    unittest.main()
