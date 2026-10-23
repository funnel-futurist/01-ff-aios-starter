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


def git_output(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout


def base_tree(event_base):
    # GitHub checks out a synthetic merge commit for pull_request. Its first
    # parent is the exact base tree used for this check, even if main moved.
    parents = git_output("rev-list", "--parents", "-n", "1", "HEAD").split()
    return "HEAD^1" if len(parents) == 3 else event_base


def top_level_directories(ref):
    return set(git_output("ls-tree", "-d", "--name-only", ref).splitlines())


def added_root_readme(base):
    return "README.md" in git_output(
        "diff", "--name-only", "--diff-filter=A", base, "HEAD", "--", "README.md"
    ).splitlines()


def main():
    errors = readme_errors(ROOT / "00-standards/template/README.md")
    if len(sys.argv) > 1:
        base = base_tree(sys.argv[1])
        for folder in sorted(top_level_directories("HEAD") - top_level_directories(base)):
            if folder.startswith(".") or folder in FRAMEWORK_FOLDERS:
                continue
            if not NUMBERED.fullmatch(folder):
                errors.append(f"new top-level folder {folder!r} needs a number, or a documented framework exception")
        # The eight headings describe a repository, not every folder. A newly
        # created repo's root README is the only PR-added README checked here.
        root_readme = ROOT / "README.md"
        if added_root_readme(base) or (
            root_readme.exists()
            and "<!-- aios-readme-template -->" in root_readme.read_text(encoding="utf-8")
        ):
            errors.extend(readme_errors(root_readme))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Standards check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
