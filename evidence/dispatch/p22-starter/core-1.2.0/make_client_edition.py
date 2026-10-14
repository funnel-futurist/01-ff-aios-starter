"""Derive the Starter client edition of the AIOS Operator Core from its canonical source.

Applies exactly the three declared differences in .aios/operator_core/manifest.json and refuses
if any anchor is missing or appears more than once, so a source change that moves an anchor
fails loudly instead of shipping a half-edited file.

usage: python3 -I make_client_edition.py SOURCE.md OUT.md
"""
import sys

NOTE = ("<!-- Client edition. It differs from the source in sections 8 and 9 only; "
        ".aios/operator_core/manifest.json says how. Managed by the Starter: don't edit this "
        "file, an upgrade replaces it. -->\n")

EDITS = [
    ("- Client upgrades replace the managed core and never touch the client's own files or data.\n",
     "- Client upgrades replace the managed core and never touch the client's own files or data, "
     "apart from the one import line a release declares for `CLAUDE.md`: added once, never twice, "
     "and taken back by a rollback.\n"),
    ("Canonical file: `writing/anti-ai-human-writing.md` in the `ff-creation-system` repo "
     "(a locked Google Doc mirror exists; edit the Markdown by pull request). Load it for any "
     "prose of real length. Must-haves:\n",
     "Canonical source: your own voice rules in `03_Quality_Control/qc_preferences.md`, applied "
     "with the `/humanize` skill (`.claude/skills/humanize/SKILL.md`). Load them for any prose of "
     "real length. Must-haves:\n"),
]


def main(src, out):
    text = open(src, encoding="utf-8").read()
    lines = text.splitlines(keepends=True)
    if not lines[0].startswith("<!-- aios-operator-core v"):
        sys.exit("line 1 is not the version marker")
    if not lines[1].startswith("# AIOS Operator Core v"):
        sys.exit("line 2 is not the title")
    text = lines[0] + NOTE + "".join(lines[1:])
    for old, new in EDITS:
        n = text.count(old)
        if n != 1:
            sys.exit("anchor found %d times, expected 1: %r" % (n, old[:60]))
        text = text.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
