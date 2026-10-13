"""The Starter ships only the bounded Core Bridge client, never the private method."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import harness

sys.path.insert(0, harness.AIOS_DIR)

from aioslib import release, util  # noqa: E402

CLIENT = os.path.join(harness.REPO_ROOT, ".aios", "core_bridge", "core_call.py")
MANIFEST = os.path.join(harness.REPO_ROOT, ".aios", "core_bridge", "manifest.json")


class Handler(BaseHTTPRequestHandler):
    response = None
    status = 200
    seen = []
    redirect_to = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        type(self).seen.append({
            "method": "POST",
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "body": json.loads(self.rfile.read(length)),
        })
        if type(self).redirect_to:
            self.send_response(302)
            self.send_header("Location", type(self).redirect_to)
            self.end_headers()
            return
        body = json.dumps(type(self).response).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).seen.append({
            "method": "GET",
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "body": None,
        })
        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class CoreBridgeClient(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        Handler.seen = []
        Handler.status = 200
        Handler.redirect_to = None
        Handler.response = {
            "ok": True,
            "request_id": "req_0123456789ab",
            "report": {"totals": {"skill_objects": 1}, "findings": []},
            "provenance": {"resolved_commit": "a" * 40},
        }
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.config = os.path.join(self.tmp.name, "instance.json")
        with open(self.config, "w") as fh:
            json.dump({
                "org": "fixture-org",
                "endpoint": "http://127.0.0.1:%d" % self.httpd.server_port,
                "key_env": "FF_CORE_KEY",
                "default_repo": "fixture-org/instance",
                "reports_dir": "reports",
            }, fh)

    def call(self, key="fixture-key"):
        env = dict(os.environ)
        if key is None:
            env.pop("FF_CORE_KEY", None)
        else:
            env["FF_CORE_KEY"] = key
        return subprocess.run(
            [sys.executable, CLIENT, "repository-health", "--instance", self.config],
            text=True, capture_output=True, env=env,
        )

    def test_entitled_call_saves_a_client_owned_report(self):
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["ok"])
        self.assertTrue(os.path.isfile(output["saved"]))
        self.assertTrue(os.path.realpath(output["saved"]).startswith(os.path.realpath(self.tmp.name) + os.sep))
        with open(output["saved"], "rb") as fh:
            self.assertEqual(output["report_sha256"], hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(Handler.seen[0]["authorization"], "Bearer fixture-key")
        self.assertEqual(Handler.seen[0]["body"]["org"], "fixture-org")

    def test_service_denial_is_preserved_and_writes_no_report(self):
        Handler.status = 403
        Handler.response = {"ok": False, "error": {"code": "NOT_ENTITLED", "message": "not entitled"}}
        result = self.call()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "NOT_ENTITLED")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "reports")))

    def test_missing_key_is_a_local_failure_and_makes_no_request(self):
        result = self.call(None)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "MISSING_CREDENTIAL")
        self.assertEqual(Handler.seen, [])

    def test_redirect_is_refused_without_forwarding_the_bearer_credential(self):
        Handler.redirect_to = "/credential-sink"
        result = self.call()
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "SERVICE_REDIRECT_REFUSED")
        self.assertEqual(len(Handler.seen), 1)
        self.assertEqual(Handler.seen[0]["method"], "POST")
        self.assertEqual(Handler.seen[0]["path"], "/v1/invoke")
        self.assertEqual(Handler.seen[0]["authorization"], "Bearer fixture-key")

    def test_plain_http_requires_a_literal_loopback_ip_not_a_hostname(self):
        config = json.loads(Path(self.config).read_text(encoding="utf-8"))
        config["endpoint"] = "http://localhost:%d" % self.httpd.server_port
        Path(self.config).write_text(json.dumps(config), encoding="utf-8")
        result = self.call()
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "INVALID_INSTANCE")
        self.assertEqual(Handler.seen, [])

    def test_https_endpoint_requires_a_hostname(self):
        config = json.loads(Path(self.config).read_text(encoding="utf-8"))
        config["endpoint"] = "https://"
        Path(self.config).write_text(json.dumps(config), encoding="utf-8")
        result = self.call()
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "INVALID_INSTANCE")
        self.assertEqual(Handler.seen, [])

    def test_socket_timeout_is_a_structured_transport_failure(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("starter_core_call_timeout", CLIENT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        opener = mock.Mock()
        opener.open.side_effect = TimeoutError("timed out while reading")
        with mock.patch.object(module.urllib.request, "build_opener", return_value=opener):
            with mock.patch.dict(os.environ, {"FF_CORE_KEY": "fixture-key"}, clear=False):
                output = io.StringIO()
                with mock.patch("sys.stdout", new=output):
                    code = module.main(["repository-health", "--instance", self.config])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "SERVICE_UNREACHABLE")

    def test_report_write_failure_is_a_structured_local_failure(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("starter_core_call_write_failure", CLIENT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module, "_write_report", side_effect=OSError("disk full /private/path")):
            with mock.patch.dict(os.environ, {"FF_CORE_KEY": "fixture-key"}, clear=False):
                output = io.StringIO()
                with mock.patch("sys.stdout", new=output):
                    code = module.main(["repository-health", "--instance", self.config])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 4)
        self.assertEqual(result["error"]["code"], "REPORT_WRITE_FAILED")
        self.assertNotIn("private/path", result["error"]["message"])

    def test_report_hash_read_failure_is_a_structured_local_failure(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("starter_core_call_hash_failure", CLIENT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        missing = os.path.join(self.tmp.name, "report-disappeared.json")
        with mock.patch.object(module, "_write_report", return_value=missing):
            with mock.patch.dict(os.environ, {"FF_CORE_KEY": "fixture-key"}, clear=False):
                output = io.StringIO()
                with mock.patch("sys.stdout", new=output):
                    code = module.main(["repository-health", "--instance", self.config])
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(output.getvalue())["error"]["code"], "REPORT_WRITE_FAILED")


class PackageBoundary(unittest.TestCase):
    def test_client_is_managed_but_instance_configuration_is_client_owned(self):
        spec = util.read_json(os.path.join(harness.REPO_ROOT, "release", "package_spec.json"))
        self.assertEqual(release.classify(spec, ".aios/core_bridge/core_call.py"), "managed")
        self.assertIsNone(release.classify(spec, ".aios/core_bridge/instance.json"))

    def test_optional_credential_is_declared(self):
        refs = util.read_json(os.path.join(harness.REPO_ROOT, "release", "credential_refs.json"))
        row = next(item for item in refs if item["name"] == "FF_CORE_KEY")
        self.assertFalse(row["required"])

    def test_vendored_client_matches_its_source_receipt(self):
        manifest = util.read_json(MANIFEST)
        with open(CLIENT, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(digest, manifest["source"]["sha256"])
        self.assertFalse(manifest["private_method_included"])

    def test_client_rejects_oversized_service_output(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("starter_core_call", CLIENT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(module.ClientError) as caught:
            module._read_json_response(io.BytesIO(b"x" * (module.MAX_RESPONSE_BYTES + 1)))
        self.assertEqual(caught.exception.code, "RESPONSE_TOO_LARGE")

    def test_no_private_bridge_or_method_code_ships_in_the_client_folder(self):
        paths = []
        for root, _, files in os.walk(os.path.dirname(CLIENT)):
            paths.extend(os.path.relpath(os.path.join(root, name), os.path.dirname(CLIENT)) for name in files)
        self.assertNotIn("service/bridge.py", paths)
        self.assertNotIn("service/capabilities/repository_health/checks.py", paths)


if __name__ == "__main__":
    unittest.main()
