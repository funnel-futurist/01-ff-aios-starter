"""DW-705: `aios.py phase unlock`. No test touches the network: the HTTP opener is injected.
Keys and payloads are synthetic."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error

import harness

sys.path.insert(0, harness.AIOS_DIR)

from aioslib import phase_unlock as pu  # noqa: E402
from aioslib.util import Refusal  # noqa: E402

KEY = "test-key-aaaaaaaaaaaaaaaaaaaaaaaa"
URL = "https://example.test/functions/v1/phase-unlock"


class Res(object):
    def __init__(self, status, body):
        self.status, self._b = status, json.dumps(body).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_returning(status, body, seen=None):
    def op(req, timeout=None):
        if seen is not None:
            seen.append(req)
        if status >= 400:
            raise urllib.error.HTTPError(req.full_url, status, "x", {}, io.BytesIO(json.dumps(body).encode()))
        return Res(status, body)
    return op


class PhaseUnlock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        subprocess.run(["git", "init", "-q", self.root], check=True)
        self.env = {pu.KEY_ENV: KEY, pu.URL_ENV: URL}

    def test_delivered_saves_only_that_phase_locally_and_never_prints_key_or_payload(self):
        seen = []
        body = {"result": "delivered", "phase_key": "phase_2", "version": "t1", "payload": {"prompts": ["P2 synthetic"]}}
        code, msg = pu.unlock(self.root, "phase_2", self.env, opener_returning(200, body, seen))
        self.assertEqual(code, 0)
        saved = json.load(open(os.path.join(self.root, ".aios", "phases", "phase_2", "payload.json")))
        self.assertEqual(saved["payload"], {"prompts": ["P2 synthetic"]})
        self.assertNotIn(KEY, msg)
        self.assertNotIn("P2 synthetic", msg)
        self.assertEqual(seen[0].get_header("X-license-key"), KEY)
        self.assertEqual(json.loads(seen[0].data), {"phase": "phase_2"})

    def test_locked_phase_is_refused_with_what_is_missing_and_nothing_saved(self):
        body = {"result": "locked", "needs": {"previous_phase_complete": False, "payment_cleared": False}}
        code, msg = pu.unlock(self.root, "phase_3", self.env, opener_returning(403, body))
        self.assertEqual(code, pu.EXIT_REFUSED)
        self.assertIn("not unlocked", msg)
        self.assertIn("previous phase", msg)
        self.assertIn("payment", msg)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".aios", "phases")))

    def test_revoked_and_unknown_keys_get_clear_messages(self):
        code, msg = pu.unlock(self.root, "phase_1", self.env, opener_returning(403, {"result": "revoked"}))
        self.assertEqual(code, pu.EXIT_REFUSED)
        self.assertIn("revoked", msg)
        code, msg = pu.unlock(self.root, "phase_1", self.env, opener_returning(401, {"result": "unknown_key"}))
        self.assertIn("not recognised", msg)
        code, msg = pu.unlock(self.root, "phase_1", self.env, opener_returning(429, {"result": "rate_limited"}))
        self.assertIn("hour", msg)

    def test_missing_key_is_a_clear_refusal(self):
        with self.assertRaises(Refusal) as cm:
            pu.unlock(self.root, "phase_1", {pu.URL_ENV: URL}, opener_returning(200, {}))
        self.assertIn("No license key", cm.exception.message)

    def test_key_file_is_used_but_refused_if_tracked_by_git(self):
        os.makedirs(os.path.join(self.root, ".aios"))
        with open(os.path.join(self.root, pu.KEY_FILE), "w") as fh:
            fh.write(KEY + "\n")
        env = {pu.URL_ENV: URL}
        code, _ = pu.unlock(self.root, "phase_1", env, opener_returning(403, {"result": "locked"}))
        self.assertEqual(code, pu.EXIT_REFUSED)
        subprocess.run(["git", "-C", self.root, "add", "-f", pu.KEY_FILE], check=True)
        with self.assertRaises(Refusal) as cm:
            pu.unlock(self.root, "phase_1", env, opener_returning(200, {}))
        self.assertIn("tracked by git", cm.exception.message)

    def test_answer_for_another_phase_is_not_saved(self):
        body = {"result": "delivered", "phase_key": "phase_3", "payload": {"x": 1}}
        with self.assertRaises(Refusal):
            pu.unlock(self.root, "phase_2", self.env, opener_returning(200, body))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".aios", "phases")))

    def test_bad_inputs_and_non_https_url_are_refused_before_any_request(self):
        seen = []
        for phase, env in (("Phase 2!", self.env), ("phase_2", {pu.KEY_ENV: "short", pu.URL_ENV: URL}),
                           ("phase_2", {pu.KEY_ENV: KEY, pu.URL_ENV: "http://example.test"}),
                           ("phase_2", {pu.KEY_ENV: KEY})):
            with self.assertRaises(Refusal):
                pu.unlock(self.root, phase, env, opener_returning(200, {}, seen))
        self.assertEqual(seen, [])

    def test_unreachable_service_is_a_clear_refusal(self):
        def down(req, timeout=None):
            raise urllib.error.URLError("down")
        with self.assertRaises(Refusal) as cm:
            pu.unlock(self.root, "phase_1", self.env, down)
        self.assertIn("Could not reach", cm.exception.message)

    def test_server_unavailable_and_non_object_answers_are_clear(self):
        code, msg = pu.unlock(self.root, "phase_1", self.env, opener_returning(503, {"result": "unavailable"}))
        self.assertEqual(code, pu.EXIT_REFUSED)
        self.assertIn("temporarily unavailable", msg)
        with self.assertRaises(Refusal):
            pu.unlock(self.root, "phase_1", self.env, opener_returning(200, ["not", "an", "object"]))

    def test_redirects_are_never_followed(self):
        import urllib.request
        handler = pu._NoRedirect()
        req = urllib.request.Request(URL, headers={"x-license-key": KEY})
        self.assertIsNone(handler.redirect_request(req, None, 302, "Found", {}, "http://elsewhere.test/"))

    def test_symlinked_phases_folder_is_refused(self):
        os.makedirs(os.path.join(self.root, ".aios"))
        elsewhere = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(elsewhere, ignore_errors=True))
        os.symlink(elsewhere, os.path.join(self.root, ".aios", "phases"))
        body = {"result": "delivered", "phase_key": "phase_1", "payload": {}}
        with self.assertRaises(Refusal):
            pu.unlock(self.root, "phase_1", self.env, opener_returning(200, body))
        self.assertEqual(os.listdir(elsewhere), [])

    def test_gitignore_keeps_key_and_phases_local(self):
        repo = os.path.dirname(os.path.dirname(harness.AIOS_DIR))
        text = open(os.path.join(repo, ".gitignore")).read()
        self.assertIn(".aios/license_key", text)
        self.assertIn(".aios/phases/", text)


if __name__ == "__main__":
    unittest.main()
