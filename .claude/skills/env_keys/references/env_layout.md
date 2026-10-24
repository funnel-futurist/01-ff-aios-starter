# The labeled .env layout

This is how every key in a person's core `.env` is written down. Five label lines sit above the key, and the value is typed by the person from their password manager. The layout never holds a value; every line below ends in `=`.

## The label lines

| Label | What it says | Written like |
|---|---|---|
| Purpose | What the key is for and which tool uses it | `# Purpose: embeddings for search, used by the OpenAI API` |
| Phase | The portal phase that first needs it, or "optional" | `# Phase: optional` |
| Get it from | The provider page where the key is created | `# Get it from: the provider console, API keys page, signed in to your own account` |
| Cost | Free, subscription or billed per use, plus its spend control | `# Cost: billed per use; alert set (notifies only); enforced limit on, project scope` |
| Owner | The account the key belongs to, and who pays if that's someone else | `# Owner: your account, paid by the company` |

## One key, written out

```
# --- Example Tool -------------------------------------------
# Purpose: what this key lets the tool do
# Phase: optional
# Get it from: the tool's console, API keys page, signed in as yourself
# Cost: billed per use; alert set (notifies only); enforced limit on, project scope
# Owner: your account
EXAMPLE_TOOL_API_KEY=
```

## The spend control on the Cost label

- **Alert:** set or not. It notifies; calls keep running.
- **Enforced limit:** on, off or not offered, and what it covers (the key, a project or the whole organization). It stops or rejects calls, but it can lag, so spend can run slightly past it.
- **Neither offered or set:** write "alert only: no enforced limit" or "no control", and who checks the usage. Never write "capped" for an alert.

## Grouping

- **By tool:** group keys by tool, with one header line per tool, so one look shows which key belongs to which tool.
- **Several keys for one tool** (an ID and a secret, say) share one header. Each key still carries its five labels.
- **Order:** keep the groups in the same order as the rows in the key registry, so the two are easy to compare.

## Where a key may live

A key may live in exactly four places:
- the provider account that issued it;
- the person's password manager;
- their own core `.env`, ignored by Git;
- for a deployed app that needs it, that host's encrypted environment settings (for example a Vercel variable marked Sensitive).

Copying a key along that path is normal, not an exposure. A key found anywhere else (a chat, Slack, email, a document, a screenshot or a commit) is exposed. Revoke it at the provider and make a new one, without repeating it.

## Never in the layout

- **A value:** not even the first few characters, and not an "example" that's really a live key.
- **Another person's key**, copied from their file.
