# Lesson outline: your keys

The outline for the keys training. A Portal lesson can be cut from it section by section. Each section gives the point to land, why it matters, and one thing the learner does.

**Learner outcome:** by the end, the learner:
- has their own core `.env`, with every key labeled;
- has a key registry that matches it;
- knows how to share a key safely;
- knows, for every key that bills by use, whether it has an alert or an enforced limit, and what that limit covers.

**Rules this teaches:**
- `00_AIOS/systems/key_registry.md` (the registry);
- `.env.example` (the label layout);
- the `env_keys` skill.

## 1. Why each person has their own keys

**Point:** a key is a signature. Use your own wherever the provider allows it.

**Why:**
- **Revoke one, not everyone:** when a laptop is lost or someone leaves, you revoke one person's key and nobody else is interrupted.
- **Clear ownership:** every call made with a key is clearly that person's, so usage, cost and mistakes trace to one place.

**Do:** list the tools you use, and mark each one "my own key" or "shared today".

## 2. Your keys live in your own .env, even when someone else pays

**Point:** who pays and who holds the key are separate questions.

**Why:**
- The company may pay for a tool, but the key you use is still issued to you and kept in your `.env`.
- The Owner label records the payer, so cost stays visible without anyone handing around one master key.
- When you move on, your key is revoked and the company's account stays intact.

**Do:** for each key, write the Owner label: your account, and who pays if it isn't you.

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

**Point:** there are two controls, and they do different jobs.
- **An alert** tells you spend passed an amount. Calls keep running.
- **An enforced limit** makes the provider stop or reject calls once spend reaches it. It may cover one key, a project or the whole organization. Some providers make you switch enforcement on; some don't offer it.

Before you first use a key that bills by use:
- set an alert;
- turn on an enforced limit where the provider offers one, and confirm in the console that it shows as enforced and what it covers;
- write both on the Cost label.

Keep one key per tool, so each tool's spend shows on its own.

**The limits of the limits:** an enforced limit can lag, so spend can run slightly past it. A key with an alert only has no ceiling at all, so someone has to watch its usage.

**Why:** a looping script or a leaked key can spend fast. An alert tells you; an enforced limit bounds the damage, close to its amount. Knowing which key belongs to which tool tells you what to switch off.

**Do:** for each key billed by use, record its alert, and whether an enforced limit is on and what it covers. List every alert-only key with the person who checks its usage.

## 7. Your key registry

**Point:** `00_AIOS/systems/key_registry.md` lists every key's name, tool, purpose, who holds it and its status. It never holds a value. It's how you always know exactly what tech you have. The connectors on your Claude account may be added there later.

**Do:**
- Run `/env_keys` to add your keys to the registry.
- Run the presence check it writes for you, in your own terminal, and paste back what it prints: "set", "empty" or "missing" for each registry name, plus a count of other lines. Fix anything missing, and explain any count above zero.

## Check for understanding

1. Your company pays for a tool. Where does your key for it live, and what does its Owner label say?
2. A teammate asks for "the key" in Slack. What do you do instead?
3. Name two reasons to use your own key rather than a shared one.
4. A key that bills by use has only an email alert. Is its spend capped? What do you check in the console, and what do you write on its Cost label?
5. You find a key in your `.env` that the registry doesn't list. What do you do?
