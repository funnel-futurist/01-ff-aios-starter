WHERE THIS SITS

Stage: technical base
Phase: Foundation
Consumes: a named tool or app, a provider account and an approved spend owner
Produces: a value-free key custody map and an honest next proof step
Metric: provider-backed apps with a named payer, credential holder and recorded proof stage
Does not solve: provider eligibility, full app quality checks or production acceptance
Feeds back into: none, because this is part of the operating base

# Lesson outline: your keys

The outline for the keys training. A Portal lesson can be cut from it section by section. Each section gives the point to land, why it matters, and one thing the learner does.

**Learner outcome:** by the end, the learner:
- has their own core `.env`, with every key labeled;
- has a key registry that matches it;
- knows how to share a key safely;
- knows, for every key that bills by use, whether it has an alert or an enforced limit, and what that limit covers.
- can name the project, payer, credential, host, model and request as separate links, and say which link has actually been proved.

**Rules this teaches:**
- `00_AIOS/systems/key_registry.md` (the registry);
- `.env.example` (the label layout);
- the `env_keys` skill.

## 1. Why each person has their own keys

**Point:** a key is a credential. Use your own for personal work wherever the provider allows it, so custody and revocation are clear. A deployed app may have a dedicated credential in its own project.

**Why:**
- **Revoke one, not everyone:** when a laptop is lost or someone leaves, you revoke one person's key and nobody else is interrupted.
- **Clear custody:** a person's key has a named holder. A hosted app has a named operator and project. Provider usage and cost may still be grouped at the project or billing-account level.

**Do:** list the tools you use, and mark each one "my own key", "shared today" or "dedicated app key".

## 2. Your keys live in your own .env, even when someone else pays

**Point:** who pays and who holds the key are separate questions. So are the provider project and the host that runs the app.

**Why:**
- The company may pay for a personal tool, but the key you use is still issued to you and kept in your `.env`.
- A dedicated app key is issued in that app's provider project and supplied only to its specific host through encrypted settings. The responsible person is recorded without copying the app key into their personal `.env`.
- The Owner label records the payer, so cost stays visible without anyone handing around one master key.
- When you move on, your key is revoked and the company's account stays intact.

**Do:** for each key, write the Owner label: your account, and who pays if it isn't you. For an app, also name its project and encrypted host-secret holder in the value-free registry.

## 3. One core .env, every key labeled

**Point:** one file per person, and five labels per key.
- **Purpose:** what it's for and which tool.
- **Phase:** the portal phase that first needs it.
- **Get it from:** the provider page.
- **Cost:** free, subscription or billed per use, and its spend control (an alert or an enforced limit).
- **Owner:** whose account it is.

**Why:** an unlabeled key is a mystery charge and a mystery risk. Labels let anyone answer "what is this, and can I turn it off?"

**Do:** copy `.env.example` to `.env`, fill in your values from your password manager, and label every key.

## 4. Keys never go in a repository

**Point:** not in any repo, your own AIOS instance included. `.gitignore` blocks `.env`, and Claude Code can't read it.

**Where a key may live:**
- the provider account that issued it;
- your password manager;
- your core `.env`;
- for a deployed app, the host's encrypted settings.

**Never:** Slack, email, a Claude chat, a document, a screenshot or a commit.

**Why:** a key in a repository is a key in every copy and every backup of that repository, forever. Deleting it later doesn't remove it from history.

**Do:** run `/security_check` before you push.

## 5. Sharing a key safely, when you must

**Point:** some providers allow only one key per account. Then the account owner shares that key through the password manager's sharing feature, with named people only.

**Why:** the password manager keeps a list of who has access and can take it back. A message thread can do neither.

**Do:** for each shared key, record "shared: name, name" in the registry's "Who holds it" column.

**If a key was pasted outside the four places in section 4:** revoke it at the provider and make a new one.

## 6. Keeping cost under control

**Point:** alerts, enforced spend caps and payment reload settings do different jobs.
- **An alert** tells you spend passed an amount. Calls keep running.
- **An enforced limit** aims to stop or reject usage once the provider records enough spend to reach it. It may cover one key, a project or the whole organization. Some providers make you switch enforcement on. Others don't offer it, and accounting delay can allow overage.

Before you first use a key that bills by use:
- set an alert;
- turn on an enforced limit where the provider offers one, and confirm in the console that it shows as enforced and what it covers;
- write both on the Cost label.

Keep separate credentials where the provider allows it, so a tool can be revoked without disrupting another. Check the provider's billing view for cost attribution: several keys can share one project's cap and one billing account's tier limit.

**The limits of the limits:** an enforced limit can lag, so spend can run slightly past it. A key with an alert only has no ceiling at all, so someone has to watch its usage.

**Why:** a looping script or a leaked key can spend fast. An alert tells you; an enforced limit bounds the damage, close to its amount. Knowing which key belongs to which tool tells you what to switch off.

**Do:** for each key billed by use, record its alert, and whether an enforced limit is on and what it covers. List every alert-only key with the person who checks its usage.

**Google example:** a maximum number of projects linked to one billing account is an account association constraint. It is not the Gemini usage-tier monthly spend cap, and an observed two-project error does not establish a universal two-project rule. The owner can assess a scoped key in an already billed project, ask the provider for a quota change, open a separately controlled billing account, or defer the app. Unlinking a live project changes its billing and is not a cleanup shortcut. [Google's Cloud Billing guide](https://docs.cloud.google.com/billing/docs/how-to/modify-project) explains the project-to-billing-account relationship. [Gemini billing](https://ai.google.dev/gemini-api/docs/billing) explains tier and project spend caps.

**Prepay is another check:** a successful payment receipt records the purchase, while the usable-credit balance needs its own positive readback. A monthly auto-charge limit applies to automatic reload purchases, not manual purchases or a guaranteed per-request cutoff. An alert only notifies, and even a project spend cap may lag, so the owner approves a budget and names who monitors actual usage. See [Gemini prepay and auto-reload](https://ai.google.dev/gemini-api/docs/billing) and [Google Cloud budget alerts](https://docs.cloud.google.com/billing/docs/how-to/budgets).

## 7. Your key registry

**Point:** `00_AIOS/systems/key_registry.md` lists every key's name, tool, purpose, who holds it and its status. It never holds a value. It's how you always know exactly what tech you have. The connectors on your Claude account may be added there later.

**Do:**
- Run `/env_keys` to add your keys to the registry.
- Run the presence check it writes for you, in your own terminal, and paste back what it prints: "set", "empty" or "missing" for each registry name, plus a count of other lines. Fix anything missing, and explain any count above zero.

## 8. Prove each link before calling the app ready

**Point:** for a project-based provider such as Gemini, an app needs six links: its project, a credential issued there, the billing payer and usable funds, the selected host's encrypted secret, the model/config setting, and an accepted request. Each link has its own evidence. [Google's API-key guide](https://ai.google.dev/gemini-api/docs/api-key) ties Gemini keys to projects. Its [troubleshooting guide](https://ai.google.dev/gemini-api/docs/troubleshooting) says a successful models-list response does not establish inference eligibility.

**Why:** an empty host variable fails before contacting the provider. A payment receipt can precede usable credit. An HTTP error with discarded details cannot identify its cause. One minimal model response proves that key, model and request worked at that moment. The full app still needs its report, quality checks and spend readback. In the source case, a later positive balance and corrected host configuration preceded one passing minimal request. That was connectivity evidence, not a completed app or lesson.

**Do:** record the strongest observed stage without a secret or account identifier: project linked, credit available, host secret confirmed by its operator, minimal response accepted, or full app QC verified. Stop repeated calls until a failed stage is diagnosed. The `env_keys` skill records this value-free map without running provider tests or changing billing.

## Check for understanding

1. Your company pays for a tool. Where does your key for it live, and what does its Owner label say?
2. A teammate asks for "the key" in Slack. What do you do instead?
3. Name two reasons to use your own key rather than a shared one.
4. A key that bills by use has only an email alert. Is its spend capped? What do you check in the console, and what do you write on its Cost label?
5. You find a key in your `.env` that the registry doesn't list. What do you do?

**Synthetic case:** A fictional company has two projects already linked to a billed account. A third app project receives a linked-project maximum error. The owner starts a separate Prepay account and receives a successful payment receipt, but the project still shows no usable credits. Later, the credit balance is positive and one minimal model request succeeds. Where should the app credential be held, what choices can the owner make about the project link, what has each readback proved, and what remains before calling the full app ready? Name the alert, auto-reload and enforced-cap checks without submitting a real key or making a provider call.

**Expected reasoning:** keep the app credential in its project and its exact host's encrypted secret, with a named payer and operator. Do not silently unlink either existing project. Separate the linked-project constraint from tier spending, then consider a scoped existing project, provider quota request, separate controlled account or deferral. Treat the receipt as payment evidence, positive balance as usable funds, and the minimal response as connectivity only. Full report/QC and observed spend remain. An alert and auto-reload charge limit are not per-request spending cutoffs. Record any enforced cap's scope and monitoring owner.
