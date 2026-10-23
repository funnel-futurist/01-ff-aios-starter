#!/usr/bin/env python3
"""Check the standards template and newly added top-level browse folders."""

import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADINGS = (
    "What this is and who it is for",
    "How it works",
    "Folder map",
    "Setup",
    "Where it runs",
    "Connections",
    "Training",
    "Owner and last reviewed",
)
FRAMEWORK_FOLDERS = {
    "app", "components", "lib", "public", "supabase", "src", "pages",
    "api", "tests", "test", "scripts", "docs", "assets", "config",
    "node_modules", "dist", "build", "coverage",
}
NUMBERED = re.compile(r"^(?:\d{2}|\d{2}[ab])[-_][A-Za-z0-9][A-Za-z0-9_-]*$")


def readme_errors(path):
    text = path.read_text(encoding="utf-8")
    found = set(re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    errors = [f"{path.relative_to(ROOT)}: missing section: {name}"
              for name in HEADINGS if name not in found]
    if "Excalidraw" not in text:
        errors.append(f"{path.relative_to(ROOT)}: mention the Excalidraw diagram")
    return errors


def new_paths(base):
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    return [pathlib.PurePosixPath(line) for line in result.stdout.splitlines()]


def main():
    errors = readme_errors(ROOT / "00-standards/template/README.md")
    if len(sys.argv) > 1:
        paths = new_paths(sys.argv[1])
        for folder in sorted({p.parts[0] for p in paths if len(p.parts) > 1}):
            if folder.startswith(".") or folder in FRAMEWORK_FOLDERS:
                continue
            if not NUMBERED.fullmatch(folder):
                errors.append(f"new top-level folder {folder!r} needs a number, or a documented framework exception")
        for path in paths:
            # Existing READMEs and instance folders migrate only in their own reviewed pass.
            if path.name != "README.md" or len(path.parts) != 2:
                continue
            if path.parts[0] == "00-standards":
                continue
            errors.extend(readme_errors(ROOT / path))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Standards check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
