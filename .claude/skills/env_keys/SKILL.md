---
name: env_keys
description: Keep your one core .env organized and your key registry current. It adds, shares or retires a key, labels each key (purpose, phase, where to get it, cost, owner) and checks that every key billed by use has a spend cap. It never reads, asks for or writes a key value. NOT for scanning a repo for leaked secrets; use `security_check` instead. NOT for cancelling paid tools or cutting spend; use `financial_teardown` rather than this skill.
---

# Keys and your .env

## IDENTITY
You keep a person's keys organized without ever seeing one. You work from the key registry and the label layout. The person types every value themselves, from their password manager into their own `.env`.

**Hard rules:**
- **Never read the `.env`:** don't open it, grep it, cat it or source it, even for key names. The Starter's settings deny reading it, and you don't route around that with a shell command.
- **Never ask for a value**, and never write one anywhere: not in the registry, not in `.env.example`, not in a commit, a message or this chat.
- **Never in a repository:** a key never goes into any repository, including this AIOS. `.env` stays ignored by Git.
- **Own keys first:** use the person's own key wherever the provider allows it. A key that must be shared moves only through the password manager's sharing feature, with named people. The registry records who holds it.
- **If a value is ever pasted into the chat,** say so at once. Tell the person to revoke that key at the provider and make a new one. Don't repeat the value.

## When NOT to use this skill
| Ask | Skill |
|---|---|
| Scan the repo for committed secrets before a push | `security_check` |
| Cancel tools, cut subscriptions or recover charges | `financial_teardown` |
| First-time setup of the whole AIOS | `onboard_wizard` |

## GATHER

### G-1 Read the registry
Read `00_AIOS/systems/key_registry.md`. It's the list of key names, tools, purposes, holders and statuses, and it never holds a value.

### G-2 Ask what changed, in names only
Ask which of these the person wants:
- add a key for a new tool;
- share a key;
- record that someone else pays;
- retire a key;
- check the spend caps;
- rebuild the `.env` layout.

Ask for the key's name, tool, provider and who pays. Never ask for the key itself.

### G-3 Compare names, run by the person
To check the `.env` against the registry, give the person this command to run in their own terminal. It prints key names only, never a value:

`sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env`

Ask them to paste the names back. You don't run it yourself.

## EXECUTION

1. **Add a key:**
   - Add a registry row with name, tool, purpose, "me" as the holder and status "not set up".
   - Write the five label lines plus an empty `NAME=` line for the person to paste into their `.env`, under that tool's group. Use the layout in `references/env_layout.md`.
   - Tell them where the provider creates the key, and to store it in their password manager first.
   - Set the status to active once they confirm it works.
2. **Someone else pays:** the key still lives in the person's own `.env`. Put the payer in the Owner label ("Owner: your account, paid by the company") and keep the person as the holder.
3. **Share a key:** only when the provider can't issue one per person.
   - The account owner shares it through the password manager with named people.
   - Set "Who holds it" to "shared: name, name". Never move it through Slack, email or chat.
4. **Retire a key:**
   - Tell the person to delete its line from their `.env` and revoke it at the provider.
   - Set the status to retired, and keep the row.
5. **Spend caps:** for every key billed by use, confirm that a spend cap and a billing alert are set in the provider's console, and that the cap is written on the Cost label. List any key without one.
6. **Rebuild the layout:** produce the whole labeled `.env` layout from the registry, grouped by tool, with every value empty, for the person to fill in from their password manager.

## Definition of done

- [ ] **D-1 - Every key in the registry carries all five labels in the layout.**
  - **Example:** ANTHROPIC_API_KEY, with lines for Purpose, Phase, Get it from, Cost (billed per use, cap set) and Owner. Anyone reading it knows why the key exists and who pays.
  - **Counter-example:** a bare `OPENAI_API_KEY=` line with no labels. Nobody can tell which tool uses it, what it costs or whose account it is.
  - **Resource:** `references/env_layout.md`

- [ ] **D-2 - No key value appears anywhere you wrote.**
  - **Example:** the registry row reads "OPENAI_API_KEY, OpenAI API, embeddings, me, active", and the layout line ends in `=` with nothing after it.
  - **Counter-example:** a registry row, commit or chat reply that holds part of a key, even its first few characters. Treat that key as exposed and have it revoked.
  - **Resource:** `00_AIOS/systems/key_registry.md`

- [ ] **D-3 - Every key billed by use has a spend cap and an alert recorded.**
  - **Example:** "Cost: billed per use, monthly cap and an alert at half of it set in the provider console." The person knows the most it can cost.
  - **Counter-example:** "Cost: pay as you go", with no cap and no alert. One runaway script can spend without limit before anyone notices.

- [ ] **D-4 - A shared key names its holders and the password manager.**
  - **Example:** "Who holds it: shared: the account owner and one named teammate, through the password manager's shared item." Anyone can see who to ask when it must be revoked.
  - **Counter-example:** "shared with the team", or a key pasted into a Slack channel. Nobody knows who has it, so it can't be revoked cleanly.

- [ ] **D-5 - The names in the registry and the names in the person's `.env` match one to one.**
  - **Example:** the names-only list the person pasted from G-3 matches the active registry rows exactly, and any extra or missing name is shown to them.
  - **Counter-example:** a key in the `.env` that the registry doesn't list. It is tech nobody knows they have, and nobody owns its cost.

## QC gate
Before the person pushes any change to this AIOS, route to `security_check` so a committed secret is caught. If a value was exposed, hand it to the person to revoke at the provider; you don't rotate keys yourself.

No approved gold standard yet.

## OUTPUT
- An updated `00_AIOS/systems/key_registry.md`.
- A block of labeled `.env` lines with empty values for the person to paste.
- A short list of anything still open: a key without a cap, an unlabeled key, or a mismatch between names.

For the reasons behind these rules (own keys, keys in your own `.env` even when someone else pays, safe sharing and cost caps), see `docs/keys_lesson_outline.md`.
