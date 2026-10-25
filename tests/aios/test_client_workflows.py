"""LW-21: the workflows every client repository runs are pinned and hold only the access they use.

They ship in the package and run inside each client's own repository. A tag-pinned action can be
moved to different code; a SHA can't. A job with write access that doesn't need it is access a
compromised dependency gets for free. And the AI reviewer must not be able to change the branch
it reviews, whatever its prompt says.

Standard library only, so no YAML parser: the checks read the text, job by job.
"""

import ast
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


def credential_result(expression, owner, api_key, oauth):
    """Evaluate only the boolean/comparison subset used by the real Actions expression."""
    expression = expression.strip()
    if not (expression.startswith("${{") and expression.endswith("}}")):
        raise AssertionError("Actions expression delimiters required")
    expression = expression[3:-2].strip()
    for name, value in [("github.repository_owner", owner), ("secrets.ANTHROPIC_API_KEY", api_key),
                        ("secrets.CLAUDE_CODE_OAUTH_TOKEN", oauth)]:
        expression = expression.replace(name, repr(value))
    tree = ast.parse(expression.replace("&&", " and ").replace("||", " or "), mode="eval")
    def value(node):
        if isinstance(node, ast.Expression): return value(node.body)
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.BoolOp):
            result = value(node.values[0])
            for child in node.values[1:]:
                if isinstance(node.op, ast.And) and not result: return result
                if isinstance(node.op, ast.Or) and result: return result
                result = value(child)
            return result
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.NotEq):
            left, right = value(node.left), value(node.comparators[0])
            if isinstance(left, str) and isinstance(right, str):
                left, right = left.casefold(), right.casefold()
            return left != right
        raise AssertionError("unexpected credential expression syntax")
    return value(tree)


def credential_expression(workflow):
    ai = jobs(workflow)["ai_review"]
    found = re.findall(r"^      HAS_CLAUDE_CREDENTIAL: (.+)$", ai, re.M)
    if len(found) != 1: raise AssertionError("one job-level credential decision required")
    return found[0]


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

    def test_the_ai_reviewer_has_no_shell_no_token_and_writes_only_its_two_files(self):
        ai = jobs(read(PR_REVIEW))["ai_review"]
        self.assertNotIn("pull_request.head.ref", ai, "it checks out the branch only to read it")
        self.assertIn("persist-credentials: false", ai)
        tools = re.search(r'--allowedTools "([^"]+)"', ai)
        self.assertTrue(tools, "the reviewer's tools are an explicit list")
        allowed = set(tools.group(1).split(","))
        self.assertEqual(allowed, {"Read", "Glob", "Grep", "Edit(./review.md)", "Edit(./verdict.json)"})
        steps = self.steps(ai)
        model = steps["Claude review (pr_review skill)"]
        self.assertNotIn("GH_TOKEN", model, "the model step holds no GitHub token")
        self.assertNotIn("github.token", model)
        self.assertNotIn("push them", ai)

    def test_a_deterministic_step_posts_the_review_from_the_verdict(self):
        steps = self.steps(jobs(read(PR_REVIEW))["ai_review"])
        self.assertIn("gh pr diff", steps["Collect the pull request for the reviewer"])
        post = steps["Post the review"]
        self.assertIn("has_error_severity", post)
        self.assertIn('"--request-changes" : "--approve"', post)
        self.assertIn("--body-file review.md", post)
        self.assertIn("--comment --body-file review.md", post, "falls back to a comment where Actions can't approve")

    def test_review_files_from_the_pull_request_are_removed_and_a_tracked_verdict_refused(self):
        ai = jobs(read(PR_REVIEW))["ai_review"]
        checkout = ai.index("uses: actions/checkout@")
        discard = ai.index("      - name: Discard review files from the pull request\n")
        collect = ai.index("      - name: Collect the pull request for the reviewer\n")
        review = ai.index("      - name: Claude review (pr_review skill)\n")
        self.assertLess(checkout, discard, "the files are removed after the checkout brings them in")
        self.assertLess(discard, collect, "and before this run's .pr_context/ is written")
        self.assertLess(collect, review)
        step = self.steps(ai)["Discard review files from the pull request"]
        self.assertIn("rm -f verdict.json review.md review_comment.md\n", step)
        self.assertIn("rm -rf .pr_context\n", step, "a .pr_context/ in the pull request is removed too")
        self.assertRegex(step, r"if git ls-files --error-unmatch verdict\.json[^\n]*; then\n[^\n]*\n\s*exit 1",
                         "a pull request that tracks verdict.json is refused")
        def cond(s):
            found = re.findall(r"^ {8}if: (.+)$", s, re.M)
            self.assertEqual(len(found), 1, "one condition, the step's own")
            return found[0]
        checkout_step = ai[checkout:ai.index("\n      - ", checkout)]
        self.assertEqual(cond(step), cond(checkout_step), "the discard runs whenever the pull request is checked out")
        self.assertNotIn("continue-on-error", step, "a refused pull request fails the job")
        self.assertEqual(ai.count("uses: actions/checkout@"), 1, "nothing checks out the pull request again after the discard")
        self.assertEqual(ai.count("      - name: Discard review files from the pull request\n"), 1, "one discard step, the one checked above")

    def test_skipped_ai_is_manual_and_an_incomplete_floor_cannot_qualify(self):
        gate = jobs(read(PR_REVIEW))["gate"]
        self.assertIn("AI_RESULT === 'skipped' ? 'AI review skipped - manual merge only'", gate)
        self.assertIn("STATIC_RESULT: ${{ needs.static_checks.result }}", gate)
        self.assertIn("staticBlocked || !staticReported || STATIC_RESULT !== 'success'", gate)
        self.assertIn("const eligible = AI_RESULT === 'success' && !gateFail", gate)
        self.assertIn("needs: [static_checks, ai_review]", gate)
        self.assertIn("if: always()", gate)


    def test_ff_owner_never_enables_paid_review_and_clients_keep_their_choice(self):
        expression = credential_expression(read(PR_REVIEW))
        for owner in ["funnel-futurist", "FUNNEL-FUTURIST", "client-org", "funnel-futurist-client", "not-funnel-futurist"]:
            for api_key, oauth in [("", ""), ("test-api", ""), ("", "test-oauth"), ("test-api", "test-oauth")]:
                with self.subTest(owner=owner, api=bool(api_key), oauth=bool(oauth)):
                    expected = "yes" if owner.casefold() != "funnel-futurist" and (api_key or oauth) else "no"
                    self.assertEqual(credential_result(expression, owner, api_key, oauth), expected)
        # A missing or inverted owner guard must actually trip the FF-with-credentials control.
        for mutant in [expression.replace("github.repository_owner != 'funnel-futurist' && ", ""),
                       expression.replace("github.repository_owner != 'funnel-futurist'", "github.repository_owner != 'other-owner'")]:
            self.assertNotEqual(mutant, expression)
            self.assertNotEqual(credential_result(mutant, "funnel-futurist", "test-api", ""), "no")

    def test_every_credential_using_step_is_guarded_and_not_configured_is_manual(self):
        ai = jobs(read(PR_REVIEW))["ai_review"]
        steps = self.steps(ai)
        self.assertIn("if: needs.static_checks.outputs.has_block != 'true'", ai)
        for name in ["Discard review files from the pull request", "Collect the pull request for the reviewer",
                     "Claude review (pr_review skill)", "Post the review", "Require a valid verdict (a finished review passes even if the action reported an error)"]:
            conditions = re.findall(r"^        if: (.+)$", steps[name], re.M)
            self.assertEqual(len(conditions), 1, name)
            self.assertIn("env.HAS_CLAUDE_CREDENTIAL == 'yes'", conditions[0], name)
        checkout = ai.split("      - uses: actions/checkout@", 1)[1].split("\n      - ", 1)[0]
        self.assertIn("if: env.HAS_CLAUDE_CREDENTIAL == 'yes'", checkout)
        unconfigured = steps["AI review is not configured"]
        self.assertIn("if: env.HAS_CLAUDE_CREDENTIAL != 'yes'", unconfigured)
        self.assertIn('"configured": false', unconfigured)
        self.assertIn("human review before merge", unconfigured)
        self.assertNotIn("ANTHROPIC_API_KEY:", unconfigured)
        self.assertNotIn("GH_TOKEN:", unconfigured)
        self.assertEqual(ai.count("HAS_CLAUDE_CREDENTIAL:"), 1, "no step may override the job decision")
        gate = jobs(read(PR_REVIEW))["gate"]
        self.assertIn("!!(v && v.configured === false)", gate)
        self.assertIn("!notConfigured", gate)
        self.assertIn("AI review not configured - manual merge only", gate)

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
