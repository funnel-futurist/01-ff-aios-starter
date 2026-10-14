"""A website folder that moves must not silently break its deploys.

The 2.x guide told clients to keep their site in `11_Projects/<site>/` and point Vercel's Root
Directory at it. The 3.0 folder move changes that path, so a Vercel project still set to the old
folder fails its next deploy. Founder requirement (2026-10-14): the upgrade refuses until every
affected Root Directory is corrected **and verified**. Verified means read back from Vercel, not
taken on the client's word.

How it decides, read-only, for EVERY folder move (not only folders that look like a site: a
site built with something this code doesn't recognise must not slip through):

* Which Vercel projects build this repository: `GET /v10/projects?repoUrl=...` in the personal
  scope and every team the token lists, page by page, plus any project named in a site folder's
  `.vercel/project.json` (what `vercel link` writes). Every one of those scopes must answer; one
  that doesn't makes the result unverified, not empty.
* A project whose Root Directory is inside an old folder is **not corrected**: refused, with the
  exact new path to set.
* Otherwise **verified**: no project the token can read builds a folder the upgrade moves.
* No token: refused, unless the founder states the repository isn't deployed by Vercel
  (`--no-vercel`, recorded with the upgrade). That statement is itself refused when Vercel's own
  files (`vercel.json`, `.vercel/`) are in the folders that move.
* Redirects are never followed: urllib would forward the token to wherever they point.

The token is the client's own (`VERCEL_TOKEN`), used for GET requests only, never printed and
never written anywhere.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from . import layout as layout_mod

API = "https://api.vercel.com"
ENV_TOKEN = "VERCEL_TOKEN"
ENV_API = "AIOS_VERCEL_API"  # tests point this at a local fake Vercel
ENV_TEAM = "VERCEL_TEAM_ID"  # optional: the team a team-scoped token belongs to
CARD = "docs/human_steps/move_a_vercel_site.md"
TIMEOUT = 15


class _Unverified(Exception):
    def __init__(self, message, code=None):
        super(_Unverified, self).__init__(message)
        self.code = code


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: urllib would forward the Authorization header to wherever it
    points, which could hand the client's token to another site (independent review)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Unverified("Vercel answered %d with a redirect, which isn't followed" % code)


_OPENER = urllib.request.build_opener(_NoRedirect)


def _get(api, token, path, params=None):
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    req = urllib.request.Request(api.rstrip("/") + path + query,
                                 headers={"Authorization": "Bearer %s" % token,
                                          "Accept": "application/json",
                                          "User-Agent": "aios-starter-upgrade"})
    try:
        with _OPENER.open(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except _Unverified:
        raise
    except urllib.error.HTTPError as exc:
        raise _Unverified("Vercel answered %d for %s" % (exc.code, path.split("?")[0]), exc.code)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise _Unverified("couldn't reach Vercel (%s)" % getattr(exc, "reason", exc))


MAX_PAGES = 50


def _all(api, token, path, params, key, cursor):
    """Every page of a Vercel list. Projects continue with `from` (a token), teams with `until`
    (a timestamp); both say where to continue in `pagination.next`. Missing a project on page two
    would move a live site unchecked (independent review)."""
    params = dict(params)
    out = []
    for _page in range(MAX_PAGES):
        data = _get(api, token, path, params)
        out.extend(data.get(key) or [])
        nxt = (data.get("pagination") or {}).get("next")
        if not nxt:
            return out
        params[cursor] = nxt
    raise _Unverified("Vercel listed more than %d pages of %s" % (MAX_PAGES, key))


def _scope(org_id):
    return {"teamId": org_id} if org_id and str(org_id).startswith("team_") else {}


def _projects(api, token, repo_slug, sites):
    """({project id: (name, root directory, how found)}, scopes read).

    Exhaustive or nothing: every scope the token is known to reach must be readable. A
    full-account token lists its teams, and then the personal scope and every team must answer.
    A token scoped to one team may be refused the team list; then the team must be named
    (VERCEL_TEAM_ID, or a site's .vercel/project.json) and that team must answer. Without a
    GitHub repository to filter by, every project in those scopes is read, so a project building
    an old folder can't hide behind a missing link.
    """
    found = {}
    try:
        teams = _all(api, token, "/v2/teams", {"limit": 100}, "teams", "until")
        required = [None] + [t.get("id") for t in teams if t.get("id")]
        team_scoped = False
    except _Unverified as exc:
        if exc.code not in (401, 403):
            raise  # a redirect, an outage: not a team-scoped token
        named = [os.environ.get(ENV_TEAM, "")] + [(s.get("vercel") or {}).get("orgId") or "" for s in sites]
        required = sorted({t for t in named if t.startswith("team_")})
        team_scoped = True
        if not required:
            raise _Unverified("this token can't list your Vercel teams and no team was named: set %s "
                              "to the team's id (it starts with team_), or use a token with access "
                              "to the whole account" % ENV_TEAM)
    read = []
    for scope in required:
        params = {"limit": 100}
        if repo_slug:
            params["repoUrl"] = "https://github.com/%s" % repo_slug
        params.update(_scope(scope) if scope else {})
        listed = _all(api, token, "/v10/projects", params, "projects", "from")  # any refusal: unverified
        read.append(scope or "personal")
        for p in listed:
            found[p.get("id")] = (p.get("name"), (p.get("rootDirectory") or "").strip("/"),
                                  ("linked to %s" % repo_slug) if repo_slug else "in this account")
    for site in sites:
        link = site.get("vercel")
        if not link:
            continue
        if not link.get("projectId"):
            raise _Unverified("%s/.vercel/project.json names no project" % site["from"])
        p = _get(api, token, "/v9/projects/%s" % urllib.parse.quote(link["projectId"]),
                 _scope(link.get("orgId")))
        found[p.get("id") or link["projectId"]] = (
            p.get("name"), (p.get("rootDirectory") or "").strip("/"),
            "named in %s/.vercel/project.json" % site["from"])
    return found, read, team_scoped


def check(sites, layout, repo_slug, token=None, api=None, no_vercel=False, vercel_files=()):
    """(rows, problems) for a layout move. Any problem refuses the upgrade.

    Every move is checked, not only folders that look like a website: a site with no file this
    code recognises would otherwise move unchecked (independent review). So the upgrade needs one
    of two things: a Vercel token, read-only, or the founder's own statement that this repository
    isn't deployed by Vercel (`--no-vercel`), which is refused when Vercel's own files are in the
    folders that move.
    """
    token = token if token is not None else os.environ.get(ENV_TOKEN, "")
    api = api or os.environ.get(ENV_API) or API
    names = ", ".join("%s (moves to %s)" % (s["from"], s["to"]) for s in sites)
    if not token:
        if no_vercel:
            if vercel_files:
                return [], ["--no-vercel, but Vercel's own files are in the folders that move (%s): "
                            "this repository is deployed by Vercel. Set %s so the upgrade can check "
                            "the projects instead. Card: %s" % (", ".join(vercel_files[:3]), ENV_TOKEN, CARD)]
            return ["not on Vercel: the founder stated this repository isn't deployed by Vercel "
                    "(--no-vercel), so no Vercel Root Directory was checked"
                    + ("; folders that look like a website: %s" % names if sites else "")], []
        return [], [
            "the upgrade has to confirm with Vercel that no project still builds a folder it moves%s"
            % ((": %s" % names) if sites else ""),
            "set %s for this one command (read-only; never printed or saved), then run the upgrade "
            "again. Card: %s" % (ENV_TOKEN, CARD),
            "if this repository isn't deployed by Vercel at all, add --no-vercel to say so; it's "
            "recorded with the upgrade",
        ]
    try:
        projects, scopes, team_scoped = _projects(api, token, repo_slug, sites)
    except _Unverified as exc:
        return [], ["%s: nothing was verified, so the folders can't move yet. Card: %s" % (exc, CARD)]

    roots = layout.get("retired_roots") or []
    rules = layout.get("moves") or []
    rows, problems = [], []
    for pid, (name, root, how) in sorted(projects.items(), key=lambda kv: str(kv[1][0])):
        old = next((r for r in roots if root == r or root.startswith(r + "/")), None)
        if old:
            new = layout_mod.destination(root, rules)
            problems.append(
                "Vercel project %s (%s, %s) still builds %s/. This upgrade moves that folder to %s/. "
                "In Vercel: the project's Settings, then Build and Deployment, then Root Directory: "
                "set it to %s and save. Then run the upgrade again. Card: %s"
                % (name, pid, how, root, new, new, CARD))
    where = ", ".join(scopes) + (" (a token scoped to that team)" if team_scoped else "")
    for site in sites:
        at_new = [n for n, r, _h in projects.values() if r == site["to"]]
        at_old = [n for n, r, _h in projects.values()
                  if r == site["from"] or r.startswith(site["from"] + "/")]
        if at_old:
            continue  # already a problem above
        if at_new:
            rows.append("%s: verified. Vercel project%s %s build%s %s/"
                        % (site["from"], "s" if len(at_new) > 1 else "", ", ".join(at_new),
                           "" if len(at_new) > 1 else "s", site["to"]))
        else:
            rows.append("%s: verified. No Vercel project in %s builds it, so no Vercel setting is "
                        "affected" % (site["from"], where))
    if not problems:
        rows.append("Vercel checked in %s: no project builds a folder this upgrade moves" % where)
    return rows, problems
