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
        for point in ("adopt.after_journal", "adopt.mid_write", "adopt.before_record"):
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
        code, out, err = self.cli("rollback", "--target", self.target)
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
                code, _o, _e = self.kill(point, "rollback", "--target", self.target)
                self.assertEqual(code, 137)
                code, out, err = self.cli("rollback", "--target", self.target)
                self.assertEqual(code, 0, out + err)
                self.assertEqual(diff(before, snapshot(self.target)), [])

    def test_c5_a_dead_lock_from_before_the_journal_clears_without_a_people_map(self):
        write(self.target, ".aios/lock", "adopt pid=999999 at then\n")
        code, out, err = self.cli("rollback", "--target", self.target)
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing to roll back", out)
        self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_c6_c8_rollback_compares_the_mode_the_disk_reported(self):
        record = self.adopt()
        for c in record["adoption"]["created"]:
            self.assertEqual(c["mode"], os.lstat(os.path.join(self.target, c["path"])).st_mode & 0o7777)
        os.chmod(os.path.join(self.target, ".aios/config.json"), 0o600)
        _r, _s, how = install_mod.rollback(self.target)
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
        code, out, err = self.cli("rollback", "--target", self.target)
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
        code, out, err = self.cli("rollback", "--target", self.target)
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
        install_mod.rollback(self.target)
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
        code, out, err = self.cli("rollback", "--target", self.target)
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
        code, out, err = self.cli("rollback", "--target", self.target)
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
        code, out, err = self.cli("rollback", "--target", self.target)
        self.assertEqual(code, 0, out + err)
        self.assertIn("cleared a dead operation's lock", out)
        self.assertFalse(os.path.lexists(os.path.join(self.target, ".aios/lock")))

    def test_a_live_lock_is_still_never_taken_without_a_role(self):
        write(self.target, ".aios/config.json", json.dumps(harness.config()))
        self.no_rollback_policy()
        self.commit("our config, and a policy nobody may roll back with")
        write(self.target, ".aios/lock", "adopt pid=%d at now\n" % os.getpid())
        self.be("acme-founder")
        code, out, err = self.cli("rollback", "--target", self.target)
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
