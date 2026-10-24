"""The env_keys skill's presence check prints registry names and counts, never anything read from a .env.

The check runs on a person's real .env, so it must not be able to echo a value. A multi-line value (a
certificate or a JSON key) can hold continuation lines shaped like NAME=, which is how a sed-based
"names only" listing leaked value content. These tests run the exact block shipped in SKILL.md against a
synthetic .env whose values are all invented, in every shell the person might paste it into.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest

import harness

SKILL = os.path.join(harness.REPO_ROOT, ".claude", "skills", "env_keys", "SKILL.md")

# Every value below is invented. The multi-line values carry continuation lines shaped like NAME=,
# one of them base64-like, which a line-oriented name listing would print.
SYNTHETIC_ENV = """# synthetic file: every value is invented
export OPENAI_API_KEY=invented-openai-value
ANTHROPIC_API_KEY = invented-anthropic-value
GOOGLE_CLIENT_SECRET=
SERVICE_ACCOUNT_JSON="{
LEAKY_CONTINUATION=invented-inside-json
}"
PEM_BLOCK="-----BEGIN INVENTED BLOCK-----
QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0123=
-----END INVENTED BLOCK-----"
EXTRA_TOOL_KEY=invented-extra
"""
CHECKED = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_CLIENT_SECRET", "FF_CORE_KEY"]
EXPECTED = [
    "ANTHROPIC_API_KEY set",
    "OPENAI_API_KEY set",
    "GOOGLE_CLIENT_SECRET empty",
    "FF_CORE_KEY missing",
    # 8 assignment-shaped lines, 3 of them registry names; the other 5 include the 2 continuation lines.
    "other lines that look like assignments: 5",
]
# Anything from the file other than the checked names must never reach the output.
FORBIDDEN = ["invented", "QUJD", "LEAKY_CONTINUATION", "SERVICE_ACCOUNT_JSON", "PEM_BLOCK", "EXTRA_TOOL_KEY"]


def shipped_block():
    with open(SKILL, encoding="utf-8") as fh:
        text = fh.read()
    section = text[text.index("### G-3"):]
    match = re.search(r"```sh\n(.*?)```", section, re.S)
    if not match:
        raise AssertionError("SKILL.md G-3 has no sh block")
    return match.group(1)


def with_names(block, names):
    out, n = re.subn(r"(?m)^(\s*for n in )[A-Za-z0-9_ ]+(; do)$", lambda m: m.group(1) + " ".join(names) + m.group(2), block)
    if n != 1:
        raise AssertionError("expected exactly one `for n in ...; do` line in the G-3 block")
    return out


def shells():
    return [s for s in ("sh", "bash", "zsh") if shutil.which(s)]


class PresenceCheck(unittest.TestCase):
    def run_in(self, shell, folder, script):
        return subprocess.run([shell, "-c", script], cwd=folder, capture_output=True, text=True, timeout=30)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="env-keys-")
        self.folder = self.tmp.name
        with open(os.path.join(self.folder, ".env"), "w", encoding="utf-8") as fh:
            fh.write(SYNTHETIC_ENV)
        self.script = with_names(shipped_block(), CHECKED)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_old_sed_listing_leaks_on_this_file(self):
        # Control: the synthetic file really does exercise the leak, so the checks below can fail.
        old = subprocess.run(["sed", "-n", r"s/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p", ".env"],
                             cwd=self.folder, capture_output=True, text=True)
        self.assertIn("QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0123", old.stdout)
        self.assertIn("LEAKY_CONTINUATION", old.stdout)

    def test_reports_status_and_a_count_in_every_available_shell(self):
        self.assertIn("sh", shells())
        for shell in shells():
            with self.subTest(shell=shell):
                got = self.run_in(shell, self.folder, self.script)
                self.assertEqual(got.returncode, 0, got.stderr)
                self.assertEqual(got.stderr, "")
                self.assertEqual(got.stdout.splitlines(), EXPECTED)

    def test_never_prints_anything_read_from_the_file(self):
        for shell in shells():
            with self.subTest(shell=shell):
                got = self.run_in(shell, self.folder, self.script)
                for token in FORBIDDEN:
                    self.assertNotIn(token, got.stdout + got.stderr)

    def test_a_folder_without_a_dotenv_says_so(self):
        empty = tempfile.TemporaryDirectory(prefix="env-keys-empty-")
        self.addCleanup(empty.cleanup)
        for shell in shells():
            with self.subTest(shell=shell):
                got = self.run_in(shell, empty.name, self.script)
                self.assertEqual(got.stdout.splitlines(), ["no .env in this folder"])


if __name__ == "__main__":
    unittest.main()
