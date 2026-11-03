"""Prepublication check: identical approval trees do not establish payload ancestry."""

import json

import harness
from harness import Sandbox
from aioslib import util


class ReleaseCarrierAncestry(Sandbox):
    def test_exact_tree_without_pin_ancestry_is_refused_before_publication(self):
        # Fixture approval only; no real release, remote ref or installation is written.
        man = harness.approve(harness.build_manifest(
            self.source, self.rev, "1.0.1", record=None))
        carrier = harness.bump_source(self.source, {
            "releases/%s.json" % man["release_id"]: json.dumps(man, indent=2) + "\n",
        }, "fixture approval carrier")
        tree = util.git(self.source, ["rev-parse", carrier + "^{tree}"])
        unrelated = util.git(self.source, ["commit-tree", tree, "-m", "same tree, no pin parent"])
        self.assertEqual(util.git(self.source, ["rev-parse", unrelated + "^{tree}"]), tree)

        # Full commit IDs are accepted by the official CLI: qualify BEFORE creating any tag.
        code, out, err = self.cli("release", "check-tag", unrelated, "--release-id",
                                  man["release_id"], "--repo", self.source)
        self.assertEqual(code, util.EXIT_PACKAGE, out + err)
        problems = [line.strip() for line in out.splitlines() if line.startswith("  - ")]
        self.assertEqual(problems, [
            "- the pinned commit %s is not an ancestor of the tag's commit %s"
            % (self.rev[:12], unrelated[:12]),
        ], out + err)

        code, out, err = self.cli("release", "check-tag", carrier, "--release-id",
                                  man["release_id"], "--repo", self.source)
        self.assertEqual(code, util.EXIT_OK, out + err)
        self.assertIn("byte for byte", out)

        # Correct ancestry must still refuse changed package bytes.
        drifted = harness.bump_source(self.source, {"START_HERE.md": "changed after approval\n"})
        code, out, err = self.cli("release", "check-tag", drifted, "--release-id",
                                  man["release_id"], "--repo", self.source)
        self.assertEqual(code, util.EXIT_PACKAGE, out + err)
        self.assertIn("differs from the pin at START_HERE.md", out)
        self.assertNotIn("is not an ancestor", out)
