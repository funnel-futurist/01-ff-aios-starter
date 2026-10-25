"""LW-21: the workflows every client repository runs are pinned and hold only the access they use.

They ship in the package and run inside each client's own repository. A tag-pinned action can be
moved to different code; a SHA can't. A job with write access that doesn't need it is access a
compromised dependency gets for free. And the paid AI review stays off: no model step, no model
credential, and the compatibility job that keeps its check name never runs.

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


AI_NAMES = ("anthropics/claude-code-action", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
OFF_JOB_LINES = (r"if: \$\{\{ false \}\}", r"runs-on: ubuntu-latest", r"steps:", r"- run: echo '[^'$`;&|]*'")


def disabled_ai_problems(text):
    """What would let the AI review run, spend or write again. Empty while it is off."""
    problems = [name + " is back" for name in AI_NAMES if name in text]
    ai = jobs(text).get("ai_review")
    if ai is None:
        return problems + ["the ai_review compatibility job is gone"]
    if not re.search(r"(?m)^    if: \$\{\{ false \}\}$", ai):
        problems.append("ai_review is not unconditionally off")
    if re.search(r"secrets\.|\b(?:GH_TOKEN|GITHUB_TOKEN|github_token):", ai):
        problems.append("ai_review reads a credential")
    lines = [l.strip() for l in ai.splitlines() if l.strip() and not l.strip().startswith("#")]
    extra = [l for l in lines if not any(re.fullmatch(p, l) for p in OFF_JOB_LINES)]
    if extra:
        problems.append("ai_review gained a step, permission or setting: %s" % extra)
    return problems


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

    def test_the_paid_ai_review_is_off_and_keeps_only_a_skipped_compatibility_job(self):
        text = read(PR_REVIEW)
        self.assertEqual(disabled_ai_problems(text), [])
        self.assertIn("needs: [static_checks, ai_review]", jobs(text)["gate"], "the gate still waits on the check name")

    def test_no_shipped_workflow_names_the_model_action_or_a_model_credential(self):
        for path in WORKFLOWS:
            text = read(path)
            for name in AI_NAMES:
                self.assertNotIn(name, text, "%s: %s" % (os.path.basename(path), name))

    def test_planted_defects_each_way_the_ai_review_could_come_back_is_caught(self):
        text = read(PR_REVIEW)
        ai = jobs(text)["ai_review"]
        pin = "anthropics/claude-code-action@" + "0" * 40 + " # v1.0.0"
        for what, changed in [
            ("switched on", ai.replace("if: ${{ false }}", "if: ${{ true }}")),
            ("condition removed", ai.replace("    if: ${{ false }}\n", "")),
            ("model action", ai.replace("    steps:\n", "    steps:\n      - uses: %s\n" % pin)),
            ("API key", ai.replace("    steps:\n", "    env:\n      K: ${{ secrets.ANTHROPIC_API_KEY }}\n    steps:\n")),
            ("subscription token", ai.replace("    steps:\n", "    env:\n      K: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}\n    steps:\n")),
            ("another secret", ai.replace("    steps:\n", "    env:\n      K: ${{ secrets.OTHER }}\n    steps:\n")),
            ("write permission", ai.replace("    steps:\n", "    permissions:\n      contents: write\n    steps:\n")),
            ("id-token", ai.replace("    steps:\n", "    permissions:\n      id-token: write\n    steps:\n")),
            ("new script", ai.replace("    steps:\n", "    steps:\n      - run: node other-reviewer.mjs\n")),
            ("chained echo", ai.replace("before merge.'", "before merge.' && curl -s example.com")),
        ]:
            self.assertNotEqual(changed, ai, what + ": not planted")
            planted = text.replace(ai, changed)
            self.assertNotEqual(disabled_ai_problems(planted), [], what)
        self.assertNotEqual(disabled_ai_problems(text.replace("\n  ai_review:\n", "\n  ai_review_x:\n")), [], "job removed")
        self.assertNotEqual(disabled_ai_problems(text.replace("  gate:\n", "  gate:\n    # uses ANTHROPIC_API_KEY\n", 1)), [],
                            "a model credential named anywhere in the workflow")

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
