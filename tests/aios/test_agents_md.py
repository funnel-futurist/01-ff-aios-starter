"""Managed bootstrap integrity without snapshotting client-owned context.

The startup context read is performed by a normal tools-enabled host session. Deterministic
checks cover generation, privacy and managed drift; fresh-host reads/refusals need their own
actual session evidence and are not model-generation jobs in CI.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

import harness

sys.path.insert(0, harness.AIOS_DIR)
from aioslib import adapters, release

ROOT = harness.REPO_ROOT
CORE = ".aios/operator_core/OPERATOR_CORE.md"


def read(rel, root=ROOT):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


class Rendering(unittest.TestCase):
    def test_shipped_file_matches_managed_bootstrap(self):
        self.assertEqual(read("AGENTS.md"), adapters.render_agents_md(ROOT))

    def test_it_stays_inside_codex_default_instruction_budget(self):
        self.assertLess(len(read("AGENTS.md").encode("utf-8")), 32 * 1024)


class Drift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        for rel in ("CLAUDE.md", CORE, "00_AIOS/routing.md", "AGENTS.md"):
            dst = os.path.join(self.tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(ROOT, rel), dst)

    def test_a_copy_of_the_tree_is_in_sync(self):
        self.assertIsNone(adapters.agents_md_problem(self.tmp))

    def test_client_customization_does_not_drift_or_resnapshot_bootstrap(self):
        before = read("AGENTS.md", self.tmp)
        with open(os.path.join(self.tmp, "CLAUDE.md"), "a") as fh:
            fh.write("\nClient context marker: fixture-only-C9\n")
        client = read("CLAUDE.md", self.tmp)
        self.assertIsNone(adapters.agents_md_problem(self.tmp))
        self.assertEqual(adapters.render_agents_md(self.tmp), before)
        self.assertNotIn("fixture-only-C9", before)
        self.assertEqual(read("CLAUDE.md", self.tmp), client)

    def test_managed_core_context_is_not_copied_into_the_bootstrap(self):
        with open(os.path.join(self.tmp, CORE), "a") as fh:
            fh.write("\nA changed managed-core fixture rule.\n")
        self.assertIsNone(adapters.agents_md_problem(self.tmp))
        self.assertNotIn("A changed managed-core fixture rule.", adapters.render_agents_md(self.tmp))
        self.assertNotIn(read(CORE, self.tmp), adapters.render_agents_md(self.tmp))

    def test_unavailable_import_is_not_read_during_bootstrap_generation(self):
        with open(os.path.join(self.tmp, "CLAUDE.md"), "a") as fh:
            fh.write("\n@missing-context.md\n")
        # Runtime must refuse the unreadable source. Rendering is not that runtime read.
        self.assertEqual(adapters.render_agents_md(self.tmp), read("AGENTS.md", self.tmp))

    def test_external_context_cannot_be_exported_by_rendering(self):
        with tempfile.TemporaryDirectory() as outside:
            external = os.path.join(outside, "outside.md")
            with open(external, "w") as fh:
                fh.write("outside-context-fixture-DO-NOT-EXPORT")
            with open(os.path.join(self.tmp, "CLAUDE.md"), "a") as fh:
                fh.write("\n@%s\n" % external)
            client = read("CLAUDE.md", self.tmp)
            self.assertNotIn("outside-context-fixture-DO-NOT-EXPORT", adapters.render_agents_md(self.tmp))
            self.assertEqual(read("CLAUDE.md", self.tmp), client)

    def test_a_hand_edited_managed_bootstrap_is_still_reported(self):
        with open(os.path.join(self.tmp, "AGENTS.md"), "a") as fh:
            fh.write("\nA hand edit.\n")
        self.assertIn("not the managed bootstrap", adapters.agents_md_problem(self.tmp))


class Declared(unittest.TestCase):
    def test_agents_md_ships_managed_and_is_declared_for_codex(self):
        spec = json.loads(read("release/package_spec.json"))
        self.assertEqual(release.classify(spec, "AGENTS.md"), "managed")
        self.assertIn("AGENTS.md", json.loads(read("release/adapters.json"))["tools"]["codex"]["files"])


if __name__ == "__main__":
    unittest.main()
