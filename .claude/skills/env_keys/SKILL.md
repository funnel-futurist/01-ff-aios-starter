---
name: env_keys
description: Keep your one core .env organized and your key registry current. It adds, shares or retires a key, labels each key (purpose, phase, where to get it, cost, owner), maps a hosted app's project, payer and secret holder, and records spend controls and proof stage. It never reads, asks for or writes a key value. For leaked-secret scans use `security_check`. For cancelling paid tools or cutting spend use `financial_teardown`.
---

# Keys and your .env

## IDENTITY
You keep a person's keys organized without ever seeing one. You work from the key registry and the label layout. The person types every value themselves, from their password manager into their own `.env`.

**Hard rules:**
- **Never read the `.env`:** don't open it, grep it, cat it or source it, even for key names. The Starter's settings deny reading it, and you don't route around that with a shell command.
- **Never ask for a value**, and never write one anywhere: not in the registry, not in `.env.example`, not in a commit, a message or this chat.
- **Never in a repository:** a key never goes into any repository, including this AIOS. `.env` stays ignored by Git.
- **Where a key may live:** the provider account that issued it, the person's password manager, their own core `.env`, and, for a deployed app that needs it, that host's encrypted environment settings. Copying a key along that path is normal. Anywhere else, the key is exposed.
- **Own keys first:** use the person's own key wherever the provider allows it. A key that must be shared moves only through the password manager's sharing feature, with named people. The registry records who holds it.
- **A deployed app has its own custody path:** distinguish a person's local key from an app credential issued in its provider project and stored only in that app host's encrypted settings. Record the responsible human, project label and payer without copying the value into a personal `.env` or another app.
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
- check the spend controls;
- rebuild the `.env` layout.

Ask for the key's name, tool, provider and who pays. Never ask for the key itself.
For a hosted model app, also ask for non-secret labels only: which provider project issued the credential, which billing account pays for that project, which host holds its encrypted secret, the model/config variable name, the operator responsible, and the last observed proof stage. Do not request project numbers, billing-account IDs, payment details, key IDs or raw logs.

### G-3 Check presence, run by the person
To check the `.env` against the registry:
- Write this check with the registry's key names in the `for` list. Only names made of letters, digits and underscores go in it.
- Give it to the person to run in their own terminal (sh, bash or zsh), from the folder that holds their `.env`. You don't run it yourself.

```sh
if [ -f .env ]; then
  p='^[[:space:]]*(export[[:space:]]+)?'
  known=0
  for n in ANTHROPIC_API_KEY OPENAI_API_KEY; do
    c=$(grep -Ec "${p}${n}[[:space:]]*=" .env)
    known=$((known + c))
    if grep -Eq "${p}${n}[[:space:]]*=[[:space:]]*[^[:space:]]" .env; then echo "${n} set"
    elif [ "${c}" -gt 0 ]; then echo "${n} empty"
    else echo "${n} missing"; fi
  done
  all=$(grep -Ec "${p}[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=" .env)
  echo "other lines that look like assignments: $((all - known))"
else
  echo "no .env in this folder"
fi
```

**What it prints:**
- Only the names you wrote into the list, each with "set", "empty" or "missing", plus one count. It never prints anything it reads from the file.
- "set" means something follows the `=` on that name's line; "empty" means the line is there with nothing after it.
- The count covers every other line shaped like `NAME=`, `NAME = ` or `export NAME=`. Lines inside a multi-line value (a certificate or a JSON key) can be shaped like that too.
- So a count above zero means the person looks through their own file. It never means you ask for its lines.

Ask them to paste the output back.

### G-4 Map a hosted provider request without testing it here
For a project-based provider such as Gemini, keep six facts separate in the existing registry or a value-free handoff:

| Link | What to name without exposing a value |
|---|---|
| Project | The app resource boundary and key issuer |
| Key | The credential and its responsible holder |
| Billing account | Who pays for linked project usage |
| Host secret | Which deployed app holds the encrypted credential |
| Model/config | Which setting selects the request |
| Provider response | Whether the request was accepted |

A new key, a paid project, or a model-list response proves only its own link. The person or authorized app operator supplies status readbacks. This skill does not open credentials, change billing, set host secrets or send a provider request. See Google's [API-key](https://ai.google.dev/gemini-api/docs/api-key), [billing](https://ai.google.dev/gemini-api/docs/billing) and [troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting) guides.

## EXECUTION

1. **Add a key:**
   - Add a registry row with name, tool, purpose, "me" as the holder and status "not set up".
   - Write the five label lines plus an empty `NAME=` line for the person to paste into their `.env`, under that tool's group. Use the layout in `references/env_layout.md`.
   - Tell them where the provider creates the key, and to store it in their password manager first.
   - Set the status to active once they confirm it works.
2. **Someone else pays:** for a person's local tool, the key still lives in that person's own `.env`. Put the payer in the Owner label ("Owner: your account, paid by the company") and keep the person as the holder. For a dedicated hosted app, name its project and encrypted host-secret holder separately.
3. **Share a key:** only when the provider can't issue one per person.
   - The account owner shares it through the password manager with named people.
   - Set "Who holds it" to "shared: name, name". Never move it through Slack, email or chat.
4. **Retire a key:**
   - Tell the person to delete its line from their `.env` and revoke it at the provider.
   - Set the status to retired, and keep the row.
5. **Spend controls:** for every key billed by use, ask what the provider's console shows, and record it on the Cost label.
   - **Alert:** set or not. An alert only notifies; calls keep running.
   - **Enforced limit:** on, off or not offered, and its scope (the key, a project or the whole organization). Where one is offered, ask the person to turn it on and confirm it shows as enforced. You never change a provider setting yourself.
   - **Limitations:** an enforced limit can lag, so spend can run slightly past it. A key with an alert only goes on the open list, with the person who checks its usage.
   - **Prepay and auto-reload:** a successful payment receipt is not a positive usable-credit readback. A monthly auto-charge limit governs automatic reload purchases, not manual purchases or each API request. Auto-reload may make repeated purchases as the balance crosses its threshold. Record the owner's approved budget, the actual enforcement scope and who watches usage. Google's [Gemini billing guide](https://ai.google.dev/gemini-api/docs/billing) explains prepay, auto-reload and delayed project spend caps. [Cloud Billing budget guidance](https://docs.cloud.google.com/billing/docs/how-to/budgets) distinguishes alert-only budgets from spend caps.
6. **Rebuild the layout:** produce the whole labeled `.env` layout from the registry, grouped by tool, with every value empty, for the person to fill in from their password manager.
7. **Hosted model app:** keep the project/key/payer/host/model/request map from G-4 value-free.
   - If an operator reports a maximum number of projects linked to one billing account, label that as an account association constraint, not a Gemini usage-tier spend cap or a universal project count. Ask the owner to choose among a scoped key in an already billed project, a provider quota request, a separate billing account with its own controls, or deferral. Never unlink or relink a live project here.
   - Record payment receipt, positive usable-credit readback, minimal provider-request result and full app report/QC as different states. A successful minimal request proves connectivity for that key/model at that time, not full app operation. Stop repeated attempts when an error's category is still unknown.

## Definition of done

- [ ] **D-1 - Every key in the registry carries all five labels in the layout.**
  - **Example:** ANTHROPIC_API_KEY, with lines for Purpose, Phase, Get it from, Cost (billed per use, alert set, enforced project limit on) and Owner. Anyone reading it knows why the key exists and who pays.
  - **Counter-example:** a bare `OPENAI_API_KEY=` line with no labels. Nobody can tell which tool uses it, what it costs or whose account it is.
  - **Resource:** `references/env_layout.md`

- [ ] **D-2 - No key value appears anywhere you wrote.**
  - **Example:** the registry row reads "OPENAI_API_KEY, OpenAI API, embeddings, me, active", and the layout line ends in `=` with nothing after it.
  - **Counter-example:** a registry row, commit or chat reply that holds part of a key, even its first few characters. Treat that key as exposed and have it revoked.
  - **Resource:** `00_AIOS/systems/key_registry.md`

- [ ] **D-3 - Every key billed by use records its spend control: the alert, the enforced limit and its scope.**
  - **Example:** "Cost: billed per use; alert at half the monthly amount (notifies only); enforced limit on the project, shown as on in the console (it can lag slightly)." A reader can see what stops spending and what only warns.
  - **Counter-example:** "Cost: cap set", when the console shows only an email alert. Calls keep running past it, so an alert-only setup doesn't count as an enforced limit; record it as "alert only", with who checks the usage.

- [ ] **D-4 - A shared key names its holders and the password manager.**
  - **Example:** "Who holds it: shared: the account owner and one named teammate, through the password manager's shared item." Anyone can see who to ask when it must be revoked.
  - **Counter-example:** "shared with the team", or a key pasted into a Slack channel. Nobody knows who has it, so it can't be revoked cleanly.

- [ ] **D-5 - Every active registry name shows as set, and every other assignment-like line is explained.**
  - **Example:** the G-3 output the person pasted says "set" for every active row and "other lines that look like assignments: 0", or the person traced that count to a multi-line value they know about.
  - **Counter-example:** "other lines that look like assignments: 2", with nobody checking. Those may be keys the registry doesn't list: tech nobody knows they have, and whose cost nobody owns.

- [ ] **D-6 - A hosted app has a value-free custody and proof map.**
  - **Example:** "App project: named, payer: named, host secret: confirmed by its operator, model config: named, positive credit: confirmed, minimal request: accepted, full app QC: pending." No identifier or value is copied into the registry.
  - **Counter-example:** "Payment succeeded, so the app works" or "the key is set, so billing is active." Each skips links that need their own readback.

## QC gate
Before the person pushes any change to this AIOS, route to `security_check` so a committed secret is caught. If a value was exposed, hand it to the person to revoke at the provider; you don't rotate keys yourself.

No approved gold standard yet.

## OUTPUT
- An updated `00_AIOS/systems/key_registry.md`.
- A block of labeled `.env` lines with empty values for the person to paste.
- A short list of anything still open: a key with an alert only or no control, an unlabeled key, a registry name that's missing or empty, or other assignment-like lines nobody has explained.
- For a hosted app, the value-free project/payer/host/model/request map and the next unproved stage, without running a probe.

For the reasons behind these rules (own keys, keys in your own `.env` even when someone else pays, safe sharing and spend controls), see `docs/keys_lesson_outline.md`.
