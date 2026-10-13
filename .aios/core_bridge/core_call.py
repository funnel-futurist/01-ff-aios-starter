#!/usr/bin/env python3
"""Thin client an FF instance (or a client instance) holds to call an FF Core
capability. It contains no method: it sends a request and saves the report.

    python3 core_call.py repository-health [--repo owner/name] [--ref main]

Reads instance.json next to this file:
    {"org": "...", "endpoint": "http://127.0.0.1:8787", "key_env": "FF_CORE_KEY",
     "default_repo": "owner/name", "reports_dir": "reports"}
The key comes from the environment variable named by key_env, never from a file in git.
Exit codes: 0 report saved, 2 refused by the service, 3 transport/response failure,
4 local configuration or credential failure.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class ClientError(Exception):
    def __init__(self, code, message, exit_code):
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


def _read_json_response(response):
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ClientError("RESPONSE_TOO_LARGE", "the service response exceeded 5 MiB", 3)
    try:
        out = json.loads(raw or b"{}")
    except (TypeError, ValueError):
        raise ClientError("INVALID_SERVICE_RESPONSE", "the service returned invalid JSON", 3)
    if not isinstance(out, dict):
        raise ClientError("INVALID_SERVICE_RESPONSE", "the service response was not an object", 3)
    return out


def _load_instance(path):
    try:
        with open(path, encoding="utf-8") as fh:
            inst = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ClientError("INVALID_INSTANCE", "the instance configuration could not be read: %s" % exc, 4)
    if not isinstance(inst, dict):
        raise ClientError("INVALID_INSTANCE", "the instance configuration must be an object", 4)
    for field in ("org", "endpoint", "key_env", "default_repo"):
        if not isinstance(inst.get(field), str) or not inst[field].strip():
            raise ClientError("INVALID_INSTANCE", "%s must be a non-empty string" % field, 4)
    if not ENV_RE.fullmatch(inst["key_env"]):
        raise ClientError("INVALID_INSTANCE", "key_env must name an uppercase environment variable", 4)
    parsed = urllib.parse.urlsplit(inst["endpoint"])
    loopback = parsed.hostname in ("127.0.0.1", "localhost", "::1")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise ClientError("INVALID_INSTANCE", "endpoint must use HTTPS (HTTP is allowed only on loopback)", 4)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ClientError("INVALID_INSTANCE", "endpoint may not contain credentials, a query, or a fragment", 4)
    reports_dir = inst.get("reports_dir", "reports")
    if not isinstance(reports_dir, str) or not reports_dir or os.path.isabs(reports_dir):
        raise ClientError("INVALID_INSTANCE", "reports_dir must be a relative path", 4)
    root = os.path.realpath(os.path.dirname(os.path.abspath(path)))
    report_root = os.path.realpath(os.path.join(root, reports_dir))
    if os.path.commonpath((root, report_root)) != root:
        raise ClientError("INVALID_INSTANCE", "reports_dir must stay inside the instance", 4)
    inst["report_root"] = report_root
    return inst


def _write_report(root, capability, request_id, report):
    if not SAFE_NAME_RE.fullmatch(request_id):
        raise ClientError("INVALID_SERVICE_RESPONSE", "the service returned an invalid request id", 3)
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "%s-%s.json" % (capability, request_id))
    fd, pending = tempfile.mkstemp(prefix=".core-report-", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
        os.replace(pending, path)
    except Exception:
        try:
            os.unlink(pending)
        except OSError:
            pass
        raise
    return path


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("capability")
    p.add_argument("--repo")
    p.add_argument("--ref", default="main")
    p.add_argument("--instance", default=os.path.join(HERE, "instance.json"))
    a = p.parse_args(argv)
    try:
        if not CAPABILITY_RE.fullmatch(a.capability):
            raise ClientError("INVALID_CAPABILITY", "capability must be a lowercase hyphenated name", 4)
        inst = _load_instance(a.instance)
        key = os.environ.get(inst["key_env"], "")
        if not key:
            raise ClientError("MISSING_CREDENTIAL", "%s is not set" % inst["key_env"], 4)
        body = json.dumps({"org": inst["org"], "capability": a.capability,
                           "repo": a.repo or inst["default_repo"], "ref": a.ref}).encode()
        req = urllib.request.Request(inst["endpoint"].rstrip("/") + "/v1/invoke", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=300) as resp:
            out = _read_json_response(resp)
    except urllib.error.HTTPError as e:
        try:
            out = _read_json_response(e)
        except ClientError as error:
            print(json.dumps({"ok": False, "error": {"code": error.code, "message": error.message}}))
            return error.exit_code
    except urllib.error.URLError as e:
        print(json.dumps({"ok": False, "error": {"code": "SERVICE_UNREACHABLE", "message": str(e.reason)}}))
        return 3
    except ClientError as e:
        print(json.dumps({"ok": False, "error": {"code": e.code, "message": e.message}}))
        return e.exit_code
    if not out.get("ok"):
        print(json.dumps(out))
        return 2
    try:
        totals = out["report"]["totals"]
        findings = len(out["report"]["findings"])
        resolved_commit = out["provenance"]["resolved_commit"]
        path = _write_report(inst["report_root"], a.capability, out.get("request_id", ""), out)
    except (ClientError, KeyError, TypeError) as exc:
        if isinstance(exc, ClientError):
            error = exc
        else:
            error = ClientError("INVALID_SERVICE_RESPONSE", "the successful response omitted required fields", 3)
        print(json.dumps({"ok": False, "error": {"code": error.code, "message": error.message}}))
        return error.exit_code
    with open(path, "rb") as fh:
        report_sha256 = hashlib.sha256(fh.read()).hexdigest()
    print(json.dumps({"ok": True, "saved": path, "request_id": out["request_id"],
                      "totals": totals, "findings": findings,
                      "resolved_commit": resolved_commit,
                      "report_sha256": report_sha256}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
