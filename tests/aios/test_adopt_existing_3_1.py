"""Starter 3.1: adopting a release into an instance that already exists (G81), and founder-lane
reviewers declared separately from founder status (G98).

Phoenix, 2026-10-14 (ai-os #532): "safe Starter adoption into FF's existing AIOS with NO OVERWRITE.
... Implement approved components/explicit overrides with rehearsal and rollback; do not infer
existing adoption works already." Phoenix, 2026-10-15 (G98): "no-overwrite 18-file adoption with
business founder role separate from CODEOWNER permission."
"""

import json
import os
import shutil
import sys
import unittest

import harness
from harness import Sandbox, run_git, write

sys.path.insert(0, harness.AIOS_DIR)
from aioslib import governance, install as install_mod, util  # noqa: E402
from aioslib.util import Refusal  # noqa: E402

from test_layout_3_0 import MAP_LINE, bump_to_v3, diff, snapshot  # noqa: E402

FF_ROLES = json.loads(json.dumps(harness.ROLES))
FF_ROLES["roles"]["operator"]["paths_denied"] = [".github/**", "CLAUDE.md"]

# The fixture release ships 12 paths. The instance keeps its own CLAUDE.md, README.md, .gitignore,
# settings and role policy; adopts the runtime-ish files it doesn't have; excludes the rest.
PLAN = {
    "schema": "ff-aios-starter/adoption@1",
    "adopt": ["scripts/team/**", "START_HERE.md", ".aios/.gitignore", ".claude/skills/**"],
    "instance_owned": [".claude/settings.json", ".aios/roles.json", "CLAUDE.md", "README.md", ".gitignore"],
    "exclude": ["templates/**", "01_Foundations/**", "06_Communication/**"],
}
ADOPTED = [".aios/.gitignore", ".claude/skills/start-my-day/SKILL.md", "START_HERE.md",
           "scripts/team/git-safety-check.sh"]


class Existing(Sandbox):
    """A company's own repository that was never a Starter copy, then an adoption into it."""

    def setUp(self):
        super(Existing, self).setUp()
        self.v = harness.approve(harness.build_manifest(self.source, self.rev, "3.0.0"))
        t = self.target
        write(t, "CLAUDE.md", "# OUR OWN brain\nOur rules, not the Starter's.\n")
        write(t, "README.md", "# our company repo\n")
        write(t, ".gitignore", "node_modules/\n.env\n")
        write(t, ".claude/settings.json", json.dumps({"permissions": {"deny": ["Read(secrets/**)"]}}))
        write(t, ".aios/roles.json", json.dumps(FF_ROLES, indent=2))
        write(t, "01_Foundations/our_own.md", "# a folder of ours with a 2.x name\n")
        write(t, "06_Clients/acme/notes.md", "# client work\n")
        os.makedirs(os.path.join(t, "empty_of_ours"))
        self.write_plan(PLAN)
        self.commit("our repo, before any Starter")

    def write_plan(self, plan):
        write(self.target, ".aios/adoption.json", json.dumps(plan, indent=2))

    def commit(self, msg):
        t = self.target
        if not os.path.isdir(os.path.join(t, ".git")):
            run_git(t, "init", "-q", "-b", "main")
            run_git(t, "config", "user.email", "ff@example.com")
            run_git(t, "config", "user.name", "ff")
        run_git(t, "add", "-A")
        run_git(t, "commit", "-qm", msg)

    def adopt(self, manifest=None, **kw):
        return install_mod.adopt_existing(self.target, manifest or self.v, self.source,
                                          kw.pop("config", None) or harness.config(), **kw)

    def refuses_unchanged(self, fn, *args, **kw):
        before = snapshot(self.target)
        with self.assertRaises(Refusal) as ctx:
            fn(*args, **kw)
        self.assertEqual(diff(before, snapshot(self.target)), [], "a refusal changed the instance")
        return ctx.exception


class Adoption(Existing):

    def test_it_creates_only_what_it_adopts_and_writes_nothing_of_the_instances(self):
        before = snapshot(self.target)
        record = self.adopt()
        after = snapshot(self.target)
        changed = [k for k in before if before[k] != after.get(k)]
        self.assertEqual([k for k in changed if k != "<git status>"], [], changed)
        new_files = sorted(k for k in after if k not in before and os.path.isfile(os.path.join(self.target, k)))
        self.assertEqual(new_files, sorted(ADOPTED + [".aios/config.json", ".aios/install.json"]))
        self.assertEqual(sorted(e["path"] for e in record["adoption"]["created"]), ADOPTED)
        self.assertEqual(install_mod.verify(self.target)[0], [])
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])

    def test_an_adopted_executable_keeps_its_bit(self):
        os.chmod(os.path.join(self.source, "scripts/team/git-safety-check.sh"), 0o755)
        rev = harness.bump_source(self.source, {}, "an executable")
        self.adopt(harness.approve(harness.build_manifest(self.source, rev, "3.0.0")))
        self.assertTrue(os.stat(os.path.join(self.target, "scripts/team/git-safety-check.sh")).st_mode & 0o100)


class RefusesWithNothingChanged(Existing):

    def plan_without(self, cls, item):
        plan = json.loads(json.dumps(PLAN))
        plan[cls] = [x for x in plan[cls] if x != item]
        return plan

    def test_a_path_the_plan_doesnt_classify(self):
        self.write_plan(self.plan_without("exclude", "templates/**"))
        self.commit("forgot one")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("templates/governance/CODEOWNERS.template: not in the plan", "\n".join(exc.details))

    def test_a_path_in_two_lists(self):
        plan = json.loads(json.dumps(PLAN))
        plan["exclude"].append("START_HERE.md")
        self.write_plan(plan)
        self.commit("twice")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("START_HERE.md: in more than one list (adopt, exclude)", exc.details)

    def test_a_catch_all_can_never_silently_classify_the_rest(self):
        plan = json.loads(json.dumps(PLAN))
        plan["exclude"] = ["**"]
        self.write_plan(plan)
        self.commit("catch-all")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("in more than one list", "\n".join(exc.details))

    def test_an_adopted_path_that_already_exists(self):
        write(self.target, "START_HERE.md", "# ours already\n")
        self.commit("ours")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("adoption never overwrites", exc.message)

    def test_a_path_declared_the_instances_that_isnt_there(self):
        os.remove(os.path.join(self.target, "README.md"))
        self.commit("no readme")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("don't exist", exc.message)

    def test_uncommitted_work(self):
        write(self.target, "06_Clients/acme/draft.md", "unsaved\n")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("uncommitted", exc.message)

    def test_no_role_policy_of_its_own(self):
        os.remove(os.path.join(self.target, ".aios/roles.json"))
        plan = self.plan_without("instance_owned", ".aios/roles.json")
        plan["exclude"].append(".aios/roles.json")
        self.write_plan(plan)
        self.commit("no policy")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("role policy", exc.message)

    def test_no_plan_and_a_plan_outside_the_instance(self):
        os.remove(os.path.join(self.target, ".aios/adoption.json"))
        self.commit("no plan")
        self.refuses_unchanged(self.adopt)
        self.refuses_unchanged(self.adopt, plan_rel="../elsewhere.json")

    def test_a_linked_folder_on_the_way(self):
        outside = os.path.join(self.tmp, "outside")
        os.makedirs(outside)
        os.symlink(outside, os.path.join(self.target, "scripts"))
        self.commit("scripts is a link")
        self.refuses_unchanged(self.adopt)
        self.assertEqual(os.listdir(outside), [])

    def test_a_different_org_config(self):
        write(self.target, ".aios/config.json", json.dumps(dict(harness.config(), org_id="someone-else")))
        self.commit("their config")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("different organization config", exc.message)

    def test_an_already_pinned_workspace(self):
        self.adopt()
        self.commit("adopted")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("use upgrade", exc.message)

    def test_an_unapproved_release(self):
        draft = harness.build_manifest(self.source, self.rev, "3.0.0")
        self.refuses_unchanged(self.adopt, draft)


class NeverMovesOrAddsALine(Existing):
    """3.0's folder move would relocate the instance's own 01_Foundations; its seed line would edit
    the instance's own CLAUDE.md. Neither ever happens to an existing instance."""

    def v3_plan(self):
        return {"schema": "ff-aios-starter/adoption@1",
                "adopt": ["scripts/team/**", "START_HERE.md", ".aios/.gitignore", ".claude/skills/**"],
                "instance_owned": [".claude/settings.json", ".aios/roles.json", "CLAUDE.md", "README.md",
                                   ".gitignore"],
                "exclude": ["templates/**", "00_AIOS/**", "02_Team_Ops/**", "04_Attention/**",
                            "release/**"]}

    def test_adopting_and_upgrading_a_release_with_a_folder_move(self):
        rev3 = bump_to_v3(self.source)
        v3 = harness.approve(harness.build_manifest(self.source, rev3, "3.0.0"))
        self.assertTrue(v3.get("layout") and v3.get("seed_lines"))
        self.write_plan(self.v3_plan())
        self.commit("plan for 3.0")
        ours = snapshot(self.target)
        self.adopt(v3)
        self.commit("adopted 3.0")
        rev31 = harness.bump_source(self.source, {"scripts/team/new_tool.sh": "#!/bin/sh\necho new\n",
                                                  "START_HERE.md": "# start here\n3.1.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev31, "3.1.0"))
        install_mod.upgrade(self.target, v31, self.source)
        after = snapshot(self.target)
        for rel in ("01_Foundations/our_own.md", "CLAUDE.md", "06_Clients/acme/notes.md"):
            self.assertEqual(ours[rel], after[rel], rel)
        with open(os.path.join(self.target, "CLAUDE.md")) as fh:
            self.assertNotIn(MAP_LINE, fh.read())
        self.assertFalse(os.path.exists(os.path.join(self.target, "00_AIOS")))
        self.assertTrue(os.path.isfile(os.path.join(self.target, "scripts/team/new_tool.sh")))
        record = install_mod.load_record(self.target)
        self.assertNotIn("layout", record)
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])


class Upgrades(Existing):

    def adopted(self):
        self.adopt()
        self.commit("adopted")

    def test_a_new_path_the_plan_doesnt_classify_refuses(self):
        self.adopted()
        rev = harness.bump_source(self.source, {"docs/new_guide.md": "# new\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        exc = self.refuses_unchanged(install_mod.upgrade, self.target, v31, self.source)
        self.assertIn("docs/new_guide.md: not in the plan", "\n".join(exc.details))

    def test_only_adopted_paths_are_written(self):
        self.adopted()
        rev = harness.bump_source(self.source, {".claude/settings.json": "{}\n", "README.md": "# theirs\n",
                                                "START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        install_mod.upgrade(self.target, v31, self.source)
        with open(os.path.join(self.target, ".claude/settings.json")) as fh:
            self.assertIn("secrets", fh.read())  # the instance's, untouched
        with open(os.path.join(self.target, "README.md")) as fh:
            self.assertEqual(fh.read(), "# our company repo\n")
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertEqual(fh.read(), "# start here\nnew.\n")  # adopted, so upgraded

    def test_a_file_the_instance_stops_adopting_stays_as_its_own(self):
        self.adopted()
        plan = json.loads(json.dumps(PLAN))
        plan["adopt"].remove("START_HERE.md")
        plan["instance_owned"].append("START_HERE.md")
        self.write_plan(plan)
        self.commit("START_HERE.md is ours now")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        record = install_mod.upgrade(self.target, v31, self.source)
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertEqual(fh.read(), "# start here\nthe two commands.\n")  # kept, not deleted or updated
        self.assertNotIn("START_HERE.md", [e["path"] for e in record["managed"]])

    def test_an_upgrade_then_rollback_returns_the_adopted_instance(self):
        self.adopted()
        before = snapshot(self.target)
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        install_mod.upgrade(self.target, harness.approve(harness.build_manifest(self.source, rev, "3.1.0")),
                            self.source)
        install_mod.rollback(self.target)
        backups = set(os.listdir(os.path.join(self.target, ".aios", "backups")))
        self.assertEqual(diff(before, snapshot(self.target, backups=())), [])
        self.assertTrue(backups)


class Rollback(Existing):

    def test_rollback_undoes_a_finished_adoption_exactly(self):
        before = snapshot(self.target)
        self.adopt()
        _r, summary, how = install_mod.rollback(self.target)
        self.assertIsNone(summary["release_id"])
        self.assertIn("adoption was undone", how)
        self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_rollback_leaves_an_adopted_file_the_instance_has_changed(self):
        self.adopt()
        write(self.target, "START_HERE.md", "# start here, edited by us\n")
        _r, _s, how = install_mod.rollback(self.target)
        self.assertIn("START_HERE.md changed", how)
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertIn("edited by us", fh.read())

    def test_a_killed_adoption_is_undone_by_the_next_rollback(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        for point in ("adopt.mid_write", "adopt.before_record"):
            with self.subTest(point=point):
                before = snapshot(self.target)
                code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                        "--config", cfg, "--repo", self.source,
                                        env={"AIOS_FAULT": "crash:" + point})
                self.assertEqual(code, 137)
                self.assertTrue(os.path.isfile(install_mod.journal_path(self.target)))
                code, out, err = self.cli("rollback", "--target", self.target)
                self.assertEqual(code, 0, out + err)
                self.assertIn("interrupted adoption was undone", out)
                self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_the_cli_adopts_and_says_what_it_did(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, out, err = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                  "--config", cfg, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("created:  4 file(s)", out)
        self.assertIn("no folder move, no seed line", out)
        code, _o, err = self.cli("adopt", "--release", rel, "--target", self.target, "--config", cfg,
                                 "--repo", self.source, "--plan", ".aios/adoption.json")
        self.assertNotEqual(code, 0)


class VerifyAgainstTheRelease(Existing):

    def test_an_adopted_file_dropped_from_record_and_disk_is_caught(self):
        record = self.adopt()
        record["managed"] = [e for e in record["managed"] if e["path"] != "START_HERE.md"]
        util.write_json(install_mod.install_record_path(self.target), record)
        os.remove(os.path.join(self.target, "START_HERE.md"))
        problems, _ = install_mod.verify(self.target, source_repo=self.source)
        self.assertTrue(any("START_HERE.md" in p for p in problems), problems)

    def test_the_instances_own_files_arent_expected(self):
        self.adopt()
        problems, _ = install_mod.verify(self.target, source_repo=self.source)
        self.assertEqual(problems, [])  # .claude/settings.json etc. are managed by the release, not here


CODEOWNERS = ("# aios-codeowners-for: acme/acme-aios\n"
              "/.github/   @acme-founder @acme-va @acme-lead\n"
              "/CLAUDE.md  @acme-founder @acme-va @acme-lead\n")


class LaneReviewers(Sandbox):
    """G98: who may approve the founder lane is declared apart from who is a founder."""

    def setUp(self):
        super(LaneReviewers, self).setUp()
        write(self.target, ".github/CODEOWNERS", CODEOWNERS)
        self.config = harness.config(people=[
            {"github": "acme-founder", "role": "founder", "display_name": "F"},
            {"github": "acme-va", "role": "operator", "display_name": "V"},
            {"github": "acme-lead", "role": "operator", "display_name": "L"}])
        self.policy = json.loads(json.dumps(FF_ROLES))

    def check(self):
        return governance.founder_review_local(self.target, self.policy, self.config)

    def test_without_a_declaration_founder_status_decides_and_operators_fail_it(self):
        results = self.check()
        self.assertTrue(all(st == "FAIL" for st, _d in results), results)
        self.assertIn("not only founders", results[0][1])

    def test_declared_reviewers_pass_without_becoming_founders(self):
        self.policy["founder_lane_reviewers"] = ["@acme-founder", "@acme-va", "@acme-lead"]
        results = self.check()
        self.assertEqual([st for st, _d in results if st != "INFO"], ["PASS", "PASS"], results)
        info = [d for st, d in results if st == "INFO"][0]
        self.assertIn("not founder status", info)
        self.assertFalse(any(" founders" in d or "a founder" in d for _s, d in results), results)
        self.assertEqual(governance.founders_of(self.config), ["@acme-founder"])  # status unchanged

    def test_declared_but_missing_one_owner_fails_with_the_reviewer_wording(self):
        self.policy["founder_lane_reviewers"] = ["@acme-founder", "@acme-va"]
        results = self.check()
        self.assertTrue(any("not only approved founder-lane reviewers" in d for _s, d in results), results)

    def test_a_reviewer_outside_the_people_map_or_a_team_is_refused(self):
        for bad in (["@someone-else"], ["@acme/leads"], [], "acme-founder"):
            with self.subTest(bad=bad):
                self.policy["founder_lane_reviewers"] = bad
                results = self.check()
                self.assertTrue(results and all(st == "FAIL" for st, _d in results), results)


if __name__ == "__main__":
    unittest.main()
