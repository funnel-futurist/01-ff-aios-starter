# Create a Supabase access token

**What it's for:** it lets the Supabase command-line tool, or an agent, act on your Supabase projects without your password. Give it only the access the job needs. A token can never do more than your own role allows. About 3 minutes.

**Where:** https://supabase.com/dashboard/account/tokens

## Steps
1. Sign in at supabase.com and open the address above. (From the dashboard: your profile icon, top right, then **Account preferences**, then **Access Tokens**.)
2. Choose to generate a new token.
3. Name it for its one job, for example `cli-<job>-<your-name>`.
4. **Scope it.** Choose the one project it's for, and only the permissions the person asking named. For example, a token that only lists projects needs just **Projects (account-wide)** with **Read**. Supabase recommends scoped tokens "for everything, especially AI agents". A scoped token starts with `sbp_fc`.
5. Confirm, then copy the token. Copy it before you leave the page.
6. Store it straight away, in your password manager, or as the line `SUPABASE_ACCESS_TOKEN=...` in your workspace's `.env` (which Git never uploads). The Supabase CLI reads that variable. Don't sign the CLI in with plain `supabase login`: its browser flow creates a classic token with your account's full access.

## It worked when
The token appears in your list of access tokens with the name you gave it, and without a **Legacy** badge. That badge marks a classic, full-access token.

## Send back
The token's **name**, its project, and its permissions. **Never the token itself**: not in chat, a document, a screenshot or a commit. If an agent needs it, you put it in `.env` yourself.

## If it goes wrong
- You left the page before copying: revoke that token and generate a new one.
- You think it leaked: revoke it at once, then make a new one.

## Video and checks
- **Video:** [How to Create a Personal Access Token in Supabase](https://www.youtube.com/watch?v=0XWUt89hpO0) (Shortcut Academy, 2 min 46 s). Its transcript was checked on 2026-10-01: it shows generating, copying, storing and revoking a token, but **not step 4 (scoping)**. Do step 4 anyway.
- **Steps checked against:**
  - Supabase Docs, "Personal Access Tokens" (https://supabase.com/docs/guides/platform/personal-access-tokens);
  - "supabase login" (https://supabase.com/docs/reference/cli/supabase-login).

  Both read 2026-10-14.
- **Not stated in those docs:** the dashboard menu path in step 1, that the token is shown only once, and where the revoke control sits. They come from the dashboard as seen on 2026-10-01.
