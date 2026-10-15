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
        # The source's own record of the release, as a real approved release has: undoing a finished
        # adoption checks it names the pin (3.1 round 24). releases/ isn't shipped, so the pin holds.
        write(self.source, "releases/%s.json" % self.v["release_id"], json.dumps(self.v, indent=2))
        run_git(self.source, "add", "-A")
        run_git(self.source, "commit", "-qm", "the release record")
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

    def forget_state(self):
        """As a machine without this workspace's local note would be (a fresh clone has none)."""
        note = os.path.join(self.target, ".aios", "backups", "state", "head.json")
        if os.path.isfile(note):
            os.remove(note)

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
        self.assertEqual(sorted(e["path"] for e in record["adoption"]["created"]),
                         sorted(ADOPTED + [".aios/config.json"]))
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
        self.assertIn("every path at once", "\n".join(exc.details))

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
        install_mod.rollback(self.target, self.source)
        backups = set(os.listdir(os.path.join(self.target, ".aios", "backups")))
        self.assertEqual(diff(before, snapshot(self.target, backups=())), [])
        self.assertTrue(backups)


class Rollback(Existing):

    def test_rollback_undoes_a_finished_adoption_exactly(self):
        before = snapshot(self.target)
        self.adopt()
        _r, summary, how = install_mod.rollback(self.target, self.source)
        self.assertIsNone(summary["release_id"])
        self.assertIn("adoption was undone", how)
        self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_rollback_leaves_an_adopted_file_the_instance_has_changed(self):
        self.adopt()
        write(self.target, "START_HERE.md", "# start here, edited by us\n")
        _r, _s, how = install_mod.rollback(self.target, self.source)
        self.assertIn("START_HERE.md changed", how)
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertIn("edited by us", fh.read())

    def test_a_killed_adoption_is_undone_by_the_next_rollback(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        for point in ("adopt.after_journal", "adopt.mid_write", "adopt.before_record"):
            with self.subTest(point=point):
                before = snapshot(self.target)
                code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                        "--config", cfg, "--repo", self.source,
                                        env={"AIOS_FAULT": "crash:" + point})
                self.assertEqual(code, 137)
                self.assertTrue(os.path.isfile(install_mod.journal_path(self.target)))
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
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


class ReviewRoundOne(Existing):
    """Gemini and Codex, 3.1 round 1."""

    def test_g1_a_file_the_plan_keeps_is_never_deleted_when_the_release_drops_it(self):
        self.adopt()
        self.commit("adopted")
        plan = json.loads(json.dumps(PLAN))
        plan["adopt"].remove("START_HERE.md")
        plan["instance_owned"].append("START_HERE.md")
        self.write_plan(plan)
        self.commit("START_HERE.md is ours now")
        run_git(self.source, "rm", "-q", "START_HERE.md")  # and the next release stops shipping it
        v31 = harness.approve(harness.build_manifest(self.source, harness.bump_source(self.source, {}, "3.1"),
                                                     "3.1.0"))
        self.assertNotIn("START_HERE.md", install_mod.upgrade_plan(self.target, v31, self.source)["removed"])
        install_mod.upgrade(self.target, v31, self.source)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "START_HERE.md")))

    def test_g1_a_file_the_plan_still_adopts_goes_when_the_release_drops_it(self):
        self.adopt()
        self.commit("adopted")
        run_git(self.source, "rm", "-q", "START_HERE.md")
        v31 = harness.approve(harness.build_manifest(self.source, harness.bump_source(self.source, {}, "3.1"),
                                                     "3.1.0"))
        self.assertIn("START_HERE.md", install_mod.upgrade_plan(self.target, v31, self.source)["removed"])
        install_mod.upgrade(self.target, v31, self.source)
        self.assertFalse(os.path.exists(os.path.join(self.target, "START_HERE.md")))

    def test_c1_a_guard_file_of_the_repositorys_own_is_never_touched(self):
        write(self.target, ".aios/backups/guard", "ours\n")
        self.commit("a file of ours at the guard's path")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("own paths", exc.message)
        with open(os.path.join(self.target, ".aios/backups/guard")) as fh:
            self.assertEqual(fh.read(), "ours\n")

    def test_c2_json_is_never_written_through_a_planted_temporary_name(self):
        outside = os.path.join(self.tmp, "outside.json")
        with open(outside, "w") as fh:
            fh.write("untouched\n")
        path = os.path.join(self.tmp, "state", "record.json")
        os.makedirs(os.path.dirname(path))
        os.symlink(outside, path + ".tmp")
        util.write_json(path, {"a": 1})
        with open(outside) as fh:
            self.assertEqual(fh.read(), "untouched\n")
        self.assertTrue(os.path.islink(path + ".tmp"))
        self.assertEqual(util.read_json(path), {"a": 1})

    def test_c3_a_file_that_appears_while_adopting_is_never_replaced(self):
        real_fault = install_mod.util.fault

        def plant(point):
            if point == "adopt.mid_write":
                write(self.target, "scripts/team/git-safety-check.sh", "someone else's, just now\n")
            real_fault(point)
        install_mod.util.fault = plant
        try:
            with self.assertRaises(Refusal) as ctx:
                self.adopt()
        finally:
            install_mod.util.fault = real_fault
        self.assertIn("appeared while this ran", ctx.exception.message)
        with open(os.path.join(self.target, "scripts/team/git-safety-check.sh")) as fh:
            self.assertEqual(fh.read(), "someone else's, just now\n")
        self.assertFalse(os.path.exists(os.path.join(self.target, ".aios/.gitignore")))  # the rest undone
        self.assertIsNone(install_mod.load_journal(self.target))

    def kill(self, point, *args):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        return self.cli(*(args or ("adopt", "--existing", "--release", rel, "--target", self.target,
                                   "--config", cfg, "--repo", self.source)),
                        env={"AIOS_FAULT": "crash:" + point})

    def test_c4_rollback_never_deletes_a_matching_file_it_didnt_write(self):
        code, _o, _e = self.kill("adopt.mid_write")
        self.assertEqual(code, 137)
        # The script isn't written yet; someone puts the release's exact bytes there by hand.
        with open(os.path.join(self.source, "scripts/team/git-safety-check.sh"), "rb") as fh:
            write(self.target, "scripts/team/git-safety-check.sh", fh.read())
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "scripts/team/git-safety-check.sh")))
        self.assertFalse(os.path.exists(os.path.join(self.target, ".aios/install.json")))

    def test_c5_a_killed_undo_is_finished_by_the_next_rollback(self):
        before = snapshot(self.target)
        self.adopt()
        for point in ("adopt.undo_before", "adopt.undo_mid"):
            with self.subTest(point=point):
                if not os.path.isfile(install_mod.install_record_path(self.target)):
                    self.adopt()
                code, _o, _e = self.kill(point, "rollback", "--target", self.target, "--repo", self.source)
                self.assertEqual(code, 137)
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertEqual(code, 0, out + err)
                self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_c5_a_dead_lock_from_before_the_journal_clears_without_a_people_map(self):
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to roll back", out)
        self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_c6_c8_rollback_compares_the_mode_the_disk_reported(self):
        record = self.adopt()
        for c in record["adoption"]["created"]:
            self.assertEqual(c["mode"], os.lstat(os.path.join(self.target, c["path"])).st_mode & 0o7777)
        os.chmod(os.path.join(self.target, ".aios/config.json"), 0o600)
        _r, _s, how = install_mod.rollback(self.target, self.source)
        self.assertIn(".aios/config.json changed permissions", how)
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".aios/config.json")))

    def test_c7_a_release_may_never_ship_the_installers_own_paths(self):
        man = json.loads(json.dumps(self.v))
        man["files"].append({"path": ".aios/txn.json", "class": "managed", "mode": "100644", "sha256": "0" * 64})
        self.assertTrue(any("installer's own state" in p for p in __import__("aioslib.release").release.check_shape(man)))
        write(self.source, ".aios/txn.json", "{}\n")
        run_git(self.source, "add", "-f", ".aios/txn.json")  # the source's own ignore rules would skip it
        rev = harness.bump_source(self.source, {}, "ships a journal")
        with self.assertRaises(Refusal) as ctx:
            harness.build_manifest(self.source, rev, "3.0.1")
        self.assertIn("installer's own state", ctx.exception.message)

    def test_c9_not_a_git_repository_and_an_uncommitted_plan(self):
        plain = os.path.join(self.tmp, "plain")
        shutil.copytree(self.target, plain, ignore=shutil.ignore_patterns(".git"))
        with self.assertRaises(Refusal) as ctx:
            install_mod.adopt_existing(plain, self.v, self.source, harness.config())
        self.assertIn("isn't a git repository", ctx.exception.message)
        write(self.target, ".gitignore", "node_modules/\n.env\n.aios/adoption.json\n")
        run_git(self.target, "rm", "-q", "--cached", ".aios/adoption.json")
        self.commit("the plan is only ignored, not committed")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("must be committed", exc.message)

    def test_c11_a_catch_all_or_a_plan_that_adopts_nothing(self):
        self.write_plan({"schema": "ff-aios-starter/adoption@1", "adopt": [], "instance_owned": [], "exclude": ["**"]})
        self.commit("catch-all only")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("every path at once", "\n".join(exc.details))
        everything = [e["path"] for e in self.v["files"]]
        owned = [p for p in everything if os.path.lexists(os.path.join(self.target, p))]
        self.write_plan({"schema": "ff-aios-starter/adoption@1", "adopt": [], "instance_owned": owned,
                         "exclude": [p for p in everything if p not in owned]})
        self.commit("adopts nothing")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("adopts no path", exc.message)


class BoundaryHonoursDeclaredReviewers(Sandbox):
    """Codex round 1, finding 10: G98 at the pull request too."""

    def setUp(self):
        super(BoundaryHonoursDeclaredReviewers, self).setUp()
        self.repo = os.path.join(self.tmp, "client")
        os.makedirs(self.repo)
        run_git(self.repo, "init", "-q", "-b", "main")
        run_git(self.repo, "config", "user.email", "t@example.com")
        run_git(self.repo, "config", "user.name", "t")
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = ["@acme-founder", "@acme-lead"]
        write(self.repo, ".aios/roles.json", json.dumps(policy, indent=2))
        write(self.repo, ".aios/config.json", json.dumps(harness.config(people=[
            {"github": "acme-founder", "role": "founder", "display_name": "F"},
            {"github": "acme-lead", "role": "operator", "display_name": "L"},
            {"github": "acme-va", "role": "operator", "display_name": "V"}]), indent=2))
        write(self.repo, "CLAUDE.md", "# rules\n")
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "-qm", "base")
        self.base = util.git(self.repo, ["rev-parse", "HEAD"])
        run_git(self.repo, "checkout", "-q", "-b", "pr")
        write(self.repo, "CLAUDE.md", "# rules, changed\n")
        run_git(self.repo, "commit", "-qam", "change")
        self.head = util.git(self.repo, ["rev-parse", "HEAD"])

    def check(self, author, approvers):
        from aioslib import boundary
        return boundary.check_pr(self.repo, self.base, self.head, author, approvers)

    def test_a_declared_reviewer_who_isnt_a_founder_satisfies_it(self):
        code, lines = self.check("acme-va", ["acme-lead"])
        self.assertEqual(code, 0, lines)

    def test_an_undeclared_operator_does_not_and_the_message_names_who_may(self):
        code, lines = self.check("acme-lead", ["acme-va"])
        self.assertNotEqual(code, 0)
        self.assertIn("approved founder-lane reviewer", "\n".join(lines))

    def test_nobody_approves_their_own_change(self):
        code, _lines = self.check("acme-lead", ["acme-lead"])
        self.assertNotEqual(code, 0)


class ReviewRoundTwo(Existing):
    """Codex, 3.1 round 2."""

    def test_r2_2_a_tracked_guard_in_a_linked_worktree_is_never_touched(self):
        write(self.target, ".aios/backups/guard", "")  # empty, but the repository's own
        run_git(self.target, "add", "-f", ".aios/backups/guard")
        self.commit("an empty file of ours at the guard's path")
        linked = os.path.join(self.tmp, "linked")
        run_git(self.target, "worktree", "add", "-q", "--detach", linked, "HEAD")
        self.assertTrue(os.path.isfile(os.path.join(linked, ".git")))  # a file, not a folder
        before = snapshot(linked)
        with self.assertRaises(Refusal) as ctx:
            install_mod.adopt_existing(linked, self.v, self.source, harness.config())
        self.assertIn("own paths", ctx.exception.message)
        self.assertEqual(diff(before, snapshot(linked)), [])

    def test_r2_4_a_kill_between_link_and_cleanup_leaves_no_temporary_copy(self):
        before = snapshot(self.target)
        backups = os.path.join(self.target, ".aios", "backups")
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.after_link"})
        self.assertEqual(code, 137)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(diff(before, snapshot(self.target)), [])
        self.assertEqual([n for n in os.listdir(backups) if n.startswith(".write-")] if os.path.isdir(backups) else [], [])

    def test_r2_5_catch_alls_are_judged_by_what_they_match(self):
        for items in (["***"], ["?*"], ["*", "*/**"], ["*", "**/*"], ["*"]):
            with self.subTest(items=items):
                plan = json.loads(json.dumps(PLAN))
                plan["exclude"] = items
                self.write_plan(plan)
                self.commit("catch-all %r" % items)
                exc = self.refuses_unchanged(self.adopt)
                self.assertIn("every path at once", "\n".join(exc.details))

    def test_r2_1_the_rehearsal_never_deletes_a_root_it_didnt_make(self):
        import subprocess
        keep = os.path.join(self.tmp, "keep")
        write(keep, "precious.txt", "mine\n")
        for name, extra in (("rehearse_310_aios.py", ["--aios", self.target]), ("rehearse_310.py", [])):
            script = os.path.join(harness.REPO_ROOT, "evidence/dispatch/p22-starter/release-3.1.0", name)
            proc = subprocess.run([sys.executable, script, keep] + extra,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(proc.returncode, 0, name)
            with open(os.path.join(keep, "precious.txt")) as fh:
                self.assertEqual(fh.read(), "mine\n", name)


class BoundaryDeclaredListIsTheWholePermission(BoundaryHonoursDeclaredReviewers):
    """Codex, 3.1 round 2: a declared list replaces founder status at the pull request too."""

    def test_a_founder_left_off_the_list_does_not_count(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = ["@acme-lead"]
        write(self.repo, ".aios/roles.json", json.dumps(policy, indent=2))
        run_git(self.repo, "checkout", "-q", "main")
        run_git(self.repo, "commit", "-qam", "only acme-lead reviews")
        self.base = util.git(self.repo, ["rev-parse", "HEAD"])
        run_git(self.repo, "checkout", "-q", "-b", "pr2")
        write(self.repo, "CLAUDE.md", "# rules, changed again\n")
        run_git(self.repo, "commit", "-qam", "change")
        self.head = util.git(self.repo, ["rev-parse", "HEAD"])
        code, _lines = self.check("acme-va", ["acme-founder"])
        self.assertNotEqual(code, 0)
        code, _lines = self.check("acme-va", ["acme-lead"])
        self.assertEqual(code, 0)

    def test_an_unusable_declaration_counts_nobody(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = ["@acme/leads"]  # a team: can't be checked
        write(self.repo, ".aios/roles.json", json.dumps(policy, indent=2))
        run_git(self.repo, "checkout", "-q", "main")
        run_git(self.repo, "commit", "-qam", "a team")
        self.base = util.git(self.repo, ["rev-parse", "HEAD"])
        run_git(self.repo, "checkout", "-q", "-b", "pr3")
        write(self.repo, "CLAUDE.md", "# rules, changed once more\n")
        run_git(self.repo, "commit", "-qam", "change")
        self.head = util.git(self.repo, ["rev-parse", "HEAD"])
        code, _lines = self.check("acme-va", ["acme-founder", "acme-lead"])
        self.assertNotEqual(code, 0)


class ReviewRoundThree(Existing):
    """Codex, 3.1 round 3."""

    def adopted(self):
        self.adopt()
        self.commit("adopted")

    def test_r3_1_reserved_paths_are_compared_as_a_mac_or_windows_disk_would(self):
        for path in (".AIOS/txn.json", ".aios\\install.json", ".Aios/Backups/x", "/.aios/lock"):
            self.assertTrue(util.is_reserved(path), path)
        self.assertFalse(util.is_reserved("scripts/aios/install.py"))
        man = json.loads(json.dumps(self.v))
        man["files"].append({"path": ".AIOS/txn.json", "class": "managed", "mode": "100644", "sha256": "0" * 64})
        from aioslib import release
        self.assertTrue(any("installer's own state" in p for p in release.check_shape(man)))

    def test_r3_2_a_null_reviewer_declaration_counts_nobody(self):
        write(self.target, ".github/CODEOWNERS", "# aios-codeowners-for: acme/acme-aios\n/CLAUDE.md @acme-founder\n")
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = None
        results = governance.founder_review_local(self.target, policy, harness.config())
        self.assertTrue(results and all(st == "FAIL" for st, _d in results), results)
        self.assertEqual(governance.lane_reviewers(policy, harness.config()), (set(), True))

    def test_r3_3_an_upgrade_refuses_a_path_the_plan_calls_the_instances_that_isnt_there(self):
        self.adopted()
        plan = json.loads(json.dumps(PLAN))
        plan["instance_owned"].append("docs/**")
        self.write_plan(plan)
        self.commit("docs are ours")
        rev = harness.bump_source(self.source, {"docs/new_guide.md": "# new\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        exc = self.refuses_unchanged(install_mod.upgrade, self.target, v31, self.source)
        self.assertIn("docs/new_guide.md: the plan says it's the instance's, but it doesn't exist",
                      "\n".join(exc.details))

    def test_r3_4_an_upgrade_refuses_a_plan_that_is_no_longer_committed(self):
        self.adopted()
        with open(os.path.join(self.target, ".gitignore"), "a") as fh:
            fh.write(".aios/adoption.json\n")
        run_git(self.target, "rm", "-q", "--cached", ".aios/adoption.json")
        self.commit("the plan is only ignored now")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        exc = self.refuses_unchanged(install_mod.upgrade, self.target, v31, self.source)
        self.assertIn("isn't committed", exc.message)

    def test_r3_5_a_seed_can_never_be_adopted(self):
        plan = json.loads(json.dumps(PLAN))
        plan["exclude"].remove("01_Foundations/**")
        plan["adopt"].append("01_Foundations/market_analysis/_workspace.md")
        self.write_plan(plan)
        self.commit("adopting a seed")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("seed", exc.message)


class BoundaryNullDeclaration(BoundaryHonoursDeclaredReviewers):

    def test_null_counts_nobody_at_the_pull_request(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = None
        write(self.repo, ".aios/roles.json", json.dumps(policy, indent=2))
        run_git(self.repo, "checkout", "-q", "main")
        run_git(self.repo, "commit", "-qam", "null")
        self.base = util.git(self.repo, ["rev-parse", "HEAD"])
        run_git(self.repo, "checkout", "-q", "-b", "pr4")
        write(self.repo, "CLAUDE.md", "# rules, changed after null\n")
        run_git(self.repo, "commit", "-qam", "change")
        self.head = util.git(self.repo, ["rev-parse", "HEAD"])
        code, _lines = self.check("acme-va", ["acme-founder"])
        self.assertNotEqual(code, 0)


class ReviewRoundFive(Existing):
    """Codex, 3.1 round 5: the guard deletes only a file it made itself."""

    def test_rollback_with_nothing_to_undo_never_deletes_a_file_at_the_guards_path(self):
        write(self.target, ".aios/backups/guard", "a file of ours\n")
        run_git(self.target, "add", "-f", ".aios/backups/guard")
        self.commit("ours, at the guard's path")
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")  # a dead holder's lock
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.target, ".aios/backups/guard")) as fh:
            self.assertEqual(fh.read(), "a file of ours\n")

    def test_the_guard_never_deletes_a_file_that_was_already_there(self):
        guard = install_mod._RecoveryGuard(self.target).path
        with open(guard, "w") as fh:
            fh.write("")
        with install_mod._RecoveryGuard(self.target):
            pass
        self.assertTrue(os.path.isfile(guard))
        os.remove(guard)
        with install_mod._RecoveryGuard(self.target):
            self.assertTrue(os.path.isfile(guard))
        self.assertFalse(os.path.exists(guard))  # made, so taken back


class ReviewRoundSix(Existing):
    """Codex, 3.1 round 6."""

    @unittest.skipIf(os.name == "nt", "Windows can't remove an open file, so nothing can replace it")
    def test_the_guard_never_deletes_a_file_that_replaced_its_own(self):
        guard = install_mod._RecoveryGuard(self.target).path
        with install_mod._RecoveryGuard(self.target):
            os.remove(guard)  # someone takes the name while this run holds the lock
            with open(guard, "w") as fh:
                fh.write("theirs\n")
        with open(guard) as fh:
            self.assertEqual(fh.read(), "theirs\n")

    def test_the_rehearsal_reads_every_checkable_rule_exact_files_included(self):
        import importlib.util
        path = os.path.join(harness.REPO_ROOT, "evidence/dispatch/p22-starter/release-3.1.0/rehearse_310_aios.py")
        spec = importlib.util.spec_from_file_location("rehearse_310_aios", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        lane, reviewers = mod.lane_from_codeowners(
            "/.github/  @a @b\n/CLAUDE.md  @a @b\n.gitignore @a\n**/*.sql @a\n.env* @a\n/docs/*/x @b\n",
            governance.parse)
        self.assertEqual(lane, [".github/**", "CLAUDE.md", ".gitignore"])
        self.assertEqual(reviewers, ["@a", "@b"])


class ReviewRoundSeven(Existing):
    """Codex and Gemini, 3.1 round 7."""

    def test_in_a_git_repository_the_guard_never_shows_as_a_change(self):
        guard = install_mod._RecoveryGuard(self.target).path
        self.assertNotIn(os.path.realpath(self.target) + os.sep + ".aios", os.path.realpath(guard))
        with open(guard, "w") as fh:  # what Windows leaves behind: it can't delete an open file
            fh.write("")
        self.assertEqual(util.git(self.target, ["status", "--porcelain", "--ignored", "--untracked-files=all"]), "")
        before = snapshot(self.target)
        self.adopt()
        install_mod.rollback(self.target, self.source)
        self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_an_adopted_path_the_repository_ignores_is_refused(self):
        write(self.target, ".gitignore", "node_modules/\n.env\nscripts/\n")
        self.commit("we ignore scripts/")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("ignored by this repository's git rules", exc.message)
        self.assertIn("scripts/team/git-safety-check.sh", exc.details)

    def test_the_installers_backups_folder_must_be_empty(self):
        write(self.target, ".aios/backups/notes.txt", "ours\n")
        self.commit("a file of ours in .aios/backups")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("own paths", exc.message)
        self.assertTrue(any("already holds files" in d for d in exc.details), exc.details)


class ReviewRoundEight(Existing):
    """Codex, 3.1 round 8."""

    def test_an_ignored_people_map_already_here_is_refused(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        with open(os.path.join(self.target, ".gitignore"), "a") as fh:
            fh.write(".aios/config.json\n")
        self.commit("our config, ignored")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("isn't committed", exc.message)

    def test_a_dead_lock_before_the_journal_is_cleared_when_a_people_map_exists(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.commit("our config, committed")
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to roll back", out)
        self.assertIn("release:  none (nothing was changed)", out)
        self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))


class ReviewRoundNine(Existing):
    """Codex, 3.1 round 9."""

    def test_an_upgrade_refuses_when_what_the_instance_runs_on_is_no_longer_committed(self):
        self.adopt()
        self.commit("adopted")
        with open(os.path.join(self.target, ".gitignore"), "a") as fh:
            fh.write(".aios/config.json\n")
        run_git(self.target, "rm", "-q", "--cached", ".aios/config.json")
        self.commit("the people map is only local now")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        exc = self.refuses_unchanged(install_mod.upgrade, self.target, v31, self.source)
        self.assertIn(".aios/config.json", exc.details)

    def test_a_policy_nobody_can_upgrade_and_roll_back_with_is_refused(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["roles"]["founder"]["lifecycle"] = ["install", "adopt", "upgrade", "governance"]  # no rollback
        write(self.target, ".aios/roles.json", json.dumps(policy, indent=2))
        self.commit("a policy without rollback")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("upgrade and roll back", exc.message)


class ReviewRoundTen(Existing):
    """Codex, 3.1 round 10."""

    def killed_after_link(self):
        """An adoption killed after its first file is linked, before the temporary copy goes."""
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.after_link"})
        self.assertEqual(code, 137)
        pending = install_mod.load_journal(self.target)["pending"]
        self.assertTrue(os.path.samestat(os.lstat(os.path.join(self.target, pending["path"])),
                                         os.lstat(os.path.join(self.target, pending["temp"]))))
        return pending

    def rolls_back_keeping(self, pending):
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, pending["path"])), "an edited file was removed")
        self.assertFalse(os.path.lexists(os.path.join(self.target, pending["temp"])))
        self.assertIn("left for you", out)
        return out

    def test_an_edit_after_a_kill_between_link_and_cleanup_is_kept(self):
        pending = self.killed_after_link()
        dest = os.path.join(self.target, pending["path"])
        with open(dest, "a") as fh:  # in place: the inode it shares with the temporary copy
            fh.write("\n")
        with open(dest, "rb") as fh:
            edited = fh.read()
        self.rolls_back_keeping(pending)
        with open(dest, "rb") as fh:
            self.assertEqual(fh.read(), edited)

    def test_a_mode_change_after_a_kill_between_link_and_cleanup_is_kept(self):
        pending = self.killed_after_link()
        os.chmod(os.path.join(self.target, pending["path"]), 0o600)
        self.rolls_back_keeping(pending)

    def no_rollback_policy(self):
        policy = json.loads(json.dumps(FF_ROLES))
        for role in policy["roles"].values():
            role["lifecycle"] = [a for a in role.get("lifecycle") or [] if a != "rollback"]
        write(self.target, ".aios/roles.json", json.dumps(policy, indent=2))

    def test_a_dead_lock_before_the_journal_is_cleared_whatever_the_policy_says(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.no_rollback_policy()
        self.commit("our config, and a policy nobody may roll back with")
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("cleared a dead operation's lock", out)
        self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_a_live_lock_is_still_never_taken_without_a_role(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.no_rollback_policy()
        self.commit("our config, and a policy nobody may roll back with")
        write(self.target, ".aios/lock", "adopt pid=%d at now\n" % os.getpid())
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertTrue(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_an_upgrade_refuses_once_the_policy_lets_nobody_roll_back(self):
        self.adopt()
        self.commit("adopted")
        self.no_rollback_policy()
        self.commit("rollback dropped from every role")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        exc = self.refuses_unchanged(install_mod.upgrade, self.target, v31, self.source)
        self.assertIn("upgrade and roll back", exc.message)


class ReviewRoundEleven(Existing):
    """Codex, 3.1 round 11."""

    def adopted(self):
        self.adopt()
        self.commit("adopted")

    def test_an_install_record_edited_after_a_kill_at_its_link_is_kept(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:adopt.record_after_link"})
        self.assertEqual(code, 137)
        pending = install_mod.load_journal(self.target)["pending"]
        self.assertEqual(pending["path"], ".aios/install.json")
        record = os.path.join(self.target, ".aios/install.json")
        with open(record, "a") as fh:  # in place; the plan hash inside is unchanged
            fh.write("\n")
        with open(record, "rb") as fh:
            edited = fh.read()
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn(".aios/install.json isn't exactly what an interrupted adoption made", out)
        with open(record, "rb") as fh:
            self.assertEqual(fh.read(), edited)
        for path in ADOPTED:  # everything else it made, unchanged, is gone
            self.assertFalse(os.path.lexists(os.path.join(self.target, path)), path)

    def test_verify_repo_takes_the_adopted_files_from_the_committed_plan(self):
        self.adopted()
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        dropped = record["managed"][0]["path"]
        record["managed"] = record["managed"][1:]
        record["adoption"]["exclude"].append(dropped)  # the record's own copy of the plan, edited
        util.write_json(path, record)
        os.remove(os.path.join(self.target, dropped))
        problems = install_mod.verify(self.target, source_repo=self.source)[0]
        self.assertTrue(any(dropped in p and "doesn't list it" in p for p in problems), problems)
        self.assertTrue(any("record's copy of the adoption plan" in p for p in problems), problems)

    def test_verify_repo_reports_a_plan_changed_since_the_last_upgrade_until_one_applies_it(self):
        self.adopted()
        plan = json.loads(json.dumps(PLAN))
        plan["adopt"].remove("START_HERE.md")
        plan["instance_owned"].append("START_HERE.md")
        self.write_plan(plan)
        self.commit("START_HERE.md is ours now")
        problems = install_mod.verify(self.target, source_repo=self.source)[0]
        self.assertTrue(any("isn't the one this instance was adopted" in p for p in problems), problems)
        rev = harness.bump_source(self.source, {"scripts/team/git-safety-check.sh": "#!/bin/sh\necho v31\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        install_mod.upgrade(self.target, v31, self.source)
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])

    def test_a_lock_that_names_no_process_is_cleared_by_rollback(self):
        for words in ("", "adopt pid="):
            with self.subTest(words=words):
                write(self.target, ".aios/lock", words)
                self.be("acme-founder")
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertEqual(code, 0, out + err)
                self.assertIn("cleared a dead operation's lock", out)
                self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_windows_aliases_of_the_installers_paths_are_reserved(self):
        for path in (".aios/lock.", ".aios/config.json ", ".aios/txn.json::$DATA", ".aios/install.json:x",
                     ".aios./lock", ".aios /lock", ".aios/backups./x", ".AIOS/Backups /x",
                     "AIOS~1/lock", ".aios/INSTAL~1.JSO", ".aios/CONFIG~1.JSO"):
            self.assertTrue(util.is_reserved(path), path)
        for path in (".aios/roles.json", ".aios/.gitignore", ".aios/operator_core/OPERATOR_CORE.md",
                     "notes~1.md", "docs/v1.0/guide.md", "scripts/aios/install.py"):
            self.assertFalse(util.is_reserved(path), path)
        from aioslib import release
        for alias in (".aios/lock.", ".aios/config.json "):
            man = json.loads(json.dumps(self.v))
            man["files"].append({"path": alias, "class": "managed", "mode": "100644", "sha256": "0" * 64})
            self.assertTrue(any("installer's own state" in p for p in release.check_shape(man)), alias)


class ReviewRoundTwelve(Existing):
    """Gemini, 3.1 round 12: a finished adoption's record, edited since, is kept like any file it made."""

    def adopted(self):
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        return os.path.join(self.target, ".aios/install.json")

    def rolls_back_keeping_the_record(self, record):
        with open(record, "rb") as fh:
            edited = fh.read()
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn(".aios/install.json changed since the adoption wrote it", out)
        self.assertIn(".aios/install.json was left because it changed", out)
        self.assertNotIn("no longer pinned", out)
        with open(record, "rb") as fh:
            self.assertEqual(fh.read(), edited)
        for path in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, path)), path)

    def test_an_edited_record_with_the_same_plan_hash_is_kept(self):
        # Since round 22 an edited record isn't trusted to say which files the adoption made: rollback
        # refuses and changes nothing until it's restored from git.
        record = self.adopted()
        data = util.read_json(record)
        data["installed_at"] = "edited by hand"
        util.write_json(record, data)  # canonical bytes, same plan hash: only the seal tells
        with open(record, "rb") as fh:
            edited = fh.read()
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertTrue(any(m in out + err for m in ("can't trust which files the adoption made",
                                                       "isn't the one this workspace's last operation wrote")),
                        out + err)
        with open(record, "rb") as fh:
            self.assertEqual(fh.read(), edited)
        for path in ADOPTED:
            self.assertTrue(os.path.lexists(os.path.join(self.target, path)), path)
        run_git(self.target, "checkout", "--", ".aios/install.json")  # restored, it rolls back
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.lexists(record))

    def test_a_record_whose_permissions_changed_is_kept(self):
        record = self.adopted()
        os.chmod(record, 0o600)
        self.rolls_back_keeping_the_record(record)

    def test_an_unedited_record_goes_and_the_workspace_is_unpinned(self):
        record = self.adopted()
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("no longer pinned", out)
        self.assertFalse(os.path.lexists(record))

    def test_the_seal_survives_an_upgrade_and_its_rollback(self):
        record = self.adopted()
        with open(record, "rb") as fh:
            adopted_bytes = fh.read()
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        install_mod.upgrade(self.target, v31, self.source)
        self.assertNotIn(install_mod.RECORD_SEAL, util.read_json(record))  # a new record
        self.commit("upgraded")
        install_mod.rollback(self.target, self.source)  # back to the adoption's own record, byte for byte
        with open(record, "rb") as fh:
            self.assertEqual(fh.read(), adopted_bytes)
        self.commit("rolled back to the adoption")
        install_mod.rollback(self.target, self.source)  # and the adoption itself
        self.assertFalse(os.path.lexists(record))
        for path in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, path)), path)


class ReviewRoundTwelveCodex(Existing):
    """Codex, 3.1 round 12."""

    def killed_at(self, point):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:" + point})
        self.assertEqual(code, 137)
        return os.path.join(self.target, ".aios/install.json")

    def rollback(self):
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        for path in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, path)), path)
        return out

    def test_a_record_replaced_after_a_kill_at_its_link_is_kept_even_with_the_same_bytes(self):
        record = self.killed_at("adopt.record_after_link")
        with open(record, "rb") as fh:
            same = fh.read()
        fresh = record + ".new"
        with open(fresh, "wb") as fh:
            fh.write(same)
        os.chmod(fresh, 0o644)
        os.replace(fresh, record)  # identical bytes and mode, but another file
        out = self.rollback()
        self.assertIn(".aios/install.json isn't exactly what an interrupted adoption made", out)
        with open(record, "rb") as fh:
            self.assertEqual(fh.read(), same)

    def test_after_its_temporary_copy_went_a_record_is_judged_by_what_was_written(self):
        record = self.killed_at("adopt.record_after_temp")
        self.assertEqual(install_mod.load_journal(self.target)["pending"]["path"], ".aios/install.json")
        with open(record, "a") as fh:
            fh.write("\n")
        self.rollback()
        self.assertTrue(os.path.isfile(record), "an edited record was removed")

    def test_after_its_temporary_copy_went_an_unchanged_record_goes(self):
        record = self.killed_at("adopt.record_after_temp")
        out = self.rollback()
        self.assertFalse(os.path.lexists(record), out)
        self.assertEqual(os.listdir(os.path.join(self.target, ".aios", "backups"))
                         if os.path.isdir(os.path.join(self.target, ".aios", "backups")) else [], [])

    def test_a_file_that_appeared_identical_when_the_link_failed_is_kept(self):
        with open(os.path.join(self.source, "START_HERE.md"), "rb") as fh:
            release_bytes = fh.read()
        real = util.create_new

        def appears_first(target, rel, data, mode, before_link=None):
            if rel == "START_HERE.md":
                with open(os.path.join(target, rel), "wb") as fh:  # someone else's, the same bytes
                    fh.write(release_bytes)
                os.chmod(os.path.join(target, rel), 0o644)
            return real(target, rel, data, mode, before_link)

        util.create_new = appears_first
        try:
            with self.assertRaises(Refusal) as ctx:
                self.adopt()
        finally:
            util.create_new = real
        self.assertIn("appeared while this ran", ctx.exception.message)
        with open(os.path.join(self.target, "START_HERE.md"), "rb") as fh:
            self.assertEqual(fh.read(), release_bytes)
        self.assertFalse(os.path.lexists(install_mod.journal_path(self.target)))

    def test_verify_repo_refuses_a_managed_file_the_plan_doesnt_adopt(self):
        self.adopt()
        self.commit("adopted")
        entries = {e["path"]: e for e in self.v["files"]}
        classes, _ = install_mod.classify_adoption(PLAN, entries)
        extra = sorted(p for p, e in entries.items() if e["class"] == "managed" and classes.get(p) == "exclude")[0]
        with open(os.path.join(self.source, extra), "rb") as fh:
            write(self.target, extra, fh.read().decode("utf-8"))
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        record["managed"].append({"path": extra, "sha256": entries[extra]["sha256"],
                                  "exec": entries[extra].get("mode") == "100755"})
        util.write_json(path, record)
        problems = install_mod.verify(self.target, source_repo=self.source)[0]
        self.assertTrue(any(extra in p and "doesn't adopt it" in p for p in problems), problems)

    def test_paths_under_a_state_file_are_reserved(self):
        from aioslib import release
        for path in (".aios/config.json/child", ".aios/install.json/x/y", ".aios/txn.json/a", ".aios/lock/b",
                     ".aios/config.json./child", ".AIOS/Install.json /x"):
            self.assertTrue(util.is_reserved(path), path)
            man = json.loads(json.dumps(self.v))
            man["files"].append({"path": path, "class": "managed", "mode": "100644", "sha256": "0" * 64})
            self.assertTrue(any("installer's own state" in p for p in release.check_shape(man)), path)
        self.assertFalse(util.is_reserved(".aios/config.jsonx/child"))


class ReviewRoundThirteen(Existing):
    """Gemini, 3.1 round 13: a temporary copy create_new couldn't remove is still cleaned up."""

    def test_a_failed_link_whose_temporary_copy_remains_is_cleaned_up_and_keeps_the_other_file(self):
        real = util.create_new

        def link_fails_and_copy_stays(target, rel, data, mode, before_link=None):
            if rel != "START_HERE.md":
                return real(target, rel, data, mode, before_link)
            tmp = util.private_temp(target)
            with open(tmp, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, 0o644)
            before_link(tmp)
            write(target, rel, "# someone else's, appeared meanwhile\n")
            raise Refusal(util.EXIT_STATE, "%s appeared while this ran; it was not overwritten" % rel)

        util.create_new = link_fails_and_copy_stays
        try:
            with self.assertRaises(Refusal):
                self.adopt()
        finally:
            util.create_new = real
        backups = os.path.join(self.target, ".aios", "backups")
        self.assertEqual([n for n in os.listdir(backups) if n.startswith(".write-")]
                         if os.path.isdir(backups) else [], [], "a temporary copy was left behind")
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertEqual(fh.read(), "# someone else's, appeared meanwhile\n")
        self.assertFalse(os.path.lexists(install_mod.journal_path(self.target)))


class ReviewRoundThirteenCodex(Existing):
    """Codex, 3.1 round 13."""

    def test_a_kill_after_a_failed_link_never_takes_the_file_that_appeared(self):
        import subprocess
        with open(os.path.join(self.source, "START_HERE.md"), "rb") as fh:
            release_bytes = fh.read()
        rel = self.write_json("release.json", self.v)
        cfg = self.write_json("org.json", harness.config())
        script = (
            "import json, os, sys\n"
            "sys.path.insert(0, %r)\n"
            "from aioslib import install, util\n"
            "real = util.create_new\n"
            "def appears_first(target, rel, data, mode, before_link=None):\n"
            "    if rel == 'START_HERE.md':\n"
            "        with open(os.path.join(target, rel), 'wb') as fh:\n"
            "            fh.write(%r)\n"
            "        os.chmod(os.path.join(target, rel), 0o644)\n"
            "    return real(target, rel, data, mode, before_link)\n"
            "util.create_new = appears_first\n"
            "install.adopt_existing(%r, json.load(open(%r)), %r, json.load(open(%r)))\n"
        ) % (harness.AIOS_DIR, release_bytes, self.target, rel, self.source, cfg)
        env = dict(os.environ, AIOS_FAULT="crash:create.link_refused")
        proc = subprocess.run([sys.executable, "-c", script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 137, proc.stderr)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.target, "START_HERE.md"), "rb") as fh:
            self.assertEqual(fh.read(), release_bytes)  # someone else's, identical, kept
        backups = os.path.join(self.target, ".aios", "backups")
        self.assertEqual([n for n in os.listdir(backups) if n.startswith(".write-")]
                         if os.path.isdir(backups) else [], [])
        for path in ADOPTED:
            if path != "START_HERE.md":
                self.assertFalse(os.path.lexists(os.path.join(self.target, path)), path)

    def test_on_windows_an_unchanged_record_is_judged_by_its_read_only_flag(self):
        self.adopt()
        self.commit("adopted")
        record = install_mod.install_record_path(self.target)
        saved = install_mod._EXEC_BITS
        install_mod._EXEC_BITS = False  # as on Windows: no POSIX bits, only read-only
        try:
            os.chmod(record, 0o666)  # what Windows reports for an ordinary writable file
            self.assertTrue(install_mod._record_unchanged(record))
            os.chmod(record, 0o444)  # read-only: changed
            self.assertFalse(install_mod._record_unchanged(record))
            os.chmod(record, 0o666)
            install_mod.rollback(self.target, self.source)
        finally:
            install_mod._EXEC_BITS = saved
        self.assertFalse(os.path.lexists(record))

    def test_a_linked_aios_folder_refuses_before_the_lock(self):
        outside = os.path.join(self.tmp, "outside")
        shutil.move(os.path.join(self.target, ".aios"), outside)
        os.symlink(outside, os.path.join(self.target, ".aios"))
        self.commit("our .aios is a link")
        before = sorted(os.listdir(outside))
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("own paths", exc.message)
        self.assertTrue(any(".aios is a link" in d for d in exc.details), exc.details)
        self.assertEqual(sorted(os.listdir(outside)), before)


def _tree(root):
    """Every folder and file under `root` (git's own folder aside), with each file's bytes."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not (dirpath == root and d == ".git")]
        rel = os.path.relpath(dirpath, root)
        out[rel + "/"] = "<folder>"  # a value, so a folder only one side has is a difference
        for f in filenames:
            with open(os.path.join(dirpath, f), "rb") as fh:
                out[os.path.join(rel, f)] = fh.read()
    return out


class ReviewRoundFourteen(Existing):
    """Codex, 3.1 round 14."""

    def test_a_failed_journal_write_leaves_no_temporary_copy_and_adoption_can_run_again(self):
        real = util.write_json
        journal = install_mod.journal_path(self.target)
        failed = []

        def disk_full_once(path, obj):
            if path == journal and isinstance(obj, dict) and obj.get("pending") and not failed:
                failed.append(path)
                raise OSError(28, "No space left on device")
            return real(path, obj)

        util.write_json = disk_full_once
        try:
            with self.assertRaises(OSError):
                self.adopt()
        finally:
            util.write_json = real
        self.assertTrue(failed)
        backups = os.path.join(self.target, ".aios", "backups")
        self.assertEqual([n for n in os.listdir(backups) if n.startswith(".write-")]
                         if os.path.isdir(backups) else [], [], "a temporary copy no journal names was left")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.adopt()  # and it runs again
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])

    def test_outside_git_a_refusal_changes_no_folder(self):
        shutil.rmtree(os.path.join(self.target, ".git"))
        before = _tree(self.target)
        with self.assertRaises(Refusal) as ctx:
            self.adopt()
        self.assertIn("isn't a git repository", ctx.exception.message)
        self.assertEqual(_tree(self.target), before)

    def test_without_an_aios_folder_a_refusal_changes_no_folder(self):
        shutil.rmtree(os.path.join(self.target, ".aios"))
        self.commit("no .aios at all")
        before = _tree(self.target)
        with self.assertRaises(Refusal) as ctx:
            self.adopt()
        self.assertIn("no role policy of its own", ctx.exception.message)
        self.assertEqual(_tree(self.target), before)


class ReviewRoundFifteen(Existing):
    """Codex, 3.1 round 15."""

    def test_rollback_in_an_ordinary_folder_creates_nothing(self):
        plain = os.path.join(self.tmp, "plain")
        write(plain, "notes.md", "# just a folder\n")
        before = _tree(plain)
        code, out, err = self.cli("rollback", "--target", plain)
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to roll back", out)
        self.assertEqual(_tree(plain), before)

    def with_config_committed(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.commit("our people map, committed")  # so the first create is an adopted file
        return _tree(self.target)

    def test_a_refused_link_leaves_no_folder_it_made(self):
        before = self.with_config_committed()
        real = os.link

        def no_links_into_new_folders(src, dst, *a, **kw):
            if ".claude/skills" in dst.replace(os.sep, "/"):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *a, **kw)

        os.link = no_links_into_new_folders
        try:
            with self.assertRaises(Refusal) as ctx:
                self.adopt()
        finally:
            os.link = real
        self.assertIn("without risking a replace", ctx.exception.message)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_create_that_fails_before_its_journal_entry_has_its_folders_pruned_by_rollback(self):
        before = self.with_config_committed()
        real = util.create_new

        def fails_after_making_folders(target, rel, data, mode, before_link=None):
            if rel.startswith(".claude/skills/"):
                util.ensure_parent(os.path.join(target, rel))
                raise OSError(5, "Input/output error")
            return real(target, rel, data, mode, before_link)

        util.create_new = fails_after_making_folders
        try:
            with self.assertRaises(OSError):
                self.adopt()
        finally:
            util.create_new = real
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_finished_adoption_rolled_back_leaves_every_folder_as_it_was(self):
        before = self.with_config_committed()
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        after = _tree(self.target)
        self.assertEqual(diff(before, after), [])

    def test_an_empty_backups_folder_that_was_there_stays(self):
        os.makedirs(os.path.join(self.target, ".aios", "backups"))
        before = self.with_config_committed()
        self.assertIn(".aios/backups/", before)
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundSixteen(Existing):
    """Codex, 3.1 round 16."""

    def cli_adopt(self, config=None):
        cfg = self.write_json("org.json", config or harness.config())
        rel = self.write_json("release.json", self.v)
        return self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                        "--config", cfg, "--repo", self.source)

    def test_the_instances_own_policy_decides_who_may_adopt_into_it(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["roles"]["founder"]["lifecycle"] = ["install", "upgrade", "rollback", "governance"]  # no adopt
        write(self.target, ".aios/roles.json", json.dumps(policy, indent=2))
        self.commit("in our instance, nobody adopts")
        before = _tree(self.target)
        self.be("acme-founder")  # the release's own policy lets a founder adopt
        code, out, err = self.cli_adopt()
        self.assertEqual(code, util.EXIT_ROLE, out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_role_only_the_instances_policy_lets_adopt_may(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["roles"]["operator"]["lifecycle"] = ["adopt"]  # the release's policy doesn't allow it
        write(self.target, ".aios/roles.json", json.dumps(policy, indent=2))
        self.commit("in our instance, an operator may adopt")
        self.be("acme-va")
        code, out, err = self.cli_adopt()
        self.assertEqual(code, 0, out + err)
        self.assertIn("by:       acme-va (operator)", out)

    def test_verify_repo_refuses_a_plan_that_isnt_committed(self):
        self.adopt()
        self.commit("adopted")
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        dropped = record["managed"][0]["path"]
        alt = json.loads(json.dumps(PLAN))
        alt["exclude"].append(dropped)
        alt["adopt"] = [p for p in alt["adopt"] if not util.match_any([p], dropped)] + \
            [e["path"] for e in record["managed"][1:]]
        write(self.target, ".aios/local_plan.json", json.dumps(alt, indent=2))  # never committed
        record["managed"] = record["managed"][1:]
        record["adoption"]["plan"] = ".aios/local_plan.json"
        record["adoption"]["plan_sha256"] = install_mod.load_adoption_plan(self.target, ".aios/local_plan.json")[1]
        for cls in ("adopt", "instance_owned", "exclude"):
            record["adoption"][cls] = alt[cls]
        util.write_json(path, record)
        os.remove(os.path.join(self.target, dropped))
        problems = install_mod.verify(self.target, source_repo=self.source)[0]
        self.assertTrue(any("isn't committed" in p for p in problems), problems)

    def test_verify_repo_refuses_a_plan_edited_since_its_commit(self):
        self.adopt()
        self.commit("adopted")
        plan_path = os.path.join(self.target, ".aios/adoption.json")
        with open(plan_path, "a") as fh:
            fh.write("\n")
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        record["adoption"]["plan_sha256"] = install_mod.load_adoption_plan(self.target)[1]  # hides the edit
        util.write_json(path, record)
        problems = install_mod.verify(self.target, source_repo=self.source)[0]
        self.assertTrue(any("aren't committed" in p for p in problems), problems)

    def test_a_folder_the_adoption_made_but_since_replaced_stays(self):
        self.adopt()
        self.commit("adopted")
        skills = os.path.join(self.target, ".claude", "skills")
        old = os.path.join(self.target, ".claude", "skills_old")
        os.rename(skills, old)  # the old folders keep their inodes while the new ones are made
        os.makedirs(os.path.join(skills, "start-my-day"))
        shutil.rmtree(old)
        install_mod.rollback(self.target, self.source)
        self.assertTrue(os.path.isdir(os.path.join(skills, "start-my-day")), "a folder it didn't make was removed")


class ReviewRoundSeventeen(Existing):
    """Codex, 3.1 round 17."""

    def test_a_kill_inside_any_early_state_write_rolls_back_to_the_exact_tree(self):
        before = _tree(self.target)
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        for n in range(1, 7):
            with self.subTest(write=n):
                code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                        "--config", cfg, "--repo", self.source,
                                        env={"AIOS_FAULT": "crash:write_json.before_replace@%d" % n})
                self.assertEqual(code, 137)
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertEqual(code, 0, out + err)
                self.assertEqual(diff(before, _tree(self.target)), [])
                self.assertEqual(util.git(self.target, ["status", "--porcelain", "--untracked-files=all"]), "")
        self.adopt()  # and it runs again
        self.assertEqual(install_mod.verify(self.target, source_repo=self.source)[0], [])

    def declared_reviewers(self):
        policy = json.loads(json.dumps(FF_ROLES))
        policy["founder_lane_reviewers"] = ["@acme-lead"]  # not a founder
        write(self.target, ".aios/roles.json", json.dumps(policy, indent=2))
        self.commit("only acme-lead reviews the founder lane")

    def test_the_edit_hold_names_the_declared_reviewers(self):
        self.declared_reviewers()
        self.adopt()
        from aioslib import boundary
        ok, reason = boundary.check_edit(self.target, "Edit", {"file_path": os.path.join(self.target, "CLAUDE.md")},
                                         identify=lambda root: "acme-va")
        self.assertFalse(ok)
        self.assertIn("for an approved founder-lane reviewer", reason)
        self.assertNotIn("or to review a pull request", reason)

    def test_start_names_the_declared_reviewers(self):
        self.declared_reviewers()
        self.adopt()
        self.commit("adopted")
        self.be("acme-va")
        code, out, err = self.cli("start", "--target", self.target)
        self.assertEqual(code, 0, out + err)
        self.assertIn("until an approved founder-lane reviewer", out)


class ReviewRoundEighteen(Existing):
    """Codex, 3.1 round 18: a name is not proof."""

    NAME = ".aios/.txn.json.aaaaaaaa.tmp"

    def test_adoption_refuses_over_a_file_with_an_installer_temporary_name(self):
        write(self.target, self.NAME, "ours\n")
        self.commit("a file of ours with that name")
        exc = self.refuses_unchanged(self.adopt)
        self.assertTrue(any("temporary files" in d for d in exc.details), exc.details)

    def test_rollback_never_sweeps_a_tracked_file(self):
        self.adopt()
        self.commit("adopted")
        write(self.target, self.NAME, "ours\n")
        self.commit("a file of ours with that name, after the adoption")
        install_mod.rollback(self.target, self.source)
        with open(os.path.join(self.target, self.NAME)) as fh:
            self.assertEqual(fh.read(), "ours\n")

    def test_releases_may_not_ship_those_names(self):
        from aioslib import release
        for path in (self.NAME, ".aios/.install.json.abc12345.tmp", ".AIOS/.config.json.zz_00000.tmp"):
            self.assertTrue(util.is_reserved(path), path)
            man = json.loads(json.dumps(self.v))
            man["files"].append({"path": path, "class": "managed", "mode": "100644", "sha256": "0" * 64})
            self.assertTrue(any("installer's own state" in p for p in release.check_shape(man)), path)
        self.assertFalse(util.is_reserved(".aios/txn.json.notes.md"))


def _folds_case(folder):
    probe = os.path.join(folder, "CaseProbe")
    write(folder, "CaseProbe", "x")
    try:
        return os.path.exists(probe.lower())
    finally:
        os.remove(probe)


class ReviewRoundNineteen(Existing):
    """Codex, 3.1 round 19: whether git tracks a path, asked literally and as the disk sees it."""

    def test_a_plan_named_like_a_pattern_isnt_mistaken_for_the_committed_one(self):
        with open(os.path.join(self.target, ".gitignore"), "a") as fh:
            fh.write(".aios/adopt*.json\n")
        self.commit("we ignore our scratch plans")
        write(self.target, ".aios/adopt*.json", json.dumps(PLAN, indent=2))  # ignored, never committed
        self.assertFalse(util.is_tracked(self.target, ".aios/adopt*.json"))
        self.assertFalse(util.is_tracked(self.target, ".aios/adopt[i]on.json"))
        exc = self.refuses_unchanged(self.adopt, plan_rel=".aios/adopt*.json")
        self.assertIn("must be committed", exc.message)

    def test_rollback_never_sweeps_a_file_tracked_under_another_case(self):
        if not _folds_case(self.tmp):
            self.skipTest("this disk keeps case, so the two spellings are two files")
        self.adopt()
        self.commit("adopted")
        name = ".txn.json.aaaaaaaa.tmp"
        write(self.target, ".aios/" + name, "ours\n")
        blob = util.git(self.target, ["hash-object", "-w", ".aios/" + name])
        run_git(self.target, "update-index", "--add", "--cacheinfo", "100644,%s,.AIOS/%s" % (blob, name))
        run_git(self.target, "commit", "-qm", "tracked as .AIOS")
        self.assertTrue(util.is_tracked(self.target, ".aios/" + name))
        install_mod.rollback(self.target, self.source)
        with open(os.path.join(self.target, ".aios", name)) as fh:
            self.assertEqual(fh.read(), "ours\n")


class ReviewRoundTwenty(Existing):
    """Codex, 3.1 round 20."""

    def test_rollback_never_follows_a_link_out_of_the_repository(self):
        self.adopt()
        self.commit("adopted")
        outside = os.path.join(self.tmp, "outside")
        with open(os.path.join(self.target, ".claude/skills/start-my-day/SKILL.md"), "rb") as fh:
            release_bytes = fh.read()
        write(outside, "start-my-day/SKILL.md", release_bytes.decode("utf-8"))  # identical bytes, outside
        os.chmod(os.path.join(outside, "start-my-day/SKILL.md"), 0o644)
        shutil.rmtree(os.path.join(self.target, ".claude", "skills"))
        os.symlink(outside, os.path.join(self.target, ".claude", "skills"))
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("reached through a link now", out)
        with open(os.path.join(outside, "start-my-day/SKILL.md"), "rb") as fh:
            self.assertEqual(fh.read(), release_bytes)

    def test_rollback_never_acts_on_a_journal_path_outside_the_workspace(self):
        outside = os.path.join(self.tmp, "outside.txt")
        write(self.tmp, "outside.txt", "not the workspace's\n")
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.mid_write"})
        self.assertEqual(code, 137)
        journal = install_mod.load_journal(self.target)
        journal["adoption"]["created"].append({"path": "../outside.txt", "mode": 0o644,
                                               "sha256": util.sha256_file(outside)})
        util.write_json(install_mod.journal_path(self.target), journal)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(outside), "a file outside the workspace was removed")

    def test_a_tracked_lock_is_the_repositorys_file(self):
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        run_git(self.target, "add", "-f", ".aios/lock")
        self.commit("a file of ours at that path")
        exc = self.refuses_unchanged(self.adopt)
        self.assertTrue(any("this repository tracks" in d for d in exc.details), exc.details)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("not the installer's lock", out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".aios/lock")))


class ReviewRoundTwentyOne(Existing):
    """Codex, 3.1 round 21: in a git workspace too, .aios and its backups folder must be real folders."""

    def adopted(self):
        self.adopt()
        self.commit("adopted")
        outside = os.path.join(self.tmp, "outside")
        os.makedirs(outside)
        return outside

    def test_an_upgrade_never_backs_up_through_a_linked_backups_folder(self):
        outside = self.adopted()
        with open(os.path.join(self.target, ".gitignore"), "a") as fh:
            fh.write("/.aios/backups\n")  # so the link itself is ignored and the worktree stays clean
        self.commit("ignore the backups path, link or not")
        backups = os.path.join(self.target, ".aios", "backups")
        if os.path.isdir(backups):
            shutil.rmtree(backups)
        os.symlink(outside, backups)
        self.assertEqual(util.git(self.target, ["status", "--porcelain"]), "")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        with self.assertRaises(Refusal) as ctx:
            install_mod.upgrade(self.target, v31, self.source)
        self.assertIn("is a link or a file, not a folder", ctx.exception.message)
        self.assertEqual(os.listdir(outside), [])

    def test_rollback_never_writes_through_a_linked_aios_folder(self):
        outside = self.adopted()
        os.rmdir(outside)
        shutil.move(os.path.join(self.target, ".aios"), outside)
        os.symlink(outside, os.path.join(self.target, ".aios"))
        before = _tree(outside)
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("is a link or a file, not a folder", ctx.exception.message)
        self.assertEqual(diff(before, _tree(outside)), [])


class ReviewRoundTwentyTwo(Existing):
    """Codex and Gemini, 3.1 round 22."""

    def test_a_finished_adoptions_record_naming_another_file_is_refused(self):
        self.adopt()
        self.commit("adopted")
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        record["adoption"]["created"].append({"path": "README.md", "sha256": None})  # the instance's own
        util.write_json(path, record)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        with open(os.path.join(self.target, "README.md")) as fh:
            self.assertEqual(fh.read(), "# our company repo\n")
        for p in ADOPTED:
            self.assertTrue(os.path.lexists(os.path.join(self.target, p)), p)

    def test_an_interrupted_adoptions_entry_without_provenance_is_left(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.mid_write"})
        self.assertEqual(code, 137)
        journal = install_mod.load_journal(self.target)
        journal["adoption"]["created"].append({"path": "README.md", "sha256": None})
        util.write_json(install_mod.journal_path(self.target), journal)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertIn("without a usable hash and mode", out)
        with open(os.path.join(self.target, "README.md")) as fh:
            self.assertEqual(fh.read(), "# our company repo\n")

    def test_a_file_where_aios_should_be_is_a_refusal_not_a_crash(self):
        for make in ("file", "link to a file"):
            with self.subTest(make=make):
                aios = os.path.join(self.tmp, "ws-" + make.replace(" ", "-"))
                os.makedirs(aios)
                if make == "file":
                    write(aios, ".aios", "not a folder\n")
                else:
                    write(self.tmp, "a-file", "x\n")
                    os.symlink(os.path.join(self.tmp, "a-file"), os.path.join(aios, ".aios"))
                with self.assertRaises(Refusal) as ctx:
                    with install_mod._Lock(aios, "upgrade"):
                        pass
                self.assertIn("is a link or a file, not a folder", ctx.exception.message)

    def test_the_backup_step_refuses_a_linked_backups_folder(self):
        self.adopt()
        self.commit("adopted")
        outside = os.path.join(self.tmp, "outside")
        os.makedirs(outside)
        backups = os.path.join(self.target, ".aios", "backups")
        if os.path.isdir(backups):
            shutil.rmtree(backups)
        os.symlink(outside, backups)
        with self.assertRaises(Refusal):
            install_mod._backup(self.target, install_mod.load_record(self.target), "txn-test")
        self.assertEqual(os.listdir(outside), [])


class ReviewRoundTwentyThree(Existing):
    """Gemini, 3.1 round 23."""

    def readme_entry(self):
        full = os.path.join(self.target, "README.md")
        return {"path": "README.md", "sha256": util.sha256_file(full),
                "mode": stat_mode(full)}

    def test_a_forged_and_resealed_record_cant_make_an_instance_file_removable(self):
        self.adopt()
        self.commit("adopted")
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        record["adoption"]["created"].append(self.readme_entry())
        record = install_mod._sealed(record)  # a seal anyone can recompute
        with open(path, "wb") as fh:
            fh.write(install_mod._record_bytes(record))
        os.chmod(path, 0o644)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)  # since round 26: it differs from the committed record
        self.assertTrue(any(m in out + err for m in ("differs from the one committed with the adoption",
                                                       "isn't the one this workspace's last operation wrote")),
                        out + err)
        with open(os.path.join(self.target, "README.md")) as fh:
            self.assertEqual(fh.read(), "# our company repo\n")

    def test_a_forged_journal_entry_cant_either(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.mid_write"})
        self.assertEqual(code, 137)
        journal = install_mod.load_journal(self.target)
        journal["adoption"]["created"].append(self.readme_entry())
        util.write_json(install_mod.journal_path(self.target), journal)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.target, "README.md")) as fh:
            self.assertEqual(fh.read(), "# our company repo\n")

    def test_the_backup_snapshot_folder_is_always_new(self):
        self.adopt()
        self.commit("adopted")
        txn = "20261015T000000Z-3.0.0-to-3.1.0"
        root = os.path.join(self.target, ".aios", "backups", txn)
        os.makedirs(root)
        os.symlink(self.target, os.path.join(root, "files"))  # would send the copies into the workspace
        before = _tree(self.target)
        with self.assertRaises(Refusal) as ctx:
            install_mod._backup(self.target, install_mod.load_record(self.target), txn)
        self.assertIn("already exists", ctx.exception.message)
        self.assertEqual(diff(before, _tree(self.target)), [])


def stat_mode(full):
    import stat as _stat
    return _stat.S_IMODE(os.lstat(full).st_mode)


class ReviewRoundTwentyThreeCodex(Existing):
    """Codex, 3.1 round 23: the journal's pending temporary copy is only ever an installer temporary."""

    def test_a_tampered_pending_temp_never_removes_a_repository_file(self):
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:adopt.mid_write"})
        self.assertEqual(code, 137)
        journal = install_mod.load_journal(self.target)
        for temp in ("README.md", ".aios/backups/README.md", ".aios/backups/.write-abc"):
            with self.subTest(temp=temp):
                if temp.startswith(".aios/backups/"):
                    write(self.target, temp, "ours\n")
                journal["pending"] = {"path": "docs/absent.md", "temp": temp,
                                      "sha256": "0" * 64, "mode": 0o644}
                util.write_json(install_mod.journal_path(self.target), journal)
                notes = install_mod._undo_adoption(self.target, journal["adoption"], journal["pending"])
                self.assertIn("an interrupted adoption's journal entry wasn't usable, so it was left alone", notes)
                self.assertTrue(os.path.isfile(os.path.join(self.target, temp)), temp)


class ReviewRoundTwentyFour(Existing):
    """Codex, 3.1 round 24: a finished adoption's undo trusts only the release, and git, not the record."""

    def forge(self, mutate):
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        mutate(record)
        record = install_mod._sealed(record)  # a seal anyone can recompute
        with open(path, "wb") as fh:
            fh.write(install_mod._record_bytes(record))
        os.chmod(path, 0o644)
        self.commit("a forged record, as a pull request could bring")
        self.forget_state()  # so the git anchor itself is what's tested

    def entry(self, rel):
        full = os.path.join(self.target, rel)
        return {"path": rel, "sha256": util.sha256_file(full), "mode": stat_mode(full)}

    def rollback_ok(self):
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        for p in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, p)), p)
        return out

    def rollback_refused(self):
        """Since round 26 a record changed after the adoption commit is refused outright, nothing changed."""
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("differs from the one committed with the adoption", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_an_instance_file_under_an_adopted_pattern_stays(self):
        write(self.target, "scripts/team/local.sh", "#!/bin/sh\necho ours\n")
        self.commit("our own script beside the starter's")
        self.adopt()
        self.commit("adopted")
        self.forge(lambda r: r["adoption"]["created"].append(self.entry("scripts/team/local.sh")))
        self.rollback_refused()
        self.assertTrue(os.path.isfile(os.path.join(self.target, "scripts/team/local.sh")))

    def test_a_people_map_the_repository_had_before_stays(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.commit("our people map, before any adoption")
        self.adopt()
        self.commit("adopted")
        self.forge(lambda r: r["adoption"]["created"].append(self.entry(".aios/config.json")))
        self.rollback_refused()
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".aios/config.json")))
        run_git(self.target, "revert", "--no-edit", "HEAD")  # the forged record undone: rollback runs
        self.rollback_ok()
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".aios/config.json")))

    def test_an_empty_folder_of_the_instances_stays(self):
        self.adopt()
        self.commit("adopted")
        st = os.lstat(os.path.join(self.target, "empty_of_ours"))
        self.forge(lambda r: r["adoption"]["made_dirs"].append(
            {"path": "empty_of_ours", "dev": st.st_dev, "ino": st.st_ino}))
        self.rollback_refused()
        self.assertTrue(os.path.isdir(os.path.join(self.target, "empty_of_ours")))

    def test_without_the_release_source_a_finished_adoption_is_refused_unchanged(self):
        self.adopt()
        self.commit("adopted")
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("needs the release it came from", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_committed_adoption_with_the_people_map_it_made_rolls_back_exactly(self):
        before = _tree(self.target)
        self.adopt()
        self.commit("adopted, the people map with it")
        self.rollback_ok()
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundTwentyFive(ReviewRoundTwentyFour):
    """Gemini, 3.1 round 25: the people map the adoption made, as git has kept it."""

    def test_a_people_map_edited_since_the_adoption_stays(self):
        self.adopt()
        self.commit("adopted")
        config = os.path.join(self.target, ".aios/config.json")
        data = util.read_json(config)
        data["people"].append({"github": "acme-lead", "role": "operator", "display_name": "Lead"})
        util.write_json(config, data)
        self.commit("we added someone")
        self.rollback_ok()
        self.assertEqual(util.read_json(config), data)  # changed since the adoption commit: it stays

    def test_a_staged_but_uncommitted_adoption_rolls_back_exactly(self):
        before = _tree(self.target)
        self.adopt()
        run_git(self.target, "add", "-A")  # staged, never committed
        self.rollback_ok()
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundTwentyFiveCodex(ReviewRoundTwentyFour):
    """Codex, 3.1 round 25: neither a journal nor a later plan can widen what rollback removes."""

    def test_a_tracked_journal_is_refused(self):
        self.adopt()
        self.commit("adopted")
        record = util.read_json(install_mod.install_record_path(self.target))
        entry = self.entry("README.md")
        journal = {"op": "adopt-undo", "phase": "undoing", "adoption": dict(record["adoption"], created=[entry]),
                   "trusted": {"README.md": entry["sha256"]}}
        util.write_json(install_mod.journal_path(self.target), journal)
        run_git(self.target, "add", "-f", ".aios/txn.json")
        self.commit("a journal, as a pull request could bring")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("not the installer's journal", out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "README.md")))

    def test_a_resumed_undo_re_derives_what_it_may_remove(self):
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        code, _o, _e = self.cli("rollback", "--target", self.target, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:adopt.undo_before"})
        self.assertEqual(code, 137)
        journal = install_mod.load_journal(self.target)
        entry = self.entry("README.md")
        # Whatever a journal claims about what was made is ignored: it holds progress only (round 26).
        journal["adoption"] = {"plan": ".aios/adoption.json", "created": [entry]}
        journal["trusted"] = {"README.md": entry["sha256"]}
        journal["release"] = {"release_id": "starter-9.9.9", "git_rev": "0" * 40}
        util.write_json(install_mod.journal_path(self.target), journal)
        code, out, err = self.cli("rollback", "--target", self.target)
        self.assertNotEqual(code, 0, out + err)  # resuming needs the release's source too
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, "README.md")))
        for p in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, p)), p)

    def test_a_plan_changed_after_the_adoption_cant_widen_it(self):
        self.adopt()
        self.commit("adopted")
        with open(os.path.join(self.source, "README.md"), "rb") as fh:
            write(self.target, "README.md", fh.read().decode("utf-8"))  # ours, with the release's bytes
        plan = json.loads(json.dumps(PLAN))
        plan["instance_owned"].remove("README.md")
        plan["adopt"].append("README.md")
        self.write_plan(plan)
        self.commit("the plan now says README.md is adopted")
        self.rollback_ok()  # the plan as committed with the adoption decides
        self.assertTrue(os.path.isfile(os.path.join(self.target, "README.md")))


class ReviewRoundTwentySix(ReviewRoundTwentyFour):
    """Codex, 3.1 round 26: one anchor for what an adoption made."""

    def test_a_tracked_journal_is_refused_whatever_it_holds(self):
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        for text in ("null", "{}", "[]"):
            with self.subTest(text=text):
                with open(install_mod.journal_path(self.target), "w") as fh:
                    fh.write(text + "\n")
                run_git(self.target, "add", "-f", ".aios/txn.json")
                self.commit("a journal holding %s" % text)
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertNotEqual(code, 0, out + err)
                self.assertIn("not the installer's journal", out + err)
                with open(install_mod.journal_path(self.target)) as fh:
                    self.assertEqual(fh.read(), text + "\n")
                for p in ADOPTED:
                    self.assertTrue(os.path.lexists(os.path.join(self.target, p)), p)

    def test_an_untracked_journal_that_isnt_one_is_refused(self):
        self.adopt()
        self.commit("adopted")
        for text in ("null", "{}", "[]"):
            with self.subTest(text=text):
                with open(install_mod.journal_path(self.target), "w") as fh:
                    fh.write(text + "\n")
                self.be("acme-founder")
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertNotEqual(code, 0, out + err)
                self.assertIn("isn't a journal the installer wrote", out + err)
        os.remove(install_mod.journal_path(self.target))

    def test_a_second_adoption_under_another_plan_rolls_back_exactly(self):
        narrow = json.loads(json.dumps(PLAN))
        narrow["adopt"].remove("START_HERE.md")
        narrow["exclude"].append("START_HERE.md")
        self.write_plan(narrow)
        self.commit("a narrow plan first")
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.commit("the first adoption undone")
        self.write_plan(PLAN)  # wider: START_HERE.md is adopted this time
        self.commit("a wider plan")
        before = _tree(self.target)
        people = harness.config(people=[
            {"github": "acme-founder", "role": "founder", "display_name": "Founder"},
            {"github": "acme-lead", "role": "operator", "display_name": "Lead"}])
        self.adopt(config=people)  # and another people map
        self.commit("adopted again")
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_an_uncommitted_adoption_whose_plan_changed_since_is_refused(self):
        self.adopt()  # never committed
        plan = json.loads(json.dumps(PLAN))
        plan["adopt"].remove("START_HERE.md")
        plan["exclude"].append("START_HERE.md")
        self.write_plan(plan)
        run_git(self.target, "add", ".aios/adoption.json")
        run_git(self.target, "commit", "-qm", "only the plan, narrowed")
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't the one the adoption was made with", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundTwentySeven(ReviewRoundTwentyFour):
    """Codex, 3.1 round 27: committed means in HEAD; present means present; a journal is checked by its path."""

    def kill_undo(self):
        self.be("acme-founder")
        code, _o, _e = self.cli("rollback", "--target", self.target, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:adopt.undo_before"})
        self.assertEqual(code, 137)

    def test_a_second_adoption_only_staged_rolls_back_exactly(self):
        self.adopt()
        self.commit("adopted")
        self.rollback_ok()
        self.commit("the first adoption undone")
        before = _tree(self.target)
        self.adopt()
        run_git(self.target, "add", "-A")  # staged, never committed
        self.rollback_ok()
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_staged_deletion_of_the_committed_record_doesnt_stop_a_resumed_undo(self):
        self.adopt()
        self.commit("adopted")
        self.kill_undo()
        run_git(self.target, "rm", "-q", ".aios/install.json")  # staged deletion, file gone
        self.rollback_ok()

    def test_a_folder_where_the_record_was_is_refused_not_taken_for_none(self):
        self.adopt()  # never committed
        self.kill_undo()
        record = install_mod.install_record_path(self.target)
        os.remove(record)
        os.makedirs(record)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't the install record", out + err)
        for p in ADOPTED:
            self.assertTrue(os.path.lexists(os.path.join(self.target, p)), p)
        self.assertTrue(os.path.isfile(install_mod.journal_path(self.target)))

    def test_with_no_record_an_invalid_journal_still_refuses(self):
        self.be("acme-founder")
        for text in ("null", "{}", "[]"):
            with self.subTest(text=text):
                write(self.target, ".aios/txn.json", text + "\n")
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertNotEqual(code, 0, out + err)
                self.assertIn("isn't a journal the installer wrote", out + err)
                os.remove(install_mod.journal_path(self.target))

    def test_a_folder_at_the_journal_path_is_a_refusal_not_a_crash(self):
        os.makedirs(install_mod.journal_path(self.target))
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't a journal the installer wrote", out + err)
        self.assertNotIn("Traceback", err)


class ReviewRoundTwentyEight(ReviewRoundTwentyFour):
    """Codex, 3.1 round 28."""

    def test_a_committed_lock_left_by_git_rm_cached_is_never_reclaimed(self):
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        run_git(self.target, "add", "-f", ".aios/lock")
        self.commit("a lock file of ours")
        run_git(self.target, "rm", "-q", "--cached", ".aios/lock")  # still in HEAD, still on disk
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.target, ".aios/lock")))

    def test_a_committed_temporary_name_left_by_git_rm_cached_is_never_swept(self):
        self.adopt()
        self.commit("adopted")
        name = ".aios/.txn.json.aaaaaaaa.tmp"
        write(self.target, name, "ours\n")
        run_git(self.target, "add", "-f", name)
        self.commit("a file of ours with that name")
        run_git(self.target, "rm", "-q", "--cached", name)
        self.rollback_ok()
        self.assertTrue(os.path.isfile(os.path.join(self.target, name)))

    def test_a_record_that_is_a_folder_or_unreadable_is_a_refusal(self):
        self.adopt()
        self.commit("adopted")
        record = install_mod.install_record_path(self.target)
        self.be("acme-founder")
        os.chmod(record, 0)
        try:
            code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        finally:
            os.chmod(record, 0o644)
        self.assertNotEqual(code, 0, out + err)
        self.assertNotIn("Traceback", err)
        os.remove(record)
        os.makedirs(record)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't the install record", out + err)

    def test_a_journal_its_operation_couldnt_have_written_is_refused(self):
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        for journal in ({"unexpected": 1}, {"op": "upgrade", "phase": "applying"},
                        {"op": "upgrade", "phase": "applying", "backup": "../elsewhere"},
                        {"op": "rollback", "phase": "restoring", "backup": ".aios/backups/x"},
                        {"op": "adopt-existing", "phase": "writing"},
                        {"op": "adopt-undo", "phase": 3}):
            with self.subTest(journal=journal):
                util.write_json(install_mod.journal_path(self.target), journal)
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertNotEqual(code, 0, out + err)
                self.assertIn("isn't a journal the installer wrote", out + err)
                self.assertNotIn("Traceback", err)
        os.remove(install_mod.journal_path(self.target))


class ReviewRoundTwentyNine(ReviewRoundTwentyFour):
    """Codex, 3.1 round 29: the anchor commit must be the adoption itself."""

    def test_a_record_deleted_and_re_added_forged_is_refused(self):
        self.adopt()
        self.commit("adopted")
        path = install_mod.install_record_path(self.target)
        original = util.read_json(path)
        run_git(self.target, "rm", "-q", ".aios/install.json")
        self.commit("a pull request deletes the record")
        forged = json.loads(json.dumps(original))
        forged["installed_at"] = "re-added"
        forged = install_mod._sealed(forged)  # sealed, and naming the files the real adoption made
        with open(path, "wb") as fh:
            fh.write(install_mod._record_bytes(forged))
        os.chmod(path, 0o644)
        self.commit("another pull request re-adds it")
        self.forget_state()
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("doesn't match the adoption that commit made", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_an_adoption_committed_in_one_commit_still_rolls_back_exactly(self):
        before = _tree(self.target)
        self.adopt()
        self.commit("adopted, as one commit")
        self.rollback_ok()
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundThirty(Existing):
    """Gemini, 3.1 round 30: a plan that isn't an object is a refusal, never a crash."""

    def test_a_plan_that_isnt_an_object_refuses_cleanly(self):
        for text in ("", "null", "[]", "3"):
            with self.subTest(text=text):
                write(self.target, ".aios/adoption.json", text)
                self.commit("a broken plan %r" % text)
                exc = self.refuses_unchanged(self.adopt)
                self.assertIsInstance(exc, Refusal)
        for plan in (None, [], 3, "x"):
            self.assertTrue(install_mod._plan_problems(plan))


class ReviewRoundThirtyCodex(ReviewRoundTwentyFour):
    """Codex, 3.1 round 30: a re-added record claiming fewer files is refused too."""

    def re_add(self, mutate):
        self.adopt()
        self.commit("adopted")
        path = install_mod.install_record_path(self.target)
        original = util.read_json(path)
        run_git(self.target, "rm", "-q", ".aios/install.json")
        self.commit("a pull request deletes the record")
        forged = json.loads(json.dumps(original))
        mutate(forged)
        forged = install_mod._sealed(forged)
        with open(path, "wb") as fh:
            fh.write(install_mod._record_bytes(forged))
        os.chmod(path, 0o644)
        self.commit("another re-adds it, claiming less")
        self.forget_state()

    def refused_unchanged(self):
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("doesn't match the adoption that commit made", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_an_empty_created_list_is_refused(self):
        self.re_add(lambda r: r["adoption"].__setitem__("created", []))
        self.refused_unchanged()

    def test_an_incomplete_created_list_is_refused(self):
        self.re_add(lambda r: r["adoption"].__setitem__("created", r["adoption"]["created"][1:]))
        self.refused_unchanged()


class ReviewRoundThirtyOne(ReviewRoundTwentyFour):
    """Codex, 3.1 round 31: a record committed under another spelling is never read as local."""

    def test_head_spelling_matches_as_the_disk_would(self):
        self.adopt()
        self.commit("adopted")
        self.assertEqual(util.head_spelling(self.target, ".aios/install.json"), ".aios/install.json")
        self.assertEqual(util.head_spelling(self.target, ".AIOS/Install.JSON"), ".aios/install.json")
        self.assertIsNone(util.head_spelling(self.target, ".aios/nothing.json"))
        self.assertTrue(util.in_head(self.target, ".AIOS/INSTALL.JSON"))

    def test_a_record_committed_under_another_case_is_refused(self):
        if not _folds_case(self.tmp):
            self.skipTest("this disk keeps case, so the two spellings are two files")
        self.adopt()
        self.commit("adopted")
        run_git(self.target, "mv", ".aios/install.json", ".aios/INSTALL.JSON")
        self.commit("a pull request renames the record's case")
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("is committed as .aios/INSTALL.JSON", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])


class ReviewRoundThirtyTwo(ReviewRoundTwentyFour):
    """Codex, 3.1 round 32."""

    def test_every_equivalent_folder_is_followed(self):
        self.adopt()
        self.commit("adopted")
        blob = util.git(self.target, ["hash-object", "-w", ".aios/install.json"])
        run_git(self.target, "update-index", "--add", "--cacheinfo", "100644,%s,.AIOS/INSTALL.JSON" % blob)
        run_git(self.target, "commit", "-qm", "the record under another folder spelling too")
        self.assertEqual(util.head_spellings(self.target, ".aios/install.json"),
                         [".AIOS/INSTALL.JSON", ".aios/install.json"])
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("not just .aios/install.json", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def upgraded(self):
        self.adopt()
        self.commit("adopted")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        v31 = harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))
        install_mod.upgrade(self.target, v31, self.source)
        self.commit("upgraded")
        return install_mod.install_record_path(self.target)

    def test_a_record_changed_after_an_upgrade_is_never_trusted_by_its_rollback(self):
        write(self.target, ".env", "SECRET=ours\n")  # ignored, local
        record_path = self.upgraded()
        record = util.read_json(record_path)
        record["managed"].append({"path": ".env", "sha256": "0" * 64, "exec": False})
        util.write_json(record_path, record)
        self.commit("a pull request adds .env to the record")
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("isn't the one this workspace's last operation wrote", ctx.exception.message)
        self.forget_state()  # and without the note, the upgrade's own copy refuses it
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("changed since the upgrade wrote it", ctx.exception.message)
        with open(os.path.join(self.target, ".env")) as fh:
            self.assertEqual(fh.read(), "SECRET=ours\n")

    def test_an_adopted_upgrade_without_its_record_copy_is_refused(self):
        record_path = self.upgraded()
        backup = util.read_json(record_path)["previous"]["backup"]
        os.remove(os.path.join(self.target, backup, "after.json"))
        self.forget_state()
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("kept no copy of the record it wrote", ctx.exception.message)

    def test_an_untouched_upgrade_still_rolls_back(self):
        self.upgraded()
        install_mod.rollback(self.target, self.source)
        with open(os.path.join(self.target, "START_HERE.md")) as fh:
            self.assertNotIn("new.", fh.read())


class ReviewRoundThirtyThree(ReviewRoundThirtyTwo):
    """Codex and Gemini, 3.1 round 33: a trusted local state head, and snapshots that are the installer's."""

    def test_a_replayed_older_record_is_refused(self):
        self.adopt()
        self.commit("adopted")
        adopted_at = util.git(self.target, ["rev-parse", "HEAD"])
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        install_mod.upgrade(self.target, harness.approve(harness.build_manifest(self.source, rev, "3.1.0")),
                            self.source)
        self.commit("upgraded")
        run_git(self.target, "checkout", adopted_at, "--", ".aios/install.json")
        self.commit("a pull request restores the adoption's record")
        before = _tree(self.target)
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't the one this workspace's last operation wrote", out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_committed_snapshot_is_never_trusted(self):
        record_path = self.upgraded()
        backup = util.read_json(record_path)["previous"]["backup"]
        run_git(self.target, "add", "-f", backup + "/after.json")
        self.commit("a pull request commits the snapshot's copy")
        self.forget_state()
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("holds files the repository tracks", ctx.exception.message)

    def test_an_adopted_instance_is_known_by_its_snapshot_not_its_record(self):
        record_path = self.upgraded()
        record = util.read_json(record_path)
        backup = record["previous"]["backup"]
        os.remove(os.path.join(self.target, backup, "after.json"))
        record.pop("adoption", None)  # a pull request makes it look like an older, non-adopted upgrade
        util.write_json(record_path, record)
        self.commit("the record no longer says adopted")
        self.forget_state()
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("kept no copy of the record it wrote", ctx.exception.message)

    def test_the_plan_must_be_committed_under_its_own_name(self):
        if not _folds_case(self.tmp):
            self.skipTest("this disk keeps case, so the two spellings are two files")
        run_git(self.target, "mv", ".aios/adoption.json", ".aios/ADOPTION.json")
        self.commit("the plan committed under another case")
        exc = self.refuses_unchanged(self.adopt)
        self.assertIn("must be committed as .aios/adoption.json exactly", exc.message)


class ReviewRoundThirtyFour(ReviewRoundThirtyTwo):
    """Codex and Gemini, 3.1 round 34: the state note's folder is the installer's own, and leaves nothing."""

    NOTE = ".aios/backups/state/head.json"

    def bump(self):
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        return harness.approve(harness.build_manifest(self.source, rev, "3.1.0"))

    def test_a_tracked_note_is_refused_before_any_change(self):
        self.adopt()
        self.commit("adopted")
        run_git(self.target, "add", "-f", self.NOTE)
        self.commit("a pull request commits the note")
        before = _tree(self.target)
        with self.assertRaises(Refusal) as ctx:
            install_mod.upgrade(self.target, self.bump(), self.source)
        self.assertIn("state note isn't its own", ctx.exception.message)
        self.assertEqual(diff(before, _tree(self.target)), [])
        with self.assertRaises(Refusal):
            install_mod.rollback(self.target, self.source)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_linked_state_folder_is_refused_and_nothing_outside_is_written(self):
        self.adopt()
        self.commit("adopted")
        outside = os.path.join(self.tmp, "outside")
        os.makedirs(outside)
        state = os.path.join(self.target, ".aios", "backups", "state")
        shutil.rmtree(state)
        os.symlink(outside, state)
        with self.assertRaises(Refusal):
            install_mod.upgrade(self.target, self.bump(), self.source)
        self.assertEqual(os.listdir(outside), [])

    def test_a_kill_while_the_note_is_written_leaves_nothing_after_rollback(self):
        before = _tree(self.target)
        self.be("acme-founder")
        cfg = self.write_json("org.json", harness.config())
        rel = self.write_json("release.json", self.v)
        code, _o, _e = self.cli("adopt", "--existing", "--release", rel, "--target", self.target,
                                "--config", cfg, "--repo", self.source, env={"AIOS_FAULT": "crash:state.after_dir"})
        self.assertEqual(code, 137)
        write(self.target, ".aios/backups/state/.head.json.abcd1234.tmp", "{}")  # as a kill inside the write leaves
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(diff(before, _tree(self.target)), [])

    def test_a_malformed_record_entry_is_a_refusal_not_a_crash(self):
        record_path = self.upgraded()
        record = util.read_json(record_path)
        record["managed"].append("not-an-entry")
        util.write_json(record_path, record)
        self.forget_state()
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("outside the workspace", ctx.exception.message)


class ReviewRoundThirtyFive(ReviewRoundThirtyTwo):
    """Codex, 3.1 round 35: recovery trusts only the records the interrupted operation knew."""

    def killed_upgrade(self, point="upgrade.before_record"):
        self.adopt()
        self.commit("adopted")
        rev = harness.bump_source(self.source, {"START_HERE.md": "# start here\nnew.\n"}, "3.1")
        rel = self.write_json("release-3.1.json", harness.approve(harness.build_manifest(self.source, rev, "3.1.0")))
        self.be("acme-founder")
        code, _o, _e = self.cli("upgrade", "--release", rel, "--target", self.target, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:" + point})
        self.assertEqual(code, 137)

    def test_a_record_changed_during_an_interrupted_upgrade_is_refused(self):
        self.killed_upgrade()
        write(self.tmp, "victim.txt", "outside\n")
        path = install_mod.install_record_path(self.target)
        record = util.read_json(path)
        record["managed"].append({"path": "../victim.txt", "sha256": "0" * 64, "exec": False})
        util.write_json(path, record)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("isn't the one the interrupted upgrade started from", out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "victim.txt")))

    def test_an_unsafe_path_in_an_interrupted_upgrades_journal_is_refused(self):
        self.killed_upgrade()
        journal = install_mod.load_journal(self.target)
        journal["adds"] = list(journal.get("adds") or []) + ["../victim.txt"]
        util.write_json(install_mod.journal_path(self.target), journal)
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("outside the workspace", out + err)

    def test_a_resumed_rollback_refuses_a_tracked_snapshot(self):
        record_path = self.upgraded()
        backup = util.read_json(record_path)["previous"]["backup"]
        self.be("acme-founder")
        code, _o, _e = self.cli("rollback", "--target", self.target, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:rollback.before_restore"})
        self.assertEqual(code, 137)
        run_git(self.target, "add", "-f", backup + "/install.json")
        run_git(self.target, "commit", "-qm", "a pull request commits the snapshot")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("holds files the repository tracks", out + err)

    def test_a_falsey_field_that_isnt_a_list_is_refused(self):
        record_path = self.upgraded()
        backup = util.read_json(record_path)["previous"]["backup"]
        snap = os.path.join(self.target, backup, "install.json")
        original = util.read_json(snap)
        self.forget_state()
        for value in ({}, "", 0, False):
            with self.subTest(value=value):
                util.write_json(snap, dict(original, managed=value))
                with self.assertRaises(Refusal) as ctx:
                    install_mod.rollback(self.target, self.source)
                self.assertIn("outside the workspace", ctx.exception.message)


class ReviewRoundThirtySix(ReviewRoundThirtyFive):
    """Codex, 3.1 round 36: a missing record is never mistaken for progress."""

    def test_an_interrupted_upgrades_record_deleted_or_broken_is_refused(self):
        for how in ("deleted", "invalid"):
            with self.subTest(how=how):
                self.setUp()
                self.killed_upgrade()
                path = install_mod.install_record_path(self.target)
                if how == "deleted":
                    os.remove(path)
                else:
                    with open(path, "w") as fh:
                        fh.write("{not json")
                before = _tree(self.target)
                code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
                self.assertNotEqual(code, 0, out + err)
                self.assertIn("isn't the one the interrupted upgrade started from", out + err)
                # nothing changed but the killed upgrade's dead lock, which rollback reclaims by design
                self.assertEqual([d for d in diff(before, _tree(self.target)) if d != ".aios/lock"], [])

    def test_a_resumed_undo_finishes_even_after_the_committed_record_was_deleted(self):
        self.adopt()
        self.commit("adopted")
        self.be("acme-founder")
        code, _o, _e = self.cli("rollback", "--target", self.target, "--repo", self.source,
                                env={"AIOS_FAULT": "crash:adopt.undo_before"})
        self.assertEqual(code, 137)
        run_git(self.target, "rm", "-q", ".aios/install.json")
        run_git(self.target, "commit", "-qm", "a pull request deletes the record meanwhile")
        code, out, err = self.cli("rollback", "--target", self.target, "--repo", self.source)
        self.assertEqual(code, 0, out + err)
        for p in ADOPTED:
            self.assertFalse(os.path.lexists(os.path.join(self.target, p)), p)


class ReviewRoundThirtySeven(ReviewRoundThirtyTwo):
    """Codex, 3.1 round 37: a finished rollback's leftover journal is checked against the note too."""

    def test_a_finished_rollback_killed_before_cleanup_refuses_a_changed_record(self):
        self.upgraded()
        install_mod.rollback(self.target, self.source)  # finished: the note names the restored record
        self.commit("rolled back")
        record_path = install_mod.install_record_path(self.target)
        current = util.read_json(record_path)
        util.write_json(install_mod.journal_path(self.target),
                        {"op": "rollback", "phase": "complete", "backup": ".aios/backups/x", "current_record": current})
        write(self.target, "notes/ours.md", "ours\n")
        changed = json.loads(json.dumps(current))
        changed["managed"].append({"path": "notes/ours.md", "sha256": util.sha256_file(
            os.path.join(self.target, "notes/ours.md")), "exec": False})
        util.write_json(record_path, changed)
        self.commit("a pull request adds a file of ours to the record")
        before = _tree(self.target)
        with self.assertRaises(Refusal) as ctx:
            install_mod.rollback(self.target, self.source)
        self.assertIn("isn't the one this workspace's last operation wrote", ctx.exception.message)
        self.assertEqual(diff(before, _tree(self.target)), [])
        self.assertTrue(os.path.isfile(install_mod.journal_path(self.target)))
