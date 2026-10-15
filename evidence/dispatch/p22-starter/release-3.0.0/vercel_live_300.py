#!/usr/bin/env python3
"""Live R-A check against Vercel's real API, with a throwaway project (port plan section 4, item 11).

usage: python3 vercel_live_300.py <empty scratch dir> --starter <candidate clone> --token-file <file>

1. Install 2.10.0 into a workspace whose `11_Projects/main-website/` is a small static site,
   linked to a NEW throwaway Vercel project (`.vercel/project.json`, as `vercel link` writes it)
   whose Root Directory is the old folder.
2. The 3.0 candidate refuses, naming the project and the new path, and changes nothing.
3. The Root Directory is corrected through Vercel's API (what the card's step 3 does by hand).
4. The candidate verifies it with Vercel and moves the site.
5. A production deployment of the upgraded workspace builds from the new folder and serves the page.
6. The throwaway project is deleted, and a read confirms it's gone.

The token is read from a file and sent only in Authorization headers; it is never printed or
written. Everything it creates is deleted at the end, even after a failure.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.vercel.com"
NAME = "aios-starter-3-rehearsal-20261014"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, (": " + detail) if detail else ""), flush=True)


def call(token, method, path, body=None, scope=None):
    url = API + path + (("&" if "?" in path else "?") + "teamId=" + scope if scope else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {}


def sh(cmd, cwd=None, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run(cmd, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--starter", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--scope", help="team id; default the token's personal team")
    a = ap.parse_args()
    token = json.load(open(a.token_file)).get("token")
    R = os.path.abspath(a.root)
    if os.path.exists(R):
        shutil.rmtree(R)
    os.makedirs(os.path.join(R, "bin"))
    with open(os.path.join(R, "bin", "gh"), "w") as fh:
        fh.write('#!/bin/sh\n[ "$1" = api ] && [ "$2" = user ] && { echo rehearsal-founder; exit 0; }; exit 1\n')
    os.chmod(os.path.join(R, "bin", "gh"), 0o755)
    env = {"PATH": os.path.join(R, "bin") + os.pathsep + os.environ["PATH"], "AIOS_NO_RELEASE_NOTICE": "1"}
    aios = [sys.executable, os.path.join(a.starter, "scripts/aios/aios.py")]

    code, teams = call(token, "GET", "/v2/teams?limit=100")
    scope = a.scope or next((t["id"] for t in teams.get("teams", []) if t.get("slug", "").endswith("-projects")), None)
    print("### V0 scope: the token's personal team (%s)" % ("found" if scope else "not found, HTTP %s%s" % (
        code, "; the CLI's saved token has expired: `vercel whoami` refreshes it" if code in (401, 403) else "")))
    if not scope:
        return 1
    project = None
    try:
        print("\n### V1 a throwaway project whose Root Directory is the 2.x folder")
        code, body = call(token, "POST", "/v11/projects", {"name": NAME, "rootDirectory": "11_Projects/main-website",
                                                          "framework": None}, scope)
        project = body.get("id")
        check("created %s (HTTP %s), Root Directory %s" % (NAME, code, body.get("rootDirectory")),
              code in (200, 201) and project and body.get("rootDirectory") == "11_Projects/main-website")
        if not project:
            return 1

        ws = os.path.join(R, "ws")
        sh(["git", "init", "-q", "--bare", ws + ".git"])
        sh(["git", "clone", "-q", ws + ".git", ws])
        G = lambda *x: sh(["git", "-c", "user.email=r@example.invalid", "-c", "user.name=R", "-C", ws] + list(x))
        G("checkout", "-q", "-b", "main")
        rec = json.load(open(os.path.join(a.starter, "releases/starter-2.10.0.json")))
        rec["status"] = "approved"
        rec["approval"] = {"approved_by": "REHEARSAL-ONLY-NOT-AN-APPROVAL", "approved_at": "2026-10-14T00:00:00Z"}
        json.dump(rec, open(os.path.join(R, "rehearsal-2.10.0.json"), "w"))
        cand = json.load(open(os.path.join(a.starter, "releases/starter-3.0.0.json")))
        cand["status"] = "approved"
        cand["approval"] = rec["approval"]
        json.dump(cand, open(os.path.join(R, "rehearsal-3.0.0.json"), "w"))
        json.dump({"schema": "ff-aios-starter/org-config@1", "org_id": "rehearsal-co",
                   "repository": "rehearsal/rehearsal-aios",
                   "people": [{"github": "rehearsal-founder", "role": "founder", "display_name": "F"}],
                   "credentials": {}, "code_owners": {}}, open(os.path.join(R, "org.json"), "w"))
        tree = os.path.join(R, "tree-2.10.0")
        sh(["git", "-C", a.starter, "worktree", "add", "-q", "--detach", tree, rec["created_from"]["git_rev"]])
        code, out = sh([sys.executable, os.path.join(tree, "scripts/aios/aios.py"), "install", "--release",
                        os.path.join(R, "rehearsal-2.10.0.json"), "--target", ws, "--config", os.path.join(R, "org.json"),
                        "--repo", a.starter], env=env)
        site = os.path.join(ws, "11_Projects", "main-website")
        os.makedirs(os.path.join(site, ".vercel"), exist_ok=True)
        with open(os.path.join(site, "index.html"), "w") as fh:
            fh.write("<!doctype html><title>aios 3.0 rehearsal</title><h1>moved site, same bytes</h1>\n")
        json.dump({"projectId": project, "orgId": scope}, open(os.path.join(site, ".vercel", "project.json"), "w"))
        with open(os.path.join(ws, ".gitignore"), "a") as fh:
            fh.write("\n.vercel\n")
        G("add", "-A")
        G("commit", "-qm", "2.10.0 with a site linked to Vercel")
        check("2.10.0 installed with a static site in 11_Projects/main-website, linked to the project", code == 0)

        up = aios + ["upgrade", "--release", os.path.join(R, "rehearsal-3.0.0.json"), "--target", ws, "--repo", a.starter]
        print("\n### V2 the candidate refuses while Vercel still builds the old folder")
        before = sh(["git", "-C", ws, "status", "--porcelain", "--ignored"])[1]
        code, out = sh(up, env=dict(env, VERCEL_TOKEN=token))
        refused = code == 5 and NAME in out and "set it to 02_Team_Ops/projects/main-website" in out
        check("refused (exit %d), naming %s and the exact new Root Directory" % (code, NAME), refused,
              "" if refused else out[-400:])
        check("nothing changed", before == sh(["git", "-C", ws, "status", "--porcelain", "--ignored"])[1]
              and os.path.isfile(os.path.join(site, "index.html")))
        check("the token appears nowhere in the output", token not in out)

        print("\n### V3 the Root Directory is corrected (the card's step 3, via the API)")
        code, body = call(token, "PATCH", "/v9/projects/%s" % project,
                          {"rootDirectory": "02_Team_Ops/projects/main-website"}, scope)
        check("Root Directory now %s (HTTP %s)" % (body.get("rootDirectory"), code),
              code == 200 and body.get("rootDirectory") == "02_Team_Ops/projects/main-website")

        print("\n### V4 the candidate verifies it with Vercel and moves the site")
        code, out = sh(up, env=dict(env, VERCEL_TOKEN=token))
        line = next((l.strip() for l in out.splitlines() if l.strip().startswith("website:")), "")
        check("upgraded (exit %d); %s" % (code, line), code == 0 and "verified" in line and NAME in line,
              "" if code == 0 else out[-400:])
        moved = os.path.join(ws, "02_Team_Ops/projects/main-website/index.html")
        check("the site is at 02_Team_Ops/projects/main-website with its bytes",
              os.path.isfile(moved) and "same bytes" in open(moved).read())
        for root, _d, files in os.walk(ws):
            if ".git" in root.split(os.sep):
                continue
            for f in files:
                with open(os.path.join(root, f), "rb") as fh:
                    if token.encode() in fh.read():
                        check("token written to %s" % f, False)

        print("\n### V5 a production deployment builds from the new folder")
        # The CLI uses its own signed-in session (the same account); no token on the command line,
        # where the process list would show it.
        code, out = sh(["vercel", "deploy", "--prod", "--yes", "--cwd", ws],
                       env={"VERCEL_ORG_ID": scope, "VERCEL_PROJECT_ID": project})
        # The CLI prints the address inside a line ("Production: https://... [2s]"), not on its own.
        found = re.search(r"https://[A-Za-z0-9.-]+\.vercel\.app", out)
        url = found.group(0) if found else ""
        check("deployed (exit %d)" % code, code == 0 and url, "" if code == 0 else out[-300:].replace(token, "***"))
        code, deps = call(token, "GET", "/v6/deployments?projectId=%s&limit=1" % project, scope=scope)
        dep = (deps.get("deployments") or [{}])[0]
        check("deployment state %s" % (dep.get("state") or dep.get("readyState")),
              (dep.get("state") or dep.get("readyState")) == "READY")
        alias = None
        code, pj = call(token, "GET", "/v9/projects/%s" % project, scope=scope)
        for t in (pj.get("targets") or {}).values():
            alias = (t.get("alias") or [None])[0] or alias
        if alias:
            try:
                with urllib.request.urlopen("https://" + alias, timeout=30) as r:
                    page = r.read().decode("utf-8", "replace")
                check("the production address serves the moved page (HTTP %d)" % r.status,
                      r.status == 200 and "moved site, same bytes" in page)
            except urllib.error.HTTPError as e:
                check("the production address answered HTTP %d" % e.code, False)
    finally:
        if project:
            print("\n### V6 cleanup")
            code, _ = call(token, "DELETE", "/v9/projects/%s" % project, scope=scope)
            check("throwaway project deleted (HTTP %s)" % code, code in (200, 204))
            code, _ = call(token, "GET", "/v9/projects/%s" % project, scope=scope)
            check("a read of it now answers 404", code == 404)
    print("\nRESULT: %d passed, %d failed" % (sum(RESULTS), len(RESULTS) - sum(RESULTS)))
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
