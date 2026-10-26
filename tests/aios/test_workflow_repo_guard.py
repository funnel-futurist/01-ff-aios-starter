"""The template's own test suite must not depend on the repository's name.

`install-contract.yml` runs the `tests` job only in the template repository. It used to compare
`github.repository` with the literal name, so a rename would have skipped the job, and GitHub counts
a skipped required job as success: every pull request would pass with no suite run. The guard now
matches the stable repository ID, which a rename doesn't change. This test keeps any literal-name
comparison out of every workflow's `if:` and pins the tests job to the template's ID.
"""

import glob
import os
import re
import unittest

import harness

ROOT = harness.REPO_ROOT
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
TEMPLATE_REPOSITORY_ID = "1259992353"
LITERAL_NAME_GUARD = re.compile(r"github\.repository\s*[!=]=\s*['\"][^'\"]+['\"]|['\"][^'\"]+/[^'\"]+['\"]\s*[!=]=\s*github\.repository\b")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def job_block(text, job):
    """The lines of one top-level job, from its key to the next job's key."""
    body = text.split("\n  %s:\n" % job, 1)[1]
    return re.split(r"\n  [A-Za-z0-9_-]+:\n", "\n" + body, maxsplit=1)[0]


def literal_name_guards(text):
    """Every `if:` line that compares github.repository with a literal owner/name string."""
    return [line.strip() for line in text.splitlines()
            if re.match(r"\s*if:", line) and LITERAL_NAME_GUARD.search(line)]


class WorkflowRepositoryGuard(unittest.TestCase):

    def test_no_workflow_guards_on_a_literal_repository_name(self):
        found = {}
        for path in sorted(glob.glob(os.path.join(WORKFLOWS, "*.yml"))):
            hits = literal_name_guards(read(path))
            if hits:
                found[os.path.basename(path)] = hits
        self.assertEqual(found, {})

    def test_the_tests_job_is_guarded_by_the_template_repository_id(self):
        block = job_block(read(os.path.join(WORKFLOWS, "install-contract.yml")), "tests")
        guards = re.findall(r"^    if:\s*(.+)$", block, re.M)
        self.assertEqual(len(guards), 1, "the tests job needs exactly one job-level if:")
        self.assertIn("github.repository_id == '%s'" % TEMPLATE_REPOSITORY_ID, guards[0])
        self.assertIn("github.event_name != 'pull_request_review'", guards[0])

    def test_the_check_catches_the_old_guard_and_spares_context_comparisons(self):
        old = "    if: github.repository == 'funnel-futurist/ff-aios-starter' && github.event_name != 'pull_request_review'"
        self.assertEqual(len(literal_name_guards(old)), 1)
        flipped = "    if: 'funnel-futurist/ff-aios-starter' == github.repository"
        self.assertEqual(len(literal_name_guards(flipped)), 1)
        context = "    if: github.event.pull_request.head.repo.full_name == github.repository"
        self.assertEqual(literal_name_guards(context), [])
        by_id = "    if: github.repository_id == '1259992353'"
        self.assertEqual(literal_name_guards(by_id), [])


if __name__ == "__main__":
    unittest.main()
