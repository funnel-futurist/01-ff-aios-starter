"""The Starter's Core Bridge client speaks contract 0.3 and still serves 0.1.5 instances.

0.3 keeps an output and its receipt only when every hash in the receipt agrees, never overwrites a
file, and keeps nothing when the service refuses the organization. An instance.json written for
0.1.5 (no outputs_dir or receipts_dir) keeps working for both contracts. Fixtures are synthetic.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import harness

CLIENT = os.path.join(harness.REPO_ROOT, ".aios", "core_bridge", "core_call.py")
MANIFEST = os.path.join(harness.REPO_ROOT, ".aios", "core_bridge", "manifest.json")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def artifact_response(org="fixture-org", inputs=None, request_id="req_v03fixture01", tamper=None):
    """A 0.3 success the way the service shapes it, with every hash right unless `tamper` names one."""
    inputs = {} if inputs is None else inputs
    content = "# Fictional deliverable\n\nSynthetic text for the client test.\n"
    data = content.encode("utf-8")
    result = {"kind": "artifact", "media_type": "text/markdown", "encoding": "utf-8", "filename": "deliverable.md",
              "content": content, "sha256": sha(data), "bytes": len(data)}
    provenance = {"capability": "example.echo-artifact@1", "method_fingerprint": "f" * 64, "service_version": "0.3.0"}
    receipt = {"request_id": request_id, "org": org, "person": "fixture-person",
               "result_sha256": sha(data), "inputs_sha256": sha(canonical(inputs)),
               "provenance_sha256": sha(canonical(provenance))}
    if tamper:
        receipt[tamper] = "0" * 64
    return {"ok": True, "contract": "0.3", "request_id": request_id, "result": result, "receipt": receipt,
            "provenance": provenance}


class Service(BaseHTTPRequestHandler):
    response = None
    status = 200
    seen = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        type(self).seen.append(json.loads(self.rfile.read(length)))
        body = json.dumps(type(self).response).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class CoreBridgeV03(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        Service.seen, Service.status, Service.response = [], 200, artifact_response()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Service)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        # Exactly the fields a 0.1.5 instance.json has: no outputs_dir, no receipts_dir.
        self.config = os.path.join(self.tmp.name, "instance.json")
        with open(self.config, "w") as fh:
            json.dump({"org": "fixture-org", "endpoint": "http://127.0.0.1:%d" % self.httpd.server_port,
                       "key_env": "FF_CORE_KEY", "default_repo": "fixture-org/instance", "reports_dir": "reports"}, fh)

    def call(self, *args):
        env = dict(os.environ, FF_CORE_KEY="fixture-key")
        return subprocess.run([sys.executable, CLIENT, *args, "--instance", self.config],
                              text=True, capture_output=True, env=env)

    def saved_files(self):
        out = []
        for root, _, files in os.walk(self.tmp.name):
            out.extend(os.path.relpath(os.path.join(root, f), self.tmp.name) for f in files)
        return sorted(f for f in out if f != "instance.json")

    def test_hash_verified_save_keeps_the_artifact_and_its_receipt(self):
        result = self.call("example.echo-artifact@1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out["contract"], "0.3")
        with open(out["saved"], "rb") as fh:
            self.assertEqual(sha(fh.read()), out["sha256"])
        self.assertEqual(out["sha256"], Service.response["receipt"]["result_sha256"])
        with open(out["receipt"], encoding="utf-8") as fh:
            kept = json.load(fh)
        self.assertEqual(kept["receipt"]["request_id"], "req_v03fixture01")
        self.assertEqual(self.saved_files(), ["outputs/req_v03fixture01-deliverable.md", "receipts/req_v03fixture01.json"])
        self.assertNotIn("Fictional deliverable", result.stdout)
        self.assertEqual(Service.seen[0]["contract"], "0.3")
        self.assertEqual(Service.seen[0]["org"], "fixture-org")

    def test_any_hash_that_disagrees_keeps_nothing(self):
        for field in ("result_sha256", "inputs_sha256", "provenance_sha256"):
            with self.subTest(field=field):
                Service.response = artifact_response(tamper=field, request_id="req_tamper%s" % field[:3])
                result = self.call("example.echo-artifact@1")
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertEqual(json.loads(result.stdout)["error"]["code"], "INVALID_SERVICE_RESPONSE")
                self.assertEqual(self.saved_files(), [])

    def test_a_saved_file_is_never_overwritten(self):
        self.assertEqual(self.call("example.echo-artifact@1").returncode, 0)
        before = self.saved_files()
        again = self.call("example.echo-artifact@1")
        self.assertEqual(again.returncode, 3, again.stdout)
        self.assertIn("nothing was overwritten", json.loads(again.stdout)["error"]["message"])
        self.assertEqual(self.saved_files(), before)

    def test_wrong_organization_is_refused_and_nothing_is_kept(self):
        Service.status = 403
        Service.response = {"ok": False, "error": {"code": "ORG_MISMATCH", "message": "this key belongs to a different organization"}}
        for capability in ("example.echo-artifact@1", "repository-health"):
            with self.subTest(capability=capability):
                result = self.call(capability)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(json.loads(result.stdout)["error"]["code"], "ORG_MISMATCH")
                self.assertEqual(self.saved_files(), [])
        self.assertTrue(all(body["org"] == "fixture-org" for body in Service.seen))

    def test_a_0_1_5_instance_still_runs_repository_health_as_before(self):
        Service.response = {"ok": True, "request_id": "req_0123456789ab",
                            "report": {"totals": {"skill_objects": 1}, "findings": []},
                            "provenance": {"resolved_commit": "a" * 40}}
        result = self.call("repository-health")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(self.saved_files(), ["reports/repository-health-req_0123456789ab.json"])
        with open(out["saved"], "rb") as fh:
            self.assertEqual(out["report_sha256"], sha(fh.read()))
        self.assertNotIn("contract", Service.seen[0])
        self.assertEqual(Service.seen[0]["repo"], "fixture-org/instance")
        self.assertEqual(Service.seen[0]["ref"], "main")

    def test_a_key_shaped_value_in_instance_json_is_refused_before_any_request(self):
        config = json.load(open(self.config))
        config["note"] = "ffcb_0123abcd_" + "x" * 20
        json.dump(config, open(self.config, "w"))
        for capability in ("repository-health", "example.echo-artifact@1"):
            with self.subTest(capability=capability):
                result = self.call(capability)
                self.assertEqual(result.returncode, 4, result.stdout)
                self.assertEqual(json.loads(result.stdout)["error"]["code"], "MISSING_CREDENTIAL")
        self.assertEqual(Service.seen, [])


class InstalledVersion(unittest.TestCase):
    def test_manifest_names_the_0_3_source_and_the_example_shows_the_new_folders(self):
        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest["version"], "0.3")
        self.assertEqual(manifest["source"]["repository"], "funnel-futurist/01-ff-aios")
        with open(os.path.join(os.path.dirname(CLIENT), "instance.example.json"), encoding="utf-8") as fh:
            example = json.load(fh)
        self.assertEqual((example.get("outputs_dir"), example.get("receipts_dir")), ("outputs", "receipts"))

    def test_new_output_folders_are_ignored_like_reports(self):
        with open(os.path.join(harness.REPO_ROOT, ".aios", ".gitignore"), encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        for folder in ("core_bridge/reports/", "core_bridge/outputs/", "core_bridge/receipts/"):
            self.assertIn(folder, lines)


if __name__ == "__main__":
    unittest.main()
