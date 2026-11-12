"""Phase unlock by license key (DW-705): the buyer-side half.

`aios.py phase unlock <phase>` sends the buyer's license key to FF's phase-unlock function and, only if that phase
is unlocked, saves the phase's setup prompts and config on this machine. A delivered phase stays here.

* The key comes from env AIOS_LICENSE_KEY, else the git-ignored file `.aios/license_key`. It is never printed,
  logged or written anywhere else, and a key file that git tracks is refused.
* The endpoint comes from env AIOS_PHASE_UNLOCK_URL, else `.aios/phase_unlock.json` {"url": "https://..."}.
* The payload is saved under the git-ignored `.aios/phases/<phase>/`, never in a tracked file.
No payload, key or secret ships in this repository.
"""

import json
import os
import re
import subprocess
import urllib.error
import urllib.request

from .util import EXIT_ERROR, Refusal

KEY_ENV = "AIOS_LICENSE_KEY"
URL_ENV = "AIOS_PHASE_UNLOCK_URL"
KEY_FILE = os.path.join(".aios", "license_key")
URL_FILE = os.path.join(".aios", "phase_unlock.json")
PHASES_DIR = os.path.join(".aios", "phases")
KEY_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")
PHASE_RE = re.compile(r"^[a-z0-9_]{1,64}$")
EXIT_REFUSED = 4

MESSAGES = {
    "locked": "Phase {phase} is not unlocked yet.",
    "revoked": "Your license key has been revoked. Contact Funnel Futurist; nothing was downloaded.",
    "unknown_key": "Your license key was not recognised. Check it was copied exactly; nothing was downloaded.",
    "unknown_phase": "There is no phase called {phase}.",
    "rate_limited": "Too many attempts with this key. Wait an hour, then try again.",
    "bad_request": "The request was rejected as malformed. Check the phase name and your key.",
    "unavailable": "The unlock service is temporarily unavailable. Try again later.",
    "error": "The unlock service hit an error. Try again later, and tell Funnel Futurist if it repeats.",
}


def _tracked(root, rel):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", rel],
                             capture_output=True, text=True)
    except OSError:
        return False
    return out.returncode == 0


def read_key(root, environ):
    key = (environ.get(KEY_ENV) or "").strip()
    if not key:
        path = os.path.join(root, KEY_FILE)
        if os.path.isfile(path):
            if _tracked(root, KEY_FILE):
                raise Refusal(EXIT_ERROR, "%s is tracked by git. Remove it from git (git rm --cached %s) "
                                          "before using it: a license key must never be committed." % (KEY_FILE, KEY_FILE))
            with open(path, encoding="utf-8") as fh:
                key = fh.read().strip()
    if not key:
        raise Refusal(EXIT_ERROR, "No license key found. Set %s, or save your key in %s "
                                  "(git-ignored). Your key is in your Funnel Futurist welcome email." % (KEY_ENV, KEY_FILE))
    if not KEY_RE.match(key):
        raise Refusal(EXIT_ERROR, "That license key is not in the expected format. Copy it again exactly.")
    return key


def read_url(root, environ):
    url = (environ.get(URL_ENV) or "").strip()
    if not url:
        path = os.path.join(root, URL_FILE)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                url = str(json.load(fh).get("url", "")).strip()
    if not url:
        raise Refusal(EXIT_ERROR, "No unlock address configured. Set %s or create %s." % (URL_ENV, URL_FILE))
    if not url.startswith("https://"):
        raise Refusal(EXIT_ERROR, "The unlock address must start with https://.")
    return url


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: it would carry the license key header to another address."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _post(url, key, phase, opener):
    req = urllib.request.Request(url, data=json.dumps({"phase": phase}).encode("utf-8"), method="POST",
                                 headers={"content-type": "application/json", "x-license-key": key})
    try:
        with opener(req, timeout=30) as res:
            return res.status, json.loads(res.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except ValueError:
            return exc.code, {}
    except (urllib.error.URLError, OSError, ValueError):
        raise Refusal(EXIT_ERROR, "Could not reach the unlock service. Check your connection and try again.")


def unlock(root, phase, environ=None, opener=None):
    """Returns (exit_code, message). Never returns or prints the key or the payload."""
    environ = os.environ if environ is None else environ
    if not PHASE_RE.match(phase or ""):
        raise Refusal(EXIT_ERROR, "Phase names are lowercase letters, digits and underscores, e.g. phase_2.")
    key = read_key(root, environ)
    url = read_url(root, environ)
    status, body = _post(url, key, phase, opener or _OPENER.open)
    if not isinstance(body, dict):
        body = {}
    result = body.get("result")
    if status == 200 and result == "delivered":
        if body.get("phase_key") != phase:
            raise Refusal(EXIT_ERROR, "The service answered for a different phase; nothing was saved.")
        out_dir = os.path.join(root, PHASES_DIR, phase)
        for d in (os.path.join(root, ".aios"), os.path.join(root, PHASES_DIR), out_dir):
            if os.path.islink(d):
                raise Refusal(EXIT_ERROR, "%s is a symlink; refusing to save the phase there." % os.path.relpath(d, root))
        os.makedirs(out_dir, exist_ok=True)
        final = os.path.join(out_dir, "payload.json")
        tmp = final + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"phase_key": phase, "version": body.get("version"), "payload": body.get("payload")},
                      fh, indent=2, sort_keys=True)
        os.replace(tmp, final)  # atomic: a half-written payload is never left in place
        return 0, "Phase %s unlocked. Its setup is saved in %s (kept on this machine, git-ignored)." % (
            phase, os.path.join(PHASES_DIR, phase, "payload.json"))
    if result == "locked":
        needs = body.get("needs") or {}
        missing = []
        if needs.get("previous_phase_complete") is False:
            missing.append("finish the previous phase in your portal")
        if needs.get("payment_cleared") is False:
            missing.append("the payment for this phase must clear")
        tail = (" Still needed: " + "; ".join(missing) + ".") if missing else ""
        return EXIT_REFUSED, MESSAGES["locked"].format(phase=phase) + tail
    if result in MESSAGES:
        return EXIT_REFUSED, MESSAGES[result].format(phase=phase)
    raise Refusal(EXIT_ERROR, "The unlock service gave an unexpected answer (HTTP %s). Try again later." % status)
