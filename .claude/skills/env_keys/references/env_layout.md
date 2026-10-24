# The labeled .env layout

This is how every key in a person's core `.env` is written down. Five label lines sit above the key, and the value is typed by the person from their password manager. The layout never holds a value; every line below ends in `=`.

## The label lines

| Label | What it says | Written like |
|---|---|---|
| Purpose | What the key is for and which tool uses it | `# Purpose: embeddings for search, used by the OpenAI API` |
| Phase | The portal phase that first needs it, or "optional" | `# Phase: optional` |
| Get it from | The provider page where the key is created | `# Get it from: the provider console, API keys page, signed in to your own account` |
| Cost | Free, subscription or billed per use, plus the cap that's set | `# Cost: billed per use, monthly cap and alert set in the console` |
| Owner | The account the key belongs to, and who pays if that's someone else | `# Owner: your account, paid by the company` |

## One key, written out

```
# --- Example Tool -------------------------------------------
# Purpose: what this key lets the tool do
# Phase: optional
# Get it from: the tool's console, API keys page, signed in as yourself
# Cost: billed per use, cap and alert set before first use
# Owner: your account
EXAMPLE_TOOL_API_KEY=
```

## Grouping

- **By tool:** group keys by tool, with one header line per tool, so one look shows which key belongs to which tool.
- **Several keys for one tool** (an ID and a secret, say) share one header. Each key still carries its five labels.
- **Order:** keep the groups in the same order as the rows in the key registry, so the two are easy to compare.

## Never in this file or the layout

- **A value:** not even the first few characters, and not an "example" that's really a live key.
- **Another person's key**, copied from their file.
- **A note of where a key was pasted:** if it was pasted somewhere other than the password manager or this file, it's exposed. Revoke it at the provider and make a new one.
