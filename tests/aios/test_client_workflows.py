"""LW-21: the workflows every client repository runs are pinned and hold only the access they use.

They ship in the package and run inside each client's own repository. A tag-pinned action can be
moved to different code; a SHA can't. A job with write access that doesn't need it is access a
compromised dependency gets for free. And the AI reviewer must not be able to change the branch
it reviews, whatever its prompt says.

Standard library only, so no YAML parser: the checks read the text, job by job.
"""

import glob
import os
import re
import unittest

import harness

WORKFLOWS = sorted(glob.glob(os.path.join(harness.REPO_ROOT, ".github", "workflows", "*.yml")))
PR_REVIEW = os.path.join(harness.REPO_ROOT, ".github", "workflows", "pr-review.yml")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def jobs(text):
    """{job name: its text}, for the two-space-indented keys under `jobs:`."""
    body = text.split("\njobs:\n", 1)[1]
    out, name = {}, None
    for line in body.splitlines():
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m:
            name = m.group(1)
            out[name] = ""
        elif name:
            out[name] += line + "\n"
    return out


def disabled_ai_problems(workflow):
    ai = jobs(workflow).get("ai_review", "")
    problems = []
    if not re.search(r"^    if: \$\{\{ false \}\}$", ai, re.M):
        problems.append("job not unconditionally disabled")
    if re.search(r"uses:\s*['\"]?anthropics/claude-code-action", workflow):
        problems.append("paid action restored")
    if re.search(r"secrets\.|\b(?:GH_TOKEN|GITHUB_TOKEN|github_token):", ai):
        problems.append("credential path restored")
    allowed = [r"if: \$\{\{ false \}\}", r"runs-on: ubuntu-latest", r"steps:", r"- run: echo .+"]
    for line in ai.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not any(re.fullmatch(pattern, line) for pattern in allowed):
            problems.append("execution or permissions added")
    return problems


class Pins(unittest.TestCase):

    def test_every_action_in_every_shipped_workflow_is_pinned_to_a_full_sha(self):
        self.assertTrue(WORKFLOWS)
        for path in WORKFLOWS:
            for line in read(path).splitlines():
                m = re.match(r"^\s*-?\s*uses:\s*(\S+)(.*)$", line)
                if not m or m.group(1).startswith("./"):
                    continue
                self.assertRegex(m.group(1), r"^[\w.-]+/[\w.-]+(/[\w./-]+)?@[0-9a-f]{40}$",
                                 "%s: %s is not pinned to a commit SHA" % (os.path.basename(path), m.group(1)))
                self.assertRegex(m.group(2), r"#\s*v\d", "%s: say the version beside the pin" % line.strip())


class Permissions(unittest.TestCase):

    def test_every_shipped_workflow_declares_its_permissions(self):
        for path in WORKFLOWS:
            self.assertRegex(read(path), r"(?m)^permissions:", os.path.basename(path))

    def test_pr_review_grants_nothing_by_default(self):
        self.assertRegex(read(PR_REVIEW), r"(?m)^permissions: \{\}\s*$")

    def test_only_the_automerge_job_can_write_code_and_only_when_switched_on(self):
        found = jobs(read(PR_REVIEW))
        self.assertEqual(set(found), {"static_checks", "ai_review", "gate", "automerge"})
        for name, text in found.items():
            if name == "automerge":
                self.assertIn("contents: write", text)
                self.assertIn("vars.PR_AUTOMERGE == 'on'", text)
                self.assertIn("needs.gate.outputs.eligible == 'true'", text)
            else:
                self.assertNotIn("contents: write", text, name)
                self.assertNotIn("gh pr merge", text, name)

    def steps(self, job_text):
        """{step name: its text} for `- name:` steps in one job."""
        out, name = {}, None
        for line in job_text.splitlines():
            m = re.match(r"^      - name: (.+)$", line)
            if m:
                name = m.group(1).strip()
                out[name] = ""
            elif re.match(r"^      - uses:", line):
                name = None
            elif name:
                out[name] += line + "\n"
        return out

    def test_disabled_model_job_has_no_action_credential_or_review_path(self):
        self.assertEqual(disabled_ai_problems(read(PR_REVIEW)), [])
        ai = jobs(read(PR_REVIEW))["ai_review"]
        self.assertNotIn("actions/checkout", ai)
        self.assertNotIn("ai_verdict", ai)
        self.assertNotIn("gh pr review", ai)

    def test_planted_reactivation_and_restored_model_paths_are_refused(self):
        workflow = read(PR_REVIEW)
        ai = jobs(workflow)["ai_review"]
        for label, changed in [
            ("enabled", ai.replace("if: ${{ false }}", "if: ${{ true }}")),
            ("condition removed", ai.replace("    if: ${{ false }}\n", "")),
            ("paid action", ai.replace("    steps:\n", "    steps:\n      - uses: anthropics/claude-code-action@" + "a" * 40 + "\n")),
            ("credential", ai.replace("    steps:\n", "    env:\n      K: ${{ secrets.ANTHROPIC_API_KEY }}\n    steps:\n")),
            ("write access", ai.replace("    steps:\n", "    permissions:\n      contents: write\n    steps:\n")),
            ("script", ai.replace("    steps:\n", "    steps:\n      - run: node another-review.mjs\n")),
        ]:
            with self.subTest(label=label):
                self.assertNotEqual(changed, ai, "control must actually be planted")
                self.assertTrue(disabled_ai_problems(workflow.replace(ai, changed, 1)))

    def test_skipped_ai_is_manual_and_an_incomplete_floor_cannot_qualify(self):
        gate = jobs(read(PR_REVIEW))["gate"]
        self.assertIn("AI_RESULT === 'skipped' ? 'AI review skipped - manual merge only'", gate)
        self.assertIn("STATIC_RESULT: ${{ needs.static_checks.result }}", gate)
        self.assertIn("staticBlocked || !staticReported || STATIC_RESULT !== 'success'", gate)
        self.assertIn("const eligible = AI_RESULT === 'success' && !gateFail", gate)
        self.assertIn("needs: [static_checks, ai_review]", gate)
        self.assertIn("if: always()", gate)

    def test_the_gate_reads_only_this_runs_verdict_and_a_missing_one_is_never_eligible(self):
        gate = jobs(read(PR_REVIEW))["gate"]
        download = gate.split("actions/download-artifact@", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("name: ai_verdict", download)
        self.assertNotIn("run-id", download, "only the artifact from this workflow run")
        self.assertIn("&& !codeownerTouched && v && tierEligible;", gate, "no verdict, no auto-merge")

    def test_the_skill_tells_the_ci_reviewer_to_suggest_not_push(self):
        skill = read(os.path.join(harness.REPO_ROOT, ".claude", "skills", "pr_review", "SKILL.md"))
        ci = skill.split("## CI MODE", 1)[1].split("## FORBIDDEN", 1)[0]
        self.assertNotIn("[pr-autofix]", ci)
        self.assertNotRegex(ci, r"(?i)\bcommit to the PR's head branch\b")
        self.assertNotIn("gh pr review", ci, "in CI the workflow posts; the model has no gh")
        self.assertIn(".pr_context/diff.txt", ci)
        self.assertIn("./review.md", ci)
        self.assertIn("Never edit, commit or push in CI mode", skill)


if __name__ == "__main__":
    unittest.main()
