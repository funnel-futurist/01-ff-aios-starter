"""Delegated install (03a #259, scope 5): a founder lets one named person install one approved release
into one repository until an expiry (at most 30 days), revocable. A grant is reusable within that window;
use is not recorded here.

The grant lives in the client's `.aios/config.json` under `install_delegations` - the same founder-lane,
code-owner-reviewed file that already holds the people map. So a grant has exactly the trust of the people
map: nobody can write themselves one without a founder approving the change.

What this does not do (by design):
- no `--as-founder`, no environment identity override: the actor is whoever `gh api user` says
  (roles.identity), the same code path the founder gate uses;
- no self-grant: the granter must be a founder/co-founder in the people map and must not be the delegate;
- no wider authority: the delegate may run `install` for that release and repository only. upgrade,
  rollback, adopt, governance and pricing still need a founder (roles.require_lifecycle).

Grant shape:
    {"grant_id": "dg-...", "delegate": "<github login>", "granted_by": "<founder github login>",
     "scope": "install", "target_repository": "owner/name", "release_id": "starter-x.y.z",
     "git_rev": "<40-hex>", "granted_at": "<ISO-8601 UTC>", "expires_at": "<ISO-8601 UTC>",
     "revoked_at": null}
"""
import re
from datetime import datetime, timedelta, timezone

from . import roles
from .util import EXIT_ROLE, Refusal

SCOPE = "install"
MAX_DAYS = 30
GRANT_ID = re.compile(r"^dg-[a-z0-9-]{4,64}$")
REV = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = ("grant_id", "delegate", "granted_by", "scope", "target_repository", "release_id",
            "git_rev", "granted_at", "expires_at")


def _when(value, field):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Refusal(EXIT_ROLE, "delegation %s must be an ISO-8601 UTC time ending in Z" % field)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise Refusal(EXIT_ROLE, "delegation %s is not a valid time" % field) from None


def find(config, grant_id):
    if not isinstance(grant_id, str) or not GRANT_ID.fullmatch(grant_id):
        raise Refusal(EXIT_ROLE, "delegation id must match %s" % GRANT_ID.pattern)
    matches = [g for g in (config.get("install_delegations") or []) if isinstance(g, dict)
               and g.get("grant_id") == grant_id]
    if len(matches) != 1:
        raise Refusal(EXIT_ROLE, "no single delegation %s in this workspace's config" % grant_id,
                      ["a founder adds it to .aios/config.json (install_delegations), a code-owner-reviewed path"])
    return matches[0]


def check_grant(policy, config, manifest, grant, login, now=None):
    """Refuse unless `login` may install `manifest` under `grant`. Returns the grant's founder login."""
    now = now or datetime.now(timezone.utc)
    missing = [k for k in REQUIRED if not grant.get(k)]
    if missing:
        raise Refusal(EXIT_ROLE, "delegation is missing %s" % ", ".join(missing))
    if grant["scope"] != SCOPE:
        raise Refusal(EXIT_ROLE, "delegation scope is %r; only %r can be delegated" % (grant["scope"], SCOPE))

    delegate = str(grant["delegate"]).lower()
    granter = str(grant["granted_by"]).lower()
    if not login or login.lower() != delegate:
        raise Refusal(EXIT_ROLE, "this delegation is for %s, not %s" % (grant["delegate"], login or "an unknown person"))
    if granter == delegate:
        raise Refusal(EXIT_ROLE, "a delegation cannot be granted to oneself")
    granter_role = roles.role_for(config, granter)
    if granter_role not in roles.lifecycle_roles(policy, "install"):
        raise Refusal(EXIT_ROLE, "%s may not install, so cannot delegate installing" % grant["granted_by"])

    if grant["target_repository"] != config.get("repository"):
        raise Refusal(EXIT_ROLE, "delegation is for %s, but this config is for %s"
                      % (grant["target_repository"], config.get("repository")))
    if grant["release_id"] != manifest.get("release_id"):
        raise Refusal(EXIT_ROLE, "delegation is for release %s, not %s"
                      % (grant["release_id"], manifest.get("release_id")))
    rev = (manifest.get("created_from") or {}).get("git_rev")
    if not REV.fullmatch(str(grant["git_rev"])) or grant["git_rev"] != rev:
        raise Refusal(EXIT_ROLE, "delegation is pinned to a different release revision")

    if grant.get("revoked_at"):
        raise Refusal(EXIT_ROLE, "delegation %s was revoked at %s" % (grant["grant_id"], grant["revoked_at"]))
    granted, expires = _when(grant["granted_at"], "granted_at"), _when(grant["expires_at"], "expires_at")
    if not granted < expires or expires - granted > timedelta(days=MAX_DAYS):
        raise Refusal(EXIT_ROLE, "delegation must expire after it is granted and within %d days" % MAX_DAYS)
    if now < granted:
        raise Refusal(EXIT_ROLE, "delegation %s is not valid yet" % grant["grant_id"])
    if now >= expires:
        raise Refusal(EXIT_ROLE, "delegation %s expired at %s" % (grant["grant_id"], grant["expires_at"]))
    return grant["granted_by"]


def require_delegated_install(policy, config, manifest, grant_id, now=None):
    """The real actor (gh) + a founder's grant for this exact release and repository. (login, role label)."""
    grant = find(config, grant_id)
    login, source = roles.identity()
    if not login:
        raise Refusal(EXIT_ROLE, "cannot establish who is running this (%s)" % source,
                      roles.identity_help(source))
    granter = check_grant(policy, config, manifest, grant, login, now=now)
    return login, "delegate of %s, grant %s" % (granter, grant["grant_id"])
