# Lesson outline: your keys

The outline for the keys training. A Portal lesson can be cut from it section by section. Each section gives the point to land, why it matters, and one thing the learner does.

**Learner outcome:** by the end, the learner:
- has their own core `.env`, with every key labeled;
- has a key registry that matches it;
- knows how to share a key safely;
- has a spend cap on every key that bills by use.

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
- **Cost:** free, subscription or billed per use, and the cap.
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

**If a key was pasted anywhere else:** revoke it at the provider and make a new one.

## 6. Keeping cost under control

**Point:** before you first use a key that bills by use:
- set a spend cap and a billing alert in the provider's console;
- write the cap on its Cost label.

Keep one key per tool, so each tool's spend shows on its own.

**Why:** a looping script or a leaked key can spend without limit. A cap turns that into an alert and a stopped bill. Knowing which key belongs to which tool tells you what to switch off.

**Do:** find every key billed by use in your registry, confirm its cap and alert, and fix any without one.

## 7. Your key registry

**Point:** `00_AIOS/systems/key_registry.md` lists every key's name, tool, purpose, who holds it and its status. It never holds a value. It's how you always know exactly what tech you have. The connectors on your Claude account may be added there later.

**Do:**
- Run `/env_keys` to add your keys to the registry.
- Paste the names-only list it gives you a command for, and fix any mismatch between the registry and your `.env`.

## Check for understanding

1. Your company pays for a tool. Where does your key for it live, and what does its Owner label say?
2. A teammate asks for "the key" in Slack. What do you do instead?
3. Name two reasons to use your own key rather than a shared one.
4. A key that bills by use has no cap. What two things do you set, and where do you write the cap?
5. You find a key in your `.env` that the registry doesn't list. What do you do?
