#!/bin/bash
# Exact-candidate rehearsal for starter-2.10.0 (DRAFT): the four next-line PRs (#35, #36, #38, #39).
#
# usage: bash rehearse_2100.sh <empty scratch dir> [branch]
#
# The real record stays draft. A COPY with a rehearsal-only approval string lets the installer
# run; it still re-hashes every installed file against the pinned commit. Identity comes from a
# stub `gh` on PATH, never a real login. Nothing here pushes or tags. It reads GitHub twice: the
# clone, and the read-only release notice (R3), which lists tags and reads two public files.
set -u
R=${1:?usage: rehearse_2100.sh <empty scratch dir> [branch]}
BRANCH=${2:-exec/lane01-starter-2.10.0-20261014}
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
m = json.load(open("starter/releases/starter-2.10.0.json"))
print("record status:", m["status"], "| pin:", m["created_from"]["git_rev"], "| files:", m["counts"])
m["status"] = "approved"
m["approval"] = {"approved_by": "REHEARSAL-ONLY-NOT-AN-APPROVAL", "approved_at": "2026-10-14T00:00:00Z"}
json.dump(m, open("rehearsal-2.10.0.json", "w"), indent=2)
for v in ("2.8.0", "2.6.0"):
    m = json.load(open("starter/releases/starter-%s.json" % v))
    print("%s record status: %s" % (v, m["status"]))
    m["status"] = "approved"  # superseded now; this only builds a workspace as it was installed while approved
    json.dump(m, open("setup-%s.json" % v, "w"), indent=2)
print("2.9.0 record status:", json.load(open("starter/releases/starter-2.9.0.json"))["status"])
EOF
cat > org.json <<'EOF'
{"schema":"ff-aios-starter/org-config@1","org_id":"rehearsal-co","repository":"rehearsal/rehearsal-aios",
 "people":[{"github":"rehearsal-founder","role":"founder","display_name":"Rehearsal founder"}],
 "credentials":{},"code_owners":{"REPO_OWNER":["@rehearsal-founder"],"PRIMARY_REVIEWER":["@rehearsal-founder"]}}
EOF
AIOS="python3 $R/starter/scripts/aios/aios.py"
mine(){ # the client's own work, the same in every upgrade below
  printf '\n## My own rule\nAlways answer in British English.\n' >> CLAUDE.md
  echo "# my own note" > 02_Deliverables/mine.md
  printf '# Our avatar\nreal client notes\n' >> 01_Foundations/avatar_analysis/_workspace.md
  mkdir -p .claude/skills/my_skill && printf -- '---\nname: my_skill\ndescription: mine\n---\nmine\n' > .claude/skills/my_skill/SKILL.md
  printf '{"permissions":{"deny":["Bash(rm -rf *)"]}}\n' > .claude/settings.local.json
}
newbits(){ # what 2.10.0 adds, as seen in a workspace
  printf 'AGENTS.md present: '; [ -f "$1/AGENTS.md" ] && echo yes || echo no
  printf 'human-step cards: '; ls "$1/docs/human_steps" 2>/dev/null | wc -l | tr -d ' '
  printf 'release notice command: '; (cd "$1" && python3 scripts/aios/aios.py release notice --help >/dev/null 2>&1 && echo yes || echo no)
  printf 'workflow actions not pinned to a full SHA: '; grep -hE '^\s*-?\s*uses:' "$1"/.github/workflows/*.yml | grep -vE '@[0-9a-f]{40}' | grep -vc './' | tr -d ' '
}

say "R2 the real draft record is refused (no approval inferred)"
$AIOS install --release starter/releases/starter-2.10.0.json --target d1 --config org.json >/dev/null 2>&1; echo "install exit=$? (expect 2)"; rm -rf d1

say "R3 fresh install of the exact candidate"
git init -q --bare fresh.git; git clone -q fresh.git fresh 2>/dev/null
$AIOS install --release rehearsal-2.10.0.json --target fresh --config org.json | head -3; echo "install exit=${PIPESTATUS[0]}"
(cd fresh && G add -A && G commit -qm "Install AIOS")
$AIOS verify --target fresh --repo starter | grep -E "verdict|checked"
core fresh
newbits fresh
printf 'AGENTS.md equals a fresh render of the installed CLAUDE.md and core: '; python3 - <<'EOF'
import sys; sys.path.insert(0, "starter/scripts/aios")
from aioslib import adapters
print(open("fresh/AGENTS.md", encoding="utf-8").read() == adapters.render_agents_md("fresh"))
EOF
printf 'not shipped (releases/tests/evidence present): '; ls -d fresh/releases fresh/tests fresh/evidence 2>/dev/null | wc -l | tr -d ' '
printf 'live release notice in a 2.10.0 workspace (expect nothing: no newer approved release): '
(cd fresh && env -u AIOS_NO_RELEASE_NOTICE python3 scripts/aios/aios.py release notice; echo "[exit $?]")

say "R4 upgrade: the approved 2.9.0 with the client's own work -> 2.10.0 candidate"
git init -q --bare up.git; git clone -q up.git up 2>/dev/null
$AIOS install --release starter/releases/starter-2.9.0.json --target up --config org.json | head -1
cd up; mine
G add -A && G commit -qm "install 2.9.0"; G add -f .claude/settings.local.json && G add -A && G commit -qm "my work" 2>/dev/null
HIST_BEFORE=$(git log --oneline | wc -l | tr -d ' ')
cd ..
fp starter up fp-before.json; snap up snap-before.json
$AIOS upgrade --release rehearsal-2.10.0.json --target up --repo starter --dry-run 2>&1 | grep -vE "^  unchanged:"
$AIOS upgrade --release rehearsal-2.10.0.json --target up --repo starter 2>&1 | tail -3; echo "upgrade exit=${PIPESTATUS[0]}"
$AIOS verify --target up --repo starter | grep -E "verdict|checked"
fp starter up fp-after.json
printf 'client files (installer state_fingerprint) after upgrade: '; same fp-before.json fp-after.json
printf 'client rule kept: '; grep -c "British English" up/CLAUDE.md
printf 'git history before -> after: %s -> ' "$HIST_BEFORE"; (cd up && git log --oneline | wc -l | tr -d ' ')
newbits up

say "R5 rollback to 2.9.0: the whole workspace comes back byte for byte"
$AIOS rollback --target up 2>&1 | tail -2; echo "rollback exit=${PIPESTATUS[0]}"
snap up snap-after-rollback.json
printf 'whole workspace vs before the upgrade: '; same snap-before.json snap-after-rollback.json
printf 'git status after rollback (porcelain lines): '; (cd up && git status --porcelain | wc -l | tr -d ' ')

say "R6 upgrade from a 2.8.0 workspace (installed while 2.8.0 was approved)"
git init -q --bare w28.git; git clone -q w28.git w28 2>/dev/null
$AIOS install --release setup-2.8.0.json --target w28 --config org.json | head -1
(cd w28 && mine && G add -f .claude/settings.local.json && G add -A && G commit -qm "2.8.0 + my work")
fp starter w28 fp28-before.json
$AIOS upgrade --release rehearsal-2.10.0.json --target w28 --repo starter 2>&1 | tail -1; echo "upgrade exit=${PIPESTATUS[0]}"
fp starter w28 fp28-after.json
printf 'client files after 2.8.0 -> 2.10.0: '; same fp28-before.json fp28-after.json
core w28

say "R7 upgrade from a 2.6.0 workspace: the bundled third-party document-skill copies go"
git init -q --bare w26.git; git clone -q w26.git w26 2>/dev/null
$AIOS install --release setup-2.6.0.json --target w26 --config org.json | head -1
printf 'document-skill folders before (docx, pptx, xlsx, pdf): '; ls -d w26/.claude/skills/docx w26/.claude/skills/pptx w26/.claude/skills/xlsx w26/.claude/skills/pdf 2>/dev/null | wc -l | tr -d ' '
(cd w26 && printf '\nmy 2.6.0 rule\n' >> CLAUDE.md && G add -A && G commit -qm "2.6.0 + my rule")
fp starter w26 fp26-before.json
$AIOS upgrade --release rehearsal-2.10.0.json --target w26 --repo starter 2>&1 | tail -1; echo "upgrade exit=${PIPESTATUS[0]}"
printf 'document-skill folders after: '; ls -d w26/.claude/skills/docx w26/.claude/skills/pptx w26/.claude/skills/xlsx w26/.claude/skills/pdf 2>/dev/null | wc -l | tr -d ' '
fp starter w26 fp26-after.json
printf 'client files after 2.6.0 -> 2.10.0: '; same fp26-before.json fp26-after.json
printf 'CLAUDE.md lines the upgrade added (expect only the declared seed line, the core import): '; (cd w26 && git diff HEAD -- CLAUDE.md | grep -E '^\+[^+]' | tr '\n' ' '); echo
printf 'client rule kept: '; grep -c "my 2.6.0 rule" w26/CLAUDE.md
$AIOS verify --target w26 --repo starter | grep -E "verdict"

say "R8 a client's own AGENTS.md: the upgrade refuses and changes nothing"
git init -q --bare ag.git; git clone -q ag.git ag 2>/dev/null
$AIOS install --release starter/releases/starter-2.9.0.json --target ag --config org.json >/dev/null
(cd ag && printf '# my Codex rules\n' > AGENTS.md && G add -A && G commit -qm "2.9.0 + my AGENTS.md")
snap ag snap-ag-before.json
$AIOS upgrade --release rehearsal-2.10.0.json --target ag --repo starter 2>&1 | grep -iE 'AGENTS|refus|exists' | head -3; echo "upgrade exit=${PIPESTATUS[0]}"
snap ag snap-ag-after.json
printf 'workspace after the refusal: '; same snap-ag-before.json snap-ag-after.json

say "R9 a hand-edited managed workflow is refused, not overwritten"
git init -q --bare ed.git; git clone -q ed.git ed 2>/dev/null
$AIOS install --release starter/releases/starter-2.9.0.json --target ed --config org.json >/dev/null
(cd ed && echo "# my edit" >> .github/workflows/pr-review.yml && G add -A && G commit -qm "edit workflow")
$AIOS upgrade --release rehearsal-2.10.0.json --target ed --repo starter 2>&1 | grep -iE 'refus|edited|modified' | head -2; echo "upgrade exit=${PIPESTATUS[0]}"
printf 'client edit still there: '; grep -c "my edit" ed/.github/workflows/pr-review.yml

say "R10 release tag route (local clone only): tag on the approval commit passes, tag on the pin fails"
cd starter
python3 - <<'EOF'
import json
p = "releases/starter-2.10.0.json"; m = json.load(open(p)); m["status"] = "approved"
m["approval"] = {"approved_by": "REHEARSAL-ONLY-NOT-AN-APPROVAL", "approved_at": "2026-10-14T00:00:00Z"}
json.dump(m, open(p, "w"), indent=2)
EOF
G commit -qam "rehearsal approval (local only)"
git tag rehearsal-approval HEAD
git tag rehearsal-pin "$(python3 -c "import json;print(json.load(open('releases/starter-2.10.0.json'))['created_from']['git_rev'])")"
$AIOS release check-tag rehearsal-approval --release-id starter-2.10.0 | tail -1
$AIOS release check-tag rehearsal-pin --release-id starter-2.10.0 2>&1 | sed -n 3,4p
cd ..
echo; echo "rehearsal done"
