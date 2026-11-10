#!/usr/bin/env python3
"""Thin client an FF instance (or a client instance) holds to call an FF Core
capability. It contains no method: it sends a request and saves what comes back.

    python3 core_call.py repository-health [--repo owner/name] [--ref main]            (contract 0.1)
    python3 core_call.py <domain>.<name>@<major> [--inputs FILE] [--repo owner/name [--ref REF]]   (contract 0.3)

Reads instance.json next to this file:
    {"org": "...", "endpoint": "http://127.0.0.1:8787", "key_env": "FF_CORE_KEY",
     "default_repo": "owner/name", "reports_dir": "reports", "outputs_dir": "outputs", "receipts_dir": "receipts"}
default_repo is needed only for a 0.1 call made without --repo; a 0.3 call sends a repo only with --repo.
The key comes from the environment variable named by key_env, never from a file in git. A key-shaped value
anywhere in instance.json is refused.

A 0.1 call saves the whole response under reports_dir, as before. A 0.3 call saves the result under outputs_dir as
<request_id>-<filename> (an artifact's content, or a report's canonical JSON as <request_id>-report.json, so the
file's SHA-256 is the receipt's result_sha256), and the receipt with its provenance under receipts_dir as
<request_id>.json. It keeps nothing unless every hash in the receipt checks out, and it never overwrites a file.
It prints paths and SHA-256s, never the content or the key.
Exit codes: 0 saved, 2 refused by the service, 3 transport/response failure,
4 local configuration or credential failure.
"""
import argparse
import hashlib
import ipaddress
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
MAX_INPUTS_BYTES = 64 * 1024
CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CAPABILITY_V03_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)+@(?:0|[1-9][0-9]{0,3})")
MAX_CAPABILITY_V03 = 96
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
KEY_SHAPE_RE = re.compile(r"ffcb_[0-9a-f]{8}_")
MEDIA_TYPES = ("text/markdown", "text/plain", "text/csv", "application/json")


class ClientError(Exception):
    def __init__(self, code, message, exit_code):
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so a bearer credential is never forwarded."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


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


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _contained(root, inst, field, default):
    value = inst.get(field, default)
    if not isinstance(value, str) or not value or os.path.isabs(value):
        raise ClientError("INVALID_INSTANCE", "%s must be a relative path" % field, 4)
    path = os.path.realpath(os.path.join(root, value))
    if os.path.commonpath((root, path)) != root:
        raise ClientError("INVALID_INSTANCE", "%s must stay inside the instance" % field, 4)
    return path


def _load_instance(path):
    try:
        with open(path, encoding="utf-8") as fh:
            inst = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ClientError("INVALID_INSTANCE", "the instance configuration could not be read: %s" % exc, 4)
    if not isinstance(inst, dict):
        raise ClientError("INVALID_INSTANCE", "the instance configuration must be an object", 4)
    if any(KEY_SHAPE_RE.search(s) for s in _strings(inst)):
        raise ClientError("MISSING_CREDENTIAL", "keys belong in the secret store, not in instance.json", 4)
    for field in ("org", "endpoint", "key_env"):
        if not isinstance(inst.get(field), str) or not inst[field].strip():
            raise ClientError("INVALID_INSTANCE", "%s must be a non-empty string" % field, 4)
    if "default_repo" in inst and (not isinstance(inst["default_repo"], str) or not inst["default_repo"].strip()):
        raise ClientError("INVALID_INSTANCE", "default_repo must be a non-empty string", 4)
    if not ENV_RE.fullmatch(inst["key_env"]):
        raise ClientError("INVALID_INSTANCE", "key_env must name an uppercase environment variable", 4)
    parsed = urllib.parse.urlsplit(inst["endpoint"])
    try:
        loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        loopback = False
    if not parsed.hostname or (parsed.scheme != "https" and not (parsed.scheme == "http" and loopback)):
        raise ClientError(
            "INVALID_INSTANCE",
            "endpoint must use HTTPS (HTTP is allowed only for a literal loopback IP)",
            4,
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ClientError("INVALID_INSTANCE", "endpoint may not contain credentials, a query, or a fragment", 4)
    root = os.path.realpath(os.path.dirname(os.path.abspath(path)))
    inst["report_root"] = _contained(root, inst, "reports_dir", "reports")
    inst["output_root"] = _contained(root, inst, "outputs_dir", "outputs")
    inst["receipt_root"] = _contained(root, inst, "receipts_dir", "receipts")
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


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _read_inputs(path):
    if path is None:
        return {}
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUTS_BYTES + 1)
    except OSError:
        raise ClientError("INVALID_INPUTS_FILE", "the inputs file could not be read", 4)
    if len(raw) > MAX_INPUTS_BYTES:
        raise ClientError("INVALID_INPUTS_FILE", "the inputs file is over 64 KiB", 4)
    try:
        inputs = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        inputs = None
    if not isinstance(inputs, dict):
        raise ClientError("INVALID_INPUTS_FILE", "the inputs file must hold one JSON object", 4)
    return inputs


def _send(inst, key, body):
    req = urllib.request.Request(inst["endpoint"].rstrip("/") + "/v1/invoke", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    opener = urllib.request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(req, timeout=300) as resp:
            return _read_json_response(resp)
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            raise ClientError("SERVICE_REDIRECT_REFUSED", "the service redirected the credential-bearing request", 3)
        return _read_json_response(e)
    except (urllib.error.URLError, OSError) as e:
        raise ClientError("SERVICE_UNREACHABLE", str(getattr(e, "reason", e)), 3)


def _invalid(message):
    return ClientError("INVALID_SERVICE_RESPONSE", message, 3)


def _checked_result(out, inputs):
    """(file name, bytes, sha256, receipt record) for a 0.3 success, once every hash agrees. Nothing is written yet."""
    request_id = out.get("request_id")
    if not isinstance(request_id, str) or not SAFE_NAME_RE.fullmatch(request_id):
        raise _invalid("the service returned an invalid request id")
    result, receipt, provenance = out.get("result"), out.get("receipt"), out.get("provenance")
    if out.get("contract") != "0.3" or not all(isinstance(x, dict) for x in (result, receipt, provenance)):
        raise _invalid("the successful response omitted required fields")
    if receipt.get("request_id") != request_id:
        raise _invalid("the receipt names another request")
    if result.get("kind") == "artifact":
        content, filename = result.get("content"), result.get("filename")
        if result.get("media_type") not in MEDIA_TYPES or result.get("encoding") != "utf-8" \
                or not isinstance(content, str):
            raise _invalid("the artifact is not one of the text types")
        if not isinstance(filename, str) or not SAFE_NAME_RE.fullmatch(filename):
            raise _invalid("the service returned an unsafe file name")
        try:
            data = content.encode("utf-8")
        except UnicodeEncodeError:
            raise _invalid("the artifact is not valid UTF-8 text")
        digest = _sha256(data)
        if result.get("sha256") != digest or result.get("bytes") != len(data):
            raise _invalid("the artifact does not match its own SHA-256 and size")
        name = "%s-%s" % (request_id, filename)
    elif result.get("kind") == "report":
        data = _canonical(result)
        digest = _sha256(data)
        name = "%s-report.json" % request_id
    else:
        raise _invalid("the service returned an unknown result kind")
    if receipt.get("result_sha256") != digest:
        raise _invalid("the receipt's result_sha256 does not match the result")
    if receipt.get("inputs_sha256") != _sha256(_canonical(inputs)):
        raise _invalid("the receipt's inputs_sha256 does not match the inputs sent")
    if receipt.get("provenance_sha256") != _sha256(_canonical(provenance)):
        raise _invalid("the receipt's provenance_sha256 does not match the provenance")
    record = (json.dumps({"receipt": receipt, "provenance": provenance}, indent=2, sort_keys=True) + "\n").encode()
    return name, data, digest, record


def _write_new(root, name, data):
    """Write `data` to root/name atomically, refusing a name that already exists (os.link never replaces a file)."""
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, name)
    fd, pending = tempfile.mkstemp(prefix=".core-output-", dir=root)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.link(pending, path)
    except FileExistsError:
        raise _invalid("%s already exists; nothing was overwritten" % name)
    finally:
        os.unlink(pending)
    return path


def _save_v03(inst, out, inputs):
    name, data, digest, record = _checked_result(out, inputs)
    saved = _write_new(inst["output_root"], name, data)
    try:
        receipt_path = _write_new(inst["receipt_root"], out["request_id"] + ".json", record)
    except BaseException:
        os.unlink(saved)
        raise
    return {"ok": True, "contract": "0.3", "request_id": out["request_id"], "kind": out["result"]["kind"],
            "saved": saved, "sha256": digest, "receipt": receipt_path, "receipt_sha256": _sha256(record)}


def _call_v01(a, inst, key):
    out = _send(inst, key, json.dumps({"org": inst["org"], "capability": a.capability,
                                       "repo": a.repo or inst["default_repo"],
                                       "ref": "main" if a.ref is None else a.ref}).encode())
    if not out.get("ok"):
        return out, 2
    try:
        totals = out["report"]["totals"]
        findings = len(out["report"]["findings"])
        resolved_commit = out["provenance"]["resolved_commit"]
        path = _write_report(inst["report_root"], a.capability, out.get("request_id", ""), out)
        with open(path, "rb") as fh:
            report_sha256 = hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        raise ClientError("REPORT_WRITE_FAILED", "the client-owned report could not be persisted and verified", 4)
    except (KeyError, TypeError):
        raise _invalid("the successful response omitted required fields")
    return {"ok": True, "saved": path, "request_id": out["request_id"], "totals": totals, "findings": findings,
            "resolved_commit": resolved_commit, "report_sha256": report_sha256}, 0


def _call_v03(a, inst, key):
    if a.ref is not None and a.repo is None:
        raise ClientError("INVALID_ARGUMENTS", "--ref is sent only with --repo", 4)
    inputs = _read_inputs(a.inputs)
    body = {"contract": "0.3", "org": inst["org"], "capability": a.capability, "inputs": inputs}
    if a.repo is not None:
        body["repo"] = a.repo
        if a.ref is not None:
            body["ref"] = a.ref
    out = _send(inst, key, json.dumps(body).encode())
    if not out.get("ok"):
        return out, 2
    try:
        return _save_v03(inst, out, inputs), 0
    except OSError:
        raise ClientError("REPORT_WRITE_FAILED", "the client-owned output could not be persisted", 4)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("capability")
    p.add_argument("--repo")
    p.add_argument("--ref")
    p.add_argument("--inputs", help="a JSON file holding one object (contract 0.3 only)")
    p.add_argument("--instance", default=os.path.join(HERE, "instance.json"))
    a = p.parse_args(argv)
    try:
        v03 = len(a.capability) <= MAX_CAPABILITY_V03 and bool(CAPABILITY_V03_RE.fullmatch(a.capability))
        if not v03 and not CAPABILITY_RE.fullmatch(a.capability):
            raise ClientError("INVALID_CAPABILITY",
                              "capability must be a 0.1 name (repository-health) or a 0.3 id (domain.name@major)", 4)
        if not v03 and a.inputs is not None:
            raise ClientError("INVALID_ARGUMENTS", "--inputs is for a 0.3 capability id", 4)
        inst = _load_instance(a.instance)
        if not v03 and not a.repo and "default_repo" not in inst:
            raise ClientError("INVALID_INSTANCE", "default_repo must be a non-empty string", 4)
        key = os.environ.get(inst["key_env"], "")
        if not key:
            raise ClientError("MISSING_CREDENTIAL", "%s is not set" % inst["key_env"], 4)
        out, code = (_call_v03 if v03 else _call_v01)(a, inst, key)
    except ClientError as e:
        print(json.dumps({"ok": False, "error": {"code": e.code, "message": e.message}}))
        return e.exit_code
    print(json.dumps(out))
    return code


if __name__ == "__main__":
    sys.exit(main())
