"""Native discovery entries share workflow bodies rather than copying them.

These tests cover package wiring and authoring refusal. Actual host discovery and invocation
need the installed Codex catalog/session receipts, not just a file-content assertion.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import harness

sys.path.insert(0, harness.AIOS_DIR)
from aioslib import adapters, release, util


class NativeEntries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        for name in adapters.NATIVE_CODEX_SKILLS:
            harness.write(self.root, ".claude/skills/%s/SKILL.md" % name,
                          "---\nname: %s\ndescription: Use for %s.\n---\n\nCanonical body.\n" % (name, name))

    def generate(self):
        entries = adapters.render_codex_skills(self.root)
        for path, text in entries.items():
            harness.write(self.root, path, text)
        return list(entries)

    def test_a_workflow_body_change_is_consumed_through_the_same_entry(self):
        paths = self.generate()
        source = ".claude/skills/start/SKILL.md"
        with open(os.path.join(self.root, source), "a") as fh:
            fh.write("\nNew canonical behavior with references/current.md.\n")
        self.assertEqual(adapters.codex_skill_problems(self.root, paths), [])
        entry = adapters.render_codex_skills(self.root)[".agents/skills/start/SKILL.md"]
        self.assertIn(source, entry)
        self.assertIn(".claude/skills/start/", entry)
        self.assertNotIn("New canonical behavior", entry)

    def test_changed_discovery_metadata_is_reported_until_regenerated(self):
        paths = self.generate()
        source = ".claude/skills/start/SKILL.md"
        harness.write(self.root, source, "---\nname: start\ndescription: A changed trigger.\n---\nBody\n")
        self.assertEqual(len(adapters.codex_skill_problems(self.root, paths)), 1)
        self.generate()
        self.assertEqual(adapters.codex_skill_problems(self.root, paths), [])

    def test_missing_or_malformed_source_refuses_before_rendering(self):
        source = ".claude/skills/review-queue/SKILL.md"
        for text in ("# no frontmatter", "---\nname: wrong\ndescription: Trigger\n---\n", "---\nname: review-queue\ndescription: >\n  hidden\n---\n"):
            harness.write(self.root, source, text)
            with self.assertRaises(util.Refusal):
                self.generate()
            self.assertFalse(os.path.exists(os.path.join(self.root, ".agents")))
        os.remove(os.path.join(self.root, source))
        with self.assertRaises(util.Refusal):
            self.generate()

    def test_linked_source_or_destination_cannot_read_or_write_another_tree(self):
        with tempfile.TemporaryDirectory() as outside:
            os.symlink(outside, os.path.join(self.root, ".agents"))
            with self.assertRaises(util.Refusal):
                self.generate()
            self.assertEqual(os.listdir(outside), [])
            os.unlink(os.path.join(self.root, ".agents"))
            source = os.path.join(self.root, ".claude/skills/start/SKILL.md")
            os.remove(source)
            os.symlink(os.path.join(outside, "missing"), source)
            with self.assertRaises(util.Refusal):
                self.generate()

    def test_duplicate_and_empty_metadata_are_refused(self):
        source = ".claude/skills/start/SKILL.md"
        for text in ("---\nname: start\nname: start\ndescription: Trigger\n---\n",
                     '---\nname: start\ndescription: ""\n---\n'):
            harness.write(self.root, source, text)
            with self.assertRaises(util.Refusal):
                self.generate()

    def test_authoring_command_refuses_an_installed_target_without_changing_it(self):
        paths = self.generate()
        before = {path: Path(self.root, path).read_bytes() for path in paths}
        harness.write(self.root, ".aios/install.json", "{}\n")
        result = subprocess.run([sys.executable, os.path.join(harness.AIOS_DIR, "aios.py"),
                                 "adapters", "render-skills", "--repo", self.root],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, util.EXIT_STATE)
        for path, data in before.items():
            with open(os.path.join(self.root, path), "rb") as fh:
                self.assertEqual(fh.read(), data)


class ShippedEntries(unittest.TestCase):
    def test_all_eight_entries_ship_managed_and_are_declared(self):
        repo = harness.REPO_ROOT
        with open(os.path.join(repo, "release/package_spec.json")) as fh:
            spec = json.load(fh)
        declared = adapters.load(repo)["tools"]["codex"]["files"]
        entries = adapters.render_codex_skills(repo)
        self.assertEqual(len(entries), 8)
        for path in entries:
            self.assertIn(path, declared)
            self.assertEqual(release.classify(spec, path), "managed")
            self.assertTrue(os.path.isfile(os.path.join(repo, path)))
        self.assertEqual(adapters.codex_skill_problems(repo, declared), [])


if __name__ == "__main__":
    unittest.main()
