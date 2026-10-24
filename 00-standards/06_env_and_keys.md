# .env and keys standard

Each person keeps their API keys in one core `.env` of their own. This standard says:
- what goes in that file;
- how each key is labeled;
- where keys may live;
- how keys are shared and paid for.

It applies to every repository and every installed AIOS. Nothing in it creates, changes or rotates a key.

## One core .env per person

- **One file:** each person has one core `.env`, at the root of their own AIOS working copy. It holds the keys that person uses. Another person's file is never a substitute for it.
- **Never in a repository:** that includes installed AIOS instances. `.gitignore` blocks `.env` and `.env.*`. Only `.env.example` is tracked, and it carries names and labels with empty values.
- **Where a key may live:**
  - the provider account that issued it;
  - the person's password manager;
  - the person's core `.env`;
  - for a deployed app, the host's encrypted environment settings, such as a Vercel variable marked Sensitive.
- **Never anywhere else:** not in Slack, email, a Claude chat, a document, a screenshot or a commit.

## Label every key

Five comment lines sit above each key in the `.env`:

| Label | What it says |
| --- | --- |
| Purpose | What the key is for and which tool uses it |
| Phase | The portal phase that first needs it, or "optional" |
| Get it from | The provider page where the key is created |
| Cost | Free, subscription or billed per use, plus its spend control: alert only, or an enforced limit and its scope |
| Owner | The account the key belongs to, and who pays if that's someone else |

`.env.example` shows the format. Group the keys by tool, so one look shows which key belongs to which tool.

## Own keys first; share only through a password manager

- **Your own key:** use one wherever the provider allows it. You can revoke it without affecting anyone else, and everything done with it is clearly yours.
- **When someone else pays:** the key still lives in your own `.env`, and its Owner label names the payer.
- **When a key can't be per person:** the account owner shares it through the password manager's sharing feature, with named people only. The registry records who holds it.

## The key registry

Every AIOS has `00_AIOS/systems/key_registry.md`.
- **What it holds:** one row per key, with its name, tool, purpose, who holds it and its status. It never holds a value.
- **What it's for:** it's the record of what tech you have. `connections.md` beside it lists the tools themselves.
- **Later:** the connectors on each Claude account may be added to the same registry.

## Cost control

There are two different controls, and the Cost label says which one a key has:
- **An alert** notifies you when spend passes an amount. Calls keep running.
- **An enforced limit** makes the provider stop or reject calls once spend reaches it.
  - It may cover one key, a project or the whole organization.
  - Some providers make you switch enforcement on, and some don't offer it.
  - It can lag, so spend can run slightly past it.

Before a usage-billed key is used for the first time:
- set an alert;
- where the provider offers an enforced limit, turn it on and confirm in the console that it shows as enforced and what it covers;
- write both on the key's Cost label: the alert, and the limit's scope and status. Where no limit is offered, write "alert only: no enforced limit" and who checks the usage.

An alert alone caps nothing, and even an enforced limit is a bound, not an exact maximum. One key per tool keeps each tool's spend separate.

## Claude Code and the .env

- **No reading:** Claude Code never reads a `.env`; the Starter's settings deny it.
- **The skill:** `env_keys` keeps the registry and the label layout, and hands the person the lines to paste. The person fills in the values from their password manager.
- **If a value leaks:** if a value ever appears outside the places listed above, treat it as exposed. Revoke it at the provider and make a new one.

## What changes together

This folder doesn't ship to installed instances. The `env_keys` skill and the registry template carry this standard there, so change all three in the same pull request.
