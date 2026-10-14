# Protected-text scan

For maintainers of this template. Not shipped to client workspaces (`release/**` is excluded from the package).

## The problem

This repository is public, and "Use this template" copies it. FF's protected method text must never land here by accident (a pasted paragraph in a new skill, a doc, a release brief). "We were careful" is not a control.

## The mechanism

A **fingerprint list** is made privately from the protected source files. The public tree is scanned against it. The list holds hashes, never text.

| | |
|---|---|
| Unit | every run of 12 consecutive words, lowercased, letters and digits only (so wrapping, case and markdown do not hide a paste) |
| Hash | HMAC-SHA256 under a random salt, first 8 bytes kept |
| Fail rule | the list's `min_hits` or more windows from one protected source in one file (3 unless the list says otherwise; `protected fingerprint --min-hits` sets it) |
| Scope | every file in the public tree (what git tracks), including `evidence/`, `templates/`, `releases/`, `tests/`, and the inside of `.docx`/`.xlsx`/`.pptx`/`.zip` files |
| Output | the path and an opaque source label such as `P-001`. Never any text |

### What the list is, and is not

- It **cannot be turned back into text.** Each entry is a keyed, truncated hash of one 12-word window. There is no text in the file.
- It **can confirm a guess.** Anyone holding the list and a candidate passage can test it. So the list is private anyway. The hash is the second wall, not the first.
- It **does not catch a paraphrase or a translation.** It is a tripwire for copy and paste, which is how protected text leaks. It does not prove that no protected idea is present.

## Where it runs

| Where | What runs | Needs the private list? |
|---|---|---|
| Public CI, every push and PR | the fixture tests (a planted invented paragraph must fail; the allow-list must be in order; the real tree is scanned against a fixture) and `protected check-allowlist` | No |
| Where the private list lives (a maintainer's machine, or the repository secret `PROTECTED_FINGERPRINTS_JSON`) | `protected scan` against the real list | Yes |

If the list is not configured, CI prints a `NOT RUN` warning and the scan command refuses to say "clean". Not having looked is not a result.

### Where FF's own list lives, and when it runs

- **A repository secret holds at most 48 KB**, about 2,500 fingerprints. That fits a short list of chosen passages. It doesn't fit a whole protected layer: FF's list is about 110 MB.
- **So FF keeps its list on a maintainer's machine and runs the scan at every release cut**, before the release is approved. The release brief records:
  - the findings;
  - how each was classified;
  - the list's sha256.
- **This repository's CI keeps printing `NOT RUN`.** That's accurate: CI didn't look.

## Commands

Private side, once per change to the protected set (output stays OUTSIDE this repository):

```bash
python3 scripts/aios/aios.py protected fingerprint \
  --source P-001=/private/path/to/first_protected_file.md \
  --source P-002=/private/path/to/second_protected_file.md \
  --out /private/path/fingerprints.json
```

Labels are opaque ids, never titles. A source with fewer than 12 words is refused, not ignored.

The scan, before every release and wherever the list lives:

```bash
python3 scripts/aios/aios.py protected scan --fingerprints /private/path/fingerprints.json
# or: AIOS_PROTECTED_FINGERPRINTS=/private/path/fingerprints.json python3 scripts/aios/aios.py protected scan
```

Exit code 7 on any finding. To use the repository secret (a list of 48 KB or less), store the file's contents as `PROTECTED_FINGERPRINTS_JSON`; the `tests` job then runs the real scan.

## The allow-list: `release/public_methods.json`

Seven method files are public **on purpose** today. The list names them one by one, each with a reason, and pins the sha256 of the exact bytes. The scan exempts those files and nothing else.

- Editing one of them turns CI red until a reviewer re-pins it (`protected pin`), so protected text cannot ride in on an allowed file.
- Whether each file stays public is a founder decision made separately. To pull one from the public tree, delete the entry and the file. This mechanism neither removes nor flags any of them.
- A stale entry, a missing reason or a duplicate fails `protected check-allowlist`.

## Rotating the list

Re-run `protected fingerprint` with the new source set (a new random salt is generated each time) and replace the private file and the secret.
