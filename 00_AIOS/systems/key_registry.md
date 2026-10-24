# Key registry

Every key you hold, one row each, so you always know exactly what tech you have.

- **Names only:** write the *name* of a key here, never its value.
- **Where values live:** the provider account that issued the key, your password manager, your own core `.env` (never committed) and, for a deployed app that needs it, that host's encrypted settings. Anywhere else, the key is exposed.
- **Labels:** the five labels for each key (purpose, phase, where to get it, cost, owner) sit above it in your `.env`.
- **Tools:** `connections.md` in this folder lists the tools themselves.
- **Upkeep:** run `/env_keys` to add, share or retire a key and keep this file current.

| Key name | Tool | Purpose | Who holds it | Status |
|---|---|---|---|---|
| ANTHROPIC_API_KEY | Claude API | Only for API billing or the CI reviewer; a Claude subscription needs no key | | not set up |
| OPENAI_API_KEY | OpenAI API | Only for embeddings or Whisper transcription | | not set up |
| FF_CORE_KEY | FF Intelligence | Only for an FF Intelligence capability your organization is entitled to use | | not set up |
| GOOGLE_CLIENT_ID | Google Workspace API | Only if you connect Google Workspace through its API | | not set up |
| GOOGLE_CLIENT_SECRET | Google Workspace API | Only if you connect Google Workspace through its API | | not set up |
| GOOGLE_REFRESH_TOKEN | Google Workspace API | Only if you connect Google Workspace through its API | | not set up |

**Who holds it:**
- **"me":** your own key, which can be revoked on its own. Use this wherever the provider allows it.
- **"shared: name, name":** a key the account owner shares through the password manager, with exactly those people.
- Never put a person's key in Slack, email or chat.

**Status:**
- **active:** the key is in use.
- **not set up:** listed but not created.
- **retired:** deleted from your `.env` and revoked at the provider. Keep the row so the history stays clear.

**Later:** the connectors on each Claude account may be added here too. They hold no key in your `.env`, but they're still tech you have.
