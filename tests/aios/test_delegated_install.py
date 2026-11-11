"""Delegated install (03a #259 scope 5): a founder's grant lets one real person install one release, once.

Identity comes from the stub `gh` on PATH, the same path the founder gate uses. There is no override to test.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import harness
from harness import Sandbox

sys.path.insert(0, harness.AIOS_DIR)

from aioslib import delegation, roles, util  # noqa: E402
from aioslib.util import Refusal  # noqa: E402

NOW = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)


class DelegatedInstall(Sandbox):
    def setUp(self):
        Sandbox.setUp(self)
        self.man = harness.approve(harness.build_manifest(self.source, self.rev, "1.0.0"))
        self.policy = None
        for path, _mode, data in util.read_tree(self.source, self.man["created_from"]["git_rev"]):
            if path == roles.POLICY_PATH.replace(os.sep, "/"):
                self.policy = json.loads(data.decode("utf-8"))
        self.assertIsNotNone(self.policy)
        self.cfg = harness.config()
        self.grant = {
            "grant_id": "dg-acme-0001", "delegate": "ff-installer", "granted_by": "acme-founder",
            "scope": "install", "target_repository": "acme/acme-aios",
            "release_id": self.man["release_id"], "git_rev": self.man["created_from"]["git_rev"],
            "granted_at": "2026-11-09T12:00:00Z", "expires_at": "2026-11-16T12:00:00Z", "revoked_at": None,
        }
        self.cfg["install_delegations"] = [self.grant]

    def refused(self, login="ff-installer", grant=None, now=NOW):
        with self.assertRaises(Refusal) as ctx:
            delegation.check_grant(self.policy, self.cfg, self.man, grant or self.grant, login, now=now)
        self.assertEqual(ctx.exception.code, util.EXIT_ROLE)
        return ctx.exception.message

    def with_(self, **changes):
        return dict(self.grant, **changes)

    def test_the_named_delegate_may_install_that_release(self):
        self.assertEqual(delegation.check_grant(self.policy, self.cfg, self.man, self.grant, "ff-installer", now=NOW),
                         "acme-founder")

    def test_real_actor_is_bound(self):
        self.assertIn("not acme-va", self.refused(login="acme-va"))
        self.assertIn("unknown person", self.refused(login=None))

    def test_no_self_grant_and_granter_must_be_able_to_install(self):
        self.assertIn("oneself", self.refused(login="acme-founder", grant=self.with_(delegate="acme-founder")))
        self.assertIn("cannot delegate", self.refused(grant=self.with_(granted_by="acme-va")))       # operator
        self.assertIn("cannot delegate", self.refused(grant=self.with_(granted_by="ff-installer2")))  # stranger

    def test_target_release_and_revision_are_bound(self):
        self.assertIn("this config is for", self.refused(grant=self.with_(target_repository="other/repo")))
        self.assertIn("not starter", self.refused(grant=self.with_(release_id="starter-9.9.9")))
        self.assertIn("revision", self.refused(grant=self.with_(git_rev="0" * 40)))
        self.assertIn("revision", self.refused(grant=self.with_(git_rev="main")))

    def test_only_install_scope_and_no_wider_authority(self):
        for scope in ("upgrade", "governance", "install,upgrade", "*"):
            self.assertIn("only 'install'", self.refused(grant=self.with_(scope=scope)))
        # The delegate still has no lifecycle role of its own.
        self.be("ff-installer")
        for action in ("install", "upgrade", "rollback", "adopt", "governance"):
            with self.assertRaises(Refusal):
                roles.require_lifecycle(self.policy, self.cfg, action)

    def test_revocation_and_expiry(self):
        self.assertIn("revoked", self.refused(grant=self.with_(revoked_at="2026-11-10T00:00:00Z")))
        self.assertIn("expired", self.refused(now=datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc)))
        self.assertIn("not valid yet", self.refused(now=datetime(2026, 11, 8, 0, 0, 0, tzinfo=timezone.utc)))
        self.assertIn("within 30 days", self.refused(grant=self.with_(expires_at="2027-01-01T00:00:00Z")))
        self.assertIn("within 30 days", self.refused(grant=self.with_(granted_at="2026-11-01T00:00:00Z",
                                                                      expires_at="2026-12-01T23:00:00Z")))
        self.assertIn("ISO-8601", self.refused(grant=self.with_(expires_at="next week")))

    def test_missing_fields_and_unknown_or_duplicate_grant(self):
        self.assertIn("missing", self.refused(grant=self.with_(granted_by="")))
        with self.assertRaises(Refusal):
            delegation.find(self.cfg, "dg-nope-0000")
        with self.assertRaises(Refusal):
            delegation.find(self.cfg, "../etc")
        self.cfg["install_delegations"].append(dict(self.grant))
        with self.assertRaises(Refusal):
            delegation.find(self.cfg, "dg-acme-0001")

    def _cli_install(self, grant_id):
        rel = self.write_json("release.json", self.man)
        cfg = self.write_json("config.json", self.cfg)
        return self.cli("install", "--release", rel, "--target", self.target, "--config", cfg,
                        "--repo", self.source, "--delegation", grant_id)

    def test_cli_end_to_end_as_delegate(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        self.grant.update(granted_at=(now - timedelta(days=1)).strftime(fmt),
                          expires_at=(now + timedelta(days=7)).strftime(fmt))
        self.be("ff-installer")
        code, out, err = self._cli_install("dg-acme-0001")
        self.assertEqual(code, 0, out + err)
        self.assertIn("by:       ff-installer (delegate of acme-founder, grant dg-acme-0001)", out)

    def test_cli_refuses_wrong_actor_and_revoked_grant(self):
        self.be("acme-va")
        code, out, err = self._cli_install("dg-acme-0001")
        self.assertEqual(code, util.EXIT_ROLE, out + err)
        self.assertFalse(os.path.exists(os.path.join(self.target, ".aios", "install.json")))
        self.be("ff-installer")
        self.grant["revoked_at"] = "2026-11-09T13:00:00Z"
        code, out, err = self._cli_install("dg-acme-0001")
        self.assertEqual(code, util.EXIT_ROLE, out + err)
        self.assertIn("revoked", out + err)

    def test_no_identity_override_exists(self):
        src = open(os.path.join(harness.AIOS_DIR, "aioslib", "delegation.py")).read()
        code = src.split('"""', 2)[2]          # skip the module docstring, which names what is absent
        for word in ("as_founder", "as-founder", "environ", "getenv"):
            self.assertNotIn(word, code)
