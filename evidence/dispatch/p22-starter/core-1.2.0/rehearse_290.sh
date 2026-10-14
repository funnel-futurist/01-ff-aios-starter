#!/bin/bash
# Exact-candidate rehearsal for starter-2.9.0 (DRAFT): AIOS Operator Core 1.2.0.
#
# usage: bash rehearse_290.sh <empty scratch dir> [branch]
#
# The real record stays draft. A COPY with a rehearsal-only approval string lets the installer
# run; it still re-hashes every installed file against the pinned commit. Identity comes from a
# stub `gh` on PATH, never a real login. Nothing here pushes, tags or touches GitHub except the
# read-only clone.
set -u
R=${1:?usage: rehearse_290.sh <empty scratch dir> [branch]}
BRANCH=${2:-exec/lane01-starter-core-1.2.0-20261014}
rm -rf "$R"; mkdir -p "$R"; cd "$R" || exit 1
say(){ printf '\n### %s\n' "$*"; }

mkdir -p bin; printf '#!/bin/sh\n[ "$1" = api ] && [ "$2" = user ] && { echo rehearsal-founder; exit 0; }; exit 1\n' > bin/gh; chmod +x bin/gh
export PATH="$R/bin:$PATH"
G(){ git -c user.email=r@example.invalid -c user.name=Rehearsal "$@"; }

# Hash every file outside .git and the installer's own retained undo copies (.aios/backups/,
# git-ignored); compare two snapshots.
snap(){ python3 - "$1" "$2" <<'EOF'
import hashlib, json, os, sys
root, out = sys.argv[1], sys.argv[2]
h = {}
for d, ds, fs in os.walk(root):
    ds[:] = [x for x in ds if x != ".git" and os.path.relpath(os.path.join(d, x), root) != os.path.join(".aios", "backups")]
    for f in fs:
        p = os.path.join(d, f)
        h[os.path.relpath(p, root)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
json.dump(h, open(out, "w"), sort_keys=True)
print(len(h), "files")
EOF
}
same(){ python3 - "$1" "$2" <<'EOF'
import json, sys
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
print("IDENTICAL" if not diff else "DIFFERENT: %d path(s): %s" % (len(diff), ", ".join(diff[:12])))
EOF
}
fp(){ python3 - "$1" "$2" "$3" <<'EOF'
import json, sys
sys.path.insert(0, sys.argv[1] + "/scripts/aios")
from aioslib import install
json.dump(install.state_fingerprint(sys.argv[2]), open(sys.argv[3], "w"), sort_keys=True)
EOF
}
core(){ sed -n 3p "$1/.aios/operator_core/OPERATOR_CORE.md"; printf 'import lines in CLAUDE.md: '; grep -cxF '@.aios/operator_core/OPERATOR_CORE.md' "$1/CLAUDE.md"; }

say "R0 tools"
python3 --version; git --version | head -1; node --version

say "R1 fresh clone of the candidate branch from GitHub"
git clone -q --branch "$BRANCH" https://github.com/funnel-futurist/ff-aios-starter.git starter
(cd starter && git log --oneline -1)
python3 - <<'EOF'
import json
m = json.load(open("starter/releases/starter-2.9.0.json"))
print("record status:", m["status"], "| pin:", m["created_from"]["git_rev"])
m["status"] = "approved"
m["approval"] = {"approved_by": "REHEARSAL-ONLY-NOT-AN-APPROVAL", "approved_at": "2026-10-14T00:00:00Z"}
json.dump(m, open("rehearsal-2.9.0.json", "w"), indent=2)
m = json.load(open("starter/releases/starter-2.7.2.json"))
m["status"] = "approved"  # 2.7.2 is superseded now; this only builds a workspace as it was installed while approved
json.dump(m, open("setup-2.7.2.json", "w"), indent=2)
print("2.8.0 record status:", json.load(open("starter/releases/starter-2.8.0.json"))["status"])
EOF
cat > org.json <<'EOF'
{"schema":"ff-aios-starter/org-config@1","org_id":"rehearsal-co","repository":"rehearsal/rehearsal-aios",
 "people":[{"github":"rehearsal-founder","role":"founder","display_name":"Rehearsal founder"}],
 "credentials":{},"code_owners":{"REPO_OWNER":["@rehearsal-founder"],"PRIMARY_REVIEWER":["@rehearsal-founder"]}}
EOF
AIOS="python3 $R/starter/scripts/aios/aios.py"

say "R2 the real draft record is refused (no approval inferred)"
$AIOS install --release starter/releases/starter-2.9.0.json --target d1 --config org.json >/dev/null 2>&1; echo "install exit=$? (expect 2)"; rm -rf d1

say "R3 fresh install of the exact candidate"
git init -q --bare fresh.git; git clone -q fresh.git fresh 2>/dev/null
$AIOS install --release rehearsal-2.9.0.json --target fresh --config org.json | head -3; echo "install exit=${PIPESTATUS[0]}"
(cd fresh && G add -A && G commit -qm "Install AIOS")
$AIOS verify --target fresh --repo starter | grep -E "verdict|checked"
core fresh
printf 'installed core sha256 = manifest pin: '; python3 -c "
import hashlib,json;b=open('fresh/.aios/operator_core/OPERATOR_CORE.md','rb').read();m=json.load(open('fresh/.aios/operator_core/manifest.json'))
print(hashlib.sha256(b).hexdigest()==m['sha256'], '| version', m['version'], '| source', m['source_commit'][:9])"
printf 'not shipped (releases/tests/evidence present): '; ls -d fresh/releases fresh/tests fresh/evidence 2>/dev/null | wc -l | tr -d ' '
printf 'private canon or company-update text in the installed tree: '; grep -rlE 'ff-creation-system|anti-ai-human-writing|team_updates|hiring_and_ip_intake' fresh --exclude-dir=.git | wc -l | tr -d ' '

say "R4 upgrade: approved 2.8.0 workspace with the client's own work -> 2.9.0 candidate"
git init -q --bare up.git; git clone -q up.git up 2>/dev/null
$AIOS install --release starter/releases/starter-2.8.0.json --target up --config org.json | head -1
core up
cd up
printf '\n## My own rule\nAlways answer in British English.\n' >> CLAUDE.md
echo "# my own note" > 02_Deliverables/mine.md
printf '# Our avatar\nreal client notes\n' >> 01_Foundations/avatar_analysis/_workspace.md
mkdir -p .claude/skills/my_skill && printf -- '---\nname: my_skill\ndescription: mine\n---\nmine\n' > .claude/skills/my_skill/SKILL.md
printf '{"permissions":{"deny":["Bash(rm -rf *)"]}}\n' > .claude/settings.local.json
G add -A && G commit -qm "install 2.8.0"; G add -f .claude/settings.local.json && G add -A && G commit -qm "my work"
HIST_BEFORE=$(git log --oneline | wc -l | tr -d ' ')
cd ..
fp starter up fp-before.json; snap up snap-before.json
$AIOS upgrade --release rehearsal-2.9.0.json --target up --repo starter --dry-run 2>&1 | grep -vE "^  unchanged:"
$AIOS upgrade --release rehearsal-2.9.0.json --target up --repo starter 2>&1 | tail -3; echo "upgrade exit=${PIPESTATUS[0]}"
$AIOS verify --target up --repo starter | grep -E "verdict|checked"
core up
fp starter up fp-after.json
printf 'client files (installer state_fingerprint) after upgrade: '; same fp-before.json fp-after.json
printf 'client rule kept: '; grep -c "British English" up/CLAUDE.md
printf 'git history before -> after: %s -> ' "$HIST_BEFORE"; (cd up && git log --oneline | wc -l | tr -d ' ')
printf 'git status after upgrade (porcelain lines, managed changes expected): '; (cd up && git status --porcelain | wc -l | tr -d ' ')

say "R5 rollback to 2.8.0: the whole workspace comes back byte for byte"
$AIOS rollback --target up 2>&1 | tail -2; echo "rollback exit=${PIPESTATUS[0]}"
snap up snap-after-rollback.json
printf 'whole workspace vs before the upgrade: '; same snap-before.json snap-after-rollback.json
printf 'git status after rollback (porcelain lines): '; (cd up && git status --porcelain | wc -l | tr -d ' ')
core up

say "R6 upgrade from a 2.7.2 workspace (installed while 2.7.2 was approved)"
git init -q --bare old.git; git clone -q old.git old 2>/dev/null
$AIOS install --release setup-2.7.2.json --target old --config org.json | head -1
(cd old && printf '\nmy 2.7.2 rule\n' >> CLAUDE.md && G add -A && G commit -qm "2.7.2 + my rule")
fp starter old fp72-before.json
$AIOS upgrade --release rehearsal-2.9.0.json --target old --repo starter 2>&1 | tail -1; echo "upgrade exit=${PIPESTATUS[0]}"
fp starter old fp72-after.json
printf 'client files after 2.7.2 -> 2.9.0: '; same fp72-before.json fp72-after.json
core old

say "R7 a hand-edited managed core is refused, not overwritten"
git init -q --bare ed.git; git clone -q ed.git ed 2>/dev/null
$AIOS install --release starter/releases/starter-2.8.0.json --target ed --config org.json >/dev/null
(cd ed && echo "my edit" >> .aios/operator_core/OPERATOR_CORE.md && G add -A && G commit -qm "edit core")
$AIOS upgrade --release rehearsal-2.9.0.json --target ed --repo starter 2>&1 | grep -iE 'refus|edited|modified' | head -2; echo "upgrade exit=${PIPESTATUS[0]}"
printf 'client edit still there: '; grep -c "my edit" ed/.aios/operator_core/OPERATOR_CORE.md

say "R8 release tag route (local clone only): tag on the approval commit passes, tag on the pin fails"
cd starter
python3 - <<'EOF'
import json
p = "releases/starter-2.9.0.json"; m = json.load(open(p)); m["status"] = "approved"
m["approval"] = {"approved_by": "REHEARSAL-ONLY-NOT-AN-APPROVAL", "approved_at": "2026-10-14T00:00:00Z"}
json.dump(m, open(p, "w"), indent=2)
EOF
G commit -qam "rehearsal approval (local only)"
git tag rehearsal-approval HEAD
git tag rehearsal-pin "$(python3 -c "import json;print(json.load(open('releases/starter-2.9.0.json'))['created_from']['git_rev'])")"
$AIOS release check-tag rehearsal-approval --release-id starter-2.9.0 | tail -1
$AIOS release check-tag rehearsal-pin --release-id starter-2.9.0 2>&1 | sed -n 3,4p
cd ..
echo; echo "rehearsal done"
