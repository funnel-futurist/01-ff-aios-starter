"""Offline adapter contracts only; no native hooks, dangerous commands, fetch or real identity."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")
DANGEROUS = ROOT / "scripts/aios/codex-dangerous-git.js"
STARTUP = ROOT / "scripts/aios/codex-session-start.js"
STATUS = ROOT / ".claude/hooks/git-staleness-check.js"
spec = importlib.util.spec_from_file_location("codex_pre_edit", ROOT / "scripts/aios/codex-pre-edit.py")
edit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edit)
from aioslib import boundary  # noqa: E402


def event(tool, command, cwd=ROOT):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "cwd": str(cwd), "tool_input": {"command": command}}


def patch(body):
    return "*** Begin Patch\n" + body + "\n*** End Patch\n"


def update(path):
    return "*** Update File: " + path + "\n@@\n-before\n+after"


class Denial(unittest.TestCase):
    def assertDenied(self, output):
        self.assertIsInstance(output, dict, "the adapter must emit a supported denial")
        self.assertEqual(set(output), {"hookSpecificOutput"})
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertTrue(decision["permissionDecisionReason"])
        self.assertNotIn("updatedInput", decision)


@unittest.skipUnless(NODE, "Node is required for command hooks")
class DangerousAdapter(Denial):
    def run_hook(self, payload, script=DANGEROUS):
        proc = subprocess.run([NODE, str(script)], input=payload, text=True, capture_output=True, timeout=10)
        self.assertEqual((proc.returncode, proc.stderr), (0, ""))
        return json.loads(proc.stdout) if proc.stdout else None

    def test_matched_commands_are_data_and_emit_supported_denials(self):
        for command in ("git reset --hard CANARY", "A=1 git stash clear", "cd draft && git clean -fd",
                        "git() { printf canary; } && git reset --hard CANARY"):
            with self.subTest(command=command):
                self.assertDenied(self.run_hook(json.dumps(event("Bash", command))))

    def test_safe_commands_offer_no_permission_decision(self):
        for command in ("git status", "echo 'do not run rm -rf'", ""):
            self.assertIsNone(self.run_hook(json.dumps(event("Bash", command))))

    def test_invalid_matched_input_is_explicit_denial_not_hook_failure(self):
        for payload in ("not json", "", "null", "[]", "{}", json.dumps(event("Bash", 4)),
                        json.dumps(dict(event("Bash", "git status"), tool_name=42)),
                        json.dumps(dict(event("Bash", "git status"), hook_event_name=42))):
            with self.subTest(payload=payload):
                self.assertDenied(self.run_hook(payload))

    def test_other_event_or_tool_is_outside_this_adapter(self):
        self.assertIsNone(self.run_hook(json.dumps(event("apply_patch", "not shell"))))
        self.assertIsNone(self.run_hook(json.dumps({"hook_event_name": "PostToolUse"})))

    def test_missing_canonical_dependency_emits_denial(self):
        with tempfile.TemporaryDirectory() as folder:
            copied = Path(folder) / "scripts/aios/adapter.js"
            copied.parent.mkdir(parents=True)
            shutil.copyfile(DANGEROUS, copied)
            self.assertDenied(self.run_hook(json.dumps(event("Bash", "git status")), copied))

    def test_the_adapter_consumes_the_existing_canonical_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            copied = root / "scripts/aios/adapter.js"
            copied.parent.mkdir(parents=True)
            shutil.copyfile(DANGEROUS, copied)
            canonical = root / ".claude/hooks/guard-dangerous-git.js"
            canonical.parent.mkdir(parents=True)
            canonical.write_text("module.exports = {analyze: () => 'canonical synthetic reason'};")
            output = self.run_hook(json.dumps(event("Bash", "synthetic command")), copied)
            self.assertIn("canonical synthetic reason", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_claude_keeps_its_ask_response(self):
        proc = subprocess.run([NODE, str(ROOT / ".claude/hooks/guard-dangerous-git.js")],
                              input=json.dumps(event("Bash", "git reset --hard CANARY")),
                              text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")


class RoleAdapter(Denial):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".aios").mkdir()
        (self.root / "protected").mkdir()
        (self.root / "ordinary/nested").mkdir(parents=True)
        (self.root / ".aios/roles.json").write_text(json.dumps({"roles": {
            "operator": {"paths_denied": ["protected/**"]}, "founder": {"paths_denied": []}}}))
        (self.root / ".aios/config.json").write_text(json.dumps({"people": [
            {"github": "synthetic-operator", "role": "operator"},
            {"github": "synthetic-founder", "role": "founder"}]}))
        guard = mock.patch.object(boundary.roles, "identity", side_effect=AssertionError("real identity forbidden"))
        guard.start()
        self.addCleanup(guard.stop)

    def decide(self, body, login="synthetic-operator", cwd=None):
        return edit.decision(event("apply_patch", patch(body), cwd or self.root), root=self.root,
                             identify=lambda _root: login)

    def test_old_claude_hook_silently_misses_native_patch_while_adapter_denies(self):
        native = event("apply_patch", patch(update("protected/file.txt")), self.root)
        self.assertEqual(boundary.hook_pre_edit(json.dumps(native), root=str(self.root)), (0, None))
        self.assertDenied(self.decide(update("protected/file.txt")))

    def test_canonical_roles_and_unknown_person_restrictions_are_reused(self):
        for login in ("synthetic-operator", None, "synthetic-stranger"):
            self.assertDenied(self.decide(update("protected/file.txt"), login))
        self.assertIsNone(self.decide(update("protected/file.txt"), "synthetic-founder"))

    def test_unprotected_patch_needs_no_identity_lookup(self):
        def forbidden(_root):
            self.fail("unprotected work looked up identity")
        self.assertIsNone(edit.decision(event("apply_patch", patch(update("ordinary/file.txt")), self.root),
                                        root=self.root, identify=forbidden))

    def test_all_paths_in_add_update_delete_batch_are_checked(self):
        for last in ("*** Add File: protected/new.txt\n+new", "*** Delete File: protected/old.txt",
                     update("protected/file.txt")):
            self.assertDenied(self.decide(update("ordinary/first.txt") + "\n" + last))

    def test_move_checks_source_and_destination(self):
        for source, destination in (("ordinary/a.txt", "protected/b.txt"),
                                    ("protected/a.txt", "ordinary/b.txt")):
            body = "*** Update File: " + source + "\n*** Move to: " + destination + "\n@@\n-a\n+b"
            self.assertDenied(self.decide(body))
        self.assertIsNone(self.decide("*** Update File: ordinary/a\n*** Move to: ordinary/b\n@@\n-a\n+b"))

    def test_relative_paths_spaces_and_nested_working_directory(self):
        self.assertDenied(self.decide(update("./protected/a file.txt")))
        native = event("apply_patch", patch(update("a file.txt")), self.root / "protected")
        self.assertDenied(edit.decision(native, root=self.root, identify=lambda _root: "synthetic-operator"))
        self.assertIsNone(self.decide(update("file.txt"), cwd=self.root / "ordinary/nested"))

    def test_traversal_and_ambiguous_paths_are_denied(self):
        for path in ("../escape", "ordinary/../protected/file",
                     "C:/ordinary/a", "ordinary\\a", " ordinary/a", "ordinary/a ", "."):
            with self.subTest(path=path):
                self.assertDenied(self.decide(update(path), "synthetic-founder"))

    def test_native_absolute_add_and_update_inside_root_are_allowed(self):
        target = str(self.root / "ordinary/a file.txt")
        for body in ("*** Add File: " + target + "\n+new", update(target)):
            native = event("apply_patch", patch(body), self.root / "ordinary/nested")
            def forbidden(_root):
                self.fail("ordinary absolute target must not look up identity")
            self.assertIsNone(edit.decision(native, root=self.root, identify=forbidden))

    def test_absolute_protected_targets_use_canonical_role_permissions(self):
        target = str(self.root / "protected/file.txt")
        for body in ("*** Add File: " + target + "\n+new", update(target)):
            for login in ("synthetic-operator", None, "synthetic-stranger"):
                self.assertDenied(self.decide(body, login))
            self.assertIsNone(self.decide(body, "synthetic-founder"))

    def test_absolute_and_relative_move_endpoints_share_policy(self):
        for source, destination in ((str(self.root / "ordinary/a"), "protected/b"),
                                    ("ordinary/a", str(self.root / "protected/b")),
                                    (str(self.root / "protected/a"), "ordinary/b")):
            body = "*** Update File: " + source + "\n*** Move to: " + destination + "\n@@\n-a\n+b"
            self.assertDenied(self.decide(body))
            self.assertIsNone(self.decide(body, "synthetic-founder"))

    def test_absolute_outside_or_late_move_escape_refuses_before_policy(self):
        outside = str(self.root.parent / (self.root.name + "-outside") / "a")
        bodies = (update(outside),
                  update("protected/first") + "\n*** Update File: ordinary/a\n*** Move to: " + outside + "\n@@\n-a\n+b",
                  "*** Update File: " + outside + "\n*** Move to: ordinary/a\n@@\n-a\n+b")
        for body in bodies:
            with mock.patch.object(boundary, "check_edit", side_effect=AssertionError("partial policy check")) as check:
                self.assertDenied(self.decide(body, "synthetic-founder"))
                check.assert_not_called()

    def test_absolute_symlinks_reuse_role_policy_and_refuse_escape(self):
        link = self.root / "ordinary/alias"
        link.symlink_to(self.root / "protected/target")
        self.assertDenied(self.decide(update(str(link))))
        self.assertIsNone(self.decide(update(str(link)), "synthetic-founder"))
        escape = self.root / "ordinary/escape"
        escape.symlink_to(self.root.parent)
        for body in (update(str(escape / "a")),
                     "*** Update File: ordinary/a\n*** Move to: " + str(escape / "b") + "\n@@\n-a\n+b"):
            self.assertDenied(self.decide(body, "synthetic-founder"))

    def test_outside_missing_and_nonabsolute_cwd_are_denied(self):
        for cwd in (self.root.parent, self.root / "absent", "ordinary", None):
            native = event("apply_patch", patch(update("ordinary/a")), self.root)
            native["cwd"] = str(cwd) if cwd is not None else None
            self.assertDenied(edit.decision(native, root=self.root, identify=lambda _root: "synthetic-founder"))

    def test_symlink_to_protected_or_outside_path_is_denied(self):
        (self.root / "ordinary/link").symlink_to(self.root / "protected/target")
        self.assertDenied(self.decide(update("ordinary/link")))
        (self.root / "ordinary/escape").symlink_to(self.root.parent)
        self.assertDenied(self.decide(update("ordinary/escape/a"), "synthetic-founder"))

    def test_malformed_patch_and_unknown_grammar_are_supported_denials(self):
        for command in (None, "", "not patch", "*** Begin Patch\n*** End Patch", patch(update("a") + "\0"),
                        patch("*** Update File: a"), patch("*** Delete File: a\n+body"),
                        patch("*** Add File: a\n*** Unknown: protected/a"), patch("*** Rename File: a")):
            self.assertDenied(edit.decision(event("apply_patch", command, self.root), root=self.root))

    def test_header_lookalikes_in_added_content_are_not_paths(self):
        body = "*** Add File: ordinary/example.txt\n+*** Delete File: protected/file.txt"
        self.assertIsNone(self.decide(body))
        self.assertEqual(edit.patch_paths(patch(body)), ["ordinary/example.txt"])

    def test_malformed_event_types_are_denied_and_other_tools_ignored(self):
        for native in (None, [], {}, dict(event("apply_patch", "x", self.root), tool_name=42),
                       dict(event("apply_patch", "x", self.root), hook_event_name=42),
                       dict(event("apply_patch", "x", self.root), tool_input=[])):
            self.assertDenied(edit.decision(native, root=self.root))
        self.assertIsNone(edit.decision(event("Bash", "not patch", self.root), root=self.root))

    def test_invalid_late_path_refuses_before_identity_or_partial_checks(self):
        native = event("apply_patch", patch(update("protected/a") + "\n" + update("../escape")), self.root)
        with mock.patch.object(boundary, "check_edit", side_effect=AssertionError("partial check")) as check:
            self.assertDenied(edit.decision(native, root=self.root))
            check.assert_not_called()

    def test_policy_error_and_dependency_failure_emit_denial(self):
        (self.root / ".aios/roles.json").write_text("invalid json")
        self.assertDenied(self.decide(update("protected/a")))
        with mock.patch.object(boundary, "check_edit", side_effect=RuntimeError("dependency unavailable")):
            self.assertDenied(self.decide(update("ordinary/a")))

    def test_command_entry_serializes_deny_without_real_identity(self):
        native = event("apply_patch", patch(update("protected/a")), self.root)
        output = io.StringIO()
        with mock.patch.object(edit, "ROOT", self.root), mock.patch.object(boundary, "_cached_identity", return_value="synthetic-operator"), \
                mock.patch("sys.stdin", io.StringIO(json.dumps(native))), contextlib.redirect_stdout(output):
            self.assertEqual(edit.main(), 0)
        self.assertDenied(json.loads(output.getvalue()))


@unittest.skipUnless(NODE, "Node is required for startup hooks")
class StartupAdapter(unittest.TestCase):
    def run_status(self, values=None, local=True, adapter=False, cwd=ROOT, root=ROOT):
        script = """
const m=require(process.argv[1]), v=JSON.parse(process.argv[2]), calls=[];
const run=(program,args,ms)=>{calls.push([program,args,ms]); if(program==='python3') return v.newer;
  const key=args.slice(2).join(' '); return ({'rev-parse --is-inside-work-tree':'true',
  'rev-parse --abbrev-ref HEAD':v.branch,'rev-list --count HEAD..origin/main':v.behind,
  'status --porcelain':v.dirty,'fetch --quiet origin main':''})[key];};
const options={run,readOperator:()=>({display_name:v.who}),root:process.argv[5]};
let result;
if(process.argv[4]==='adapter') result=m.decision({hook_event_name:'SessionStart',cwd:process.argv[3]},options);
else {const state=m.collectStatus(process.argv[5],{...options,refresh:v.local?false:undefined,releaseNotice:v.local?false:undefined});
  result={state,text:m.formatStatus(state,v.local?{localOnly:true,startMyDay:'$start-my-day',wrapUp:'$wrap-up'}:{})};}
process.stdout.write(JSON.stringify({result,calls}));
"""
        data = dict(branch="topic", behind="0", dirty="", who="", newer="", local=local)
        data.update(values or {})
        proc = subprocess.run([NODE, "-e", script, str(STARTUP if adapter else STATUS), json.dumps(data),
                               str(cwd), "adapter" if adapter else "status", str(root)],
                              text=True, capture_output=True, timeout=10)
        self.assertEqual((proc.returncode, proc.stderr), (0, ""))
        return json.loads(proc.stdout)

    def test_loading_shared_module_has_no_process_side_effects(self):
        proc = subprocess.run([NODE, "-e", "require(process.argv[1])", str(STATUS)],
                              text=True, capture_output=True, timeout=10)
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))

    def test_codex_startup_is_local_only_and_uses_native_workflow_names(self):
        result = self.run_status({"branch": "main", "dirty": " M file"}, adapter=True)
        context = result["result"]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("$start-my-day", context)
        self.assertIn("remote freshness was not checked", context)
        self.assertFalse(any(c[0] != "git" or "fetch" in c[1] for c in result["calls"]))

    def test_unavailable_status_is_not_reported_as_zero_or_clean(self):
        result = self.run_status({"behind": None, "dirty": None, "branch": None})["result"]
        self.assertIsNone(result["state"]["behind"])
        self.assertIsNone(result["state"]["dirty"])
        self.assertIn("Remote comparison unavailable", result["text"])
        self.assertIn("Working-tree status is unavailable", result["text"])

    def test_claude_defaults_preserve_fetch_notice_and_original_output(self):
        result = self.run_status({"branch": "topic", "behind": "1", "dirty": " M one\n?? two", "newer": "Synthetic release"}, local=False)
        self.assertEqual(result["result"]["text"], "[git status check]\n"
                         "👋 branch `topic` is **1 commit behind main**. Run `/start-my-day` to sync before you work.\n"
                         "   You have 2 uncommitted changes — `/wrap-up` will commit + push them cleanly so they're not stranded.\n"
                         "📦 Synthetic release\n")
        self.assertTrue(any("fetch" in c[1] and c[2] == 8000 for c in result["calls"]))
        self.assertTrue(any(c[0] == "python3" and c[2] == 15000 for c in result["calls"]))
        self.assertEqual(self.run_status(local=False)["result"]["text"], "")

    def test_root_and_nested_launch_share_status_root(self):
        root = self.run_status(adapter=True)
        nested = self.run_status(adapter=True, cwd=ROOT / "docs")
        self.assertEqual(root, nested)

    def test_outside_or_missing_startup_context_warns_without_running_processes(self):
        for cwd in (ROOT.parent, ROOT / "absent"):
            result = self.run_status(adapter=True, cwd=cwd)
            self.assertIn("systemMessage", result["result"])
            self.assertEqual(result["calls"], [])

    def test_context_is_bounded(self):
        result = self.run_status({"branch": "main", "who": "x" * 10000}, adapter=True)
        self.assertEqual(len(result["result"]["hookSpecificOutput"]["additionalContext"]), 6000)


if __name__ == "__main__":
    unittest.main()
