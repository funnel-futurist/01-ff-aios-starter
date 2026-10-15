# Move a Vercel site to its 3.0 folder

**What it's for:** Starter 3.0's upgrade moves the old numbered folders to new domain folders. A website kept in an old folder (usually `11_Projects/<site>/`) moves to `02_Team_Ops/projects/<site>/`. If its Vercel project still builds the old folder, the next deploy fails, because that folder is gone. So the upgrade refuses to move the site until the project's **Root Directory** names the new folder, and it checks this with Vercel itself, read-only, using your Vercel token. About 20 minutes, in one sitting.

**You need:**
- to be a founder: only a founder can run an upgrade;
- an up-to-date clone of `ff-aios-starter` next to your workspace. The upgrade runs from there, not from inside your workspace;
- your workspace with everything committed. The upgrade refuses uncommitted work;
- access to the site's project in Vercel.

## Steps
1. **See what moves.** In the Starter clone, run `git pull`, then:
   ```
   python3 scripts/aios/aios.py upgrade --release releases/starter-3.0.0.json --target ../my-workspace --dry-run
   ```
   (Use your workspace's path in place of `../my-workspace`.) It writes nothing. For each website folder it prints where it moves, for example `11_Projects/<site> (moves to 02_Team_Ops/projects/<site>)`. That new folder is the Root Directory you'll set. It then stops at **BLOCKED** and asks for a Vercel token. That's expected at this point.
2. **Make a Vercel token for this check.** Open https://vercel.com/account/tokens (the **Account Tokens** page in your account settings).
   - Name it for its one job, for example `aios-3-0-upgrade-check`.
   - Open the **Scope** dropdown, select the team that owns the project, then **All Projects**. Not a single project: the upgrade searches the whole team for every project that builds your repository. If the project isn't in a team, only **Full Account** reaches it.
   - Choose the shortest expiration offered, then select **Create**.
   - Copy the token before you leave the page. Vercel shows it only once. Don't paste it into a chat, a document or a file. The upgrade only reads with it.
3. **Point the project at the new folder.** In Vercel, open the project, then **Settings**, then **Build and Deployment**. Scroll down to **Root Directory**, enter the new path exactly as the dry run printed it, and click **Save**. If the old Root Directory was a folder inside the site folder, keep its ending: `11_Projects/<site>/app` becomes `02_Team_Ops/projects/<site>/app`.

   Vercel applies this on the next deployment, and until the upgrade is merged that folder doesn't exist in your repository. A push in between, to `main` or any other branch, would try to build a folder that isn't there yet. So do steps 3 to 5 in one sitting.
4. **Run the upgrade on a branch.** In your workspace, start a branch: `git switch -c starter-3-0`. Then, in the Starter clone, run:
   ```
   read -s VERCEL_TOKEN
   ```
   Paste the token and press **Enter**. Nothing shows as you paste. Then run:
   ```
   VERCEL_TOKEN="$VERCEL_TOKEN" python3 scripts/aios/aios.py upgrade --release releases/starter-3.0.0.json --target ../my-workspace
   unset VERCEL_TOKEN
   ```
   The token goes to that one command only. `read -s` keeps it off the screen and out of your terminal's history, and the upgrade never prints it or saves it. The upgrade asks Vercel before it moves anything. If a project still builds the old folder, it refuses, changes nothing, and prints the project and the exact path to set: fix it as in step 3, then run this step again.
5. **Commit, check the preview, merge.** In your workspace: `git add -A`, then `git commit -m "Upgrade to Starter 3.0"`. Push the branch and open a pull request. Vercel builds a preview for it, now from the new folder, and comments on the pull request with the link. Open the preview and check the site loads. Then merge.
6. **Delete the token.** On the Account Tokens page (https://vercel.com/account/tokens), delete the token you made in step 2. With the Vercel CLI instead: `vercel tokens ls` to find its ID, then `vercel tokens rm <token-id>`.

If the upgrade also printed a `NEXT:` line about founder review, do [Restore founder review after the 3.0 move](restore_founder_review.md) next.

## A repository that isn't on Vercel
Every 3.0 upgrade checks Vercel, because it can't tell a website from its files alone. If nothing in this repository is deployed by Vercel, there's nothing to check: add `--no-vercel` to the upgrade command instead of giving a token. The upgrade records that you said so. It refuses the flag if Vercel's own files (`vercel.json`, or a `.vercel/` folder) are in the folders it moves, because then the repository is on Vercel.

If a site is hosted somewhere else, update that host's folder setting after the upgrade, before your next deploy.

## It worked when
- the upgrade prints `website:  11_Projects/<site>: verified. Vercel project <name> builds 02_Team_Ops/projects/<site>/`;
- the pull request's Vercel preview builds and opens;
- after merging, the next production deployment builds from the new folder and the site opens at its usual address.

## Send back
- the Vercel project name;
- the Root Directory now set;
- the pull request's preview link;
- the upgrade's `website:` line.

Never the token.

## If it goes wrong
- **The upgrade refuses and names a project that "still builds" an old folder.** That project's Root Directory still names the old folder. It may be a second project you'd forgotten builds the same repository. Set its Root Directory as in step 3 (the refusal prints the exact path), then run step 4 again. Nothing was moved.
- **The refusal says "Vercel answered 401", "403" or "404", or that nothing was verified.** The token is wrong, expired, or can't see the team that owns the project. Make a new token with **Scope** set to that team and **All Projects** (step 2), delete the old one, and run step 4 again.
- **The refusal says "this token could read no Vercel scope".** A token scoped to one team may not be allowed to list your teams. Run step 4 again with the team's ID too: `VERCEL_TEAM_ID=team_... VERCEL_TOKEN="$VERCEL_TOKEN" python3 ...` (the ID starts with `team_`).
- **Vercel won't let you pick the team for the token.** Some teams require two-factor sign-in or SAML before you can create a token scoped to them. The dashboard tells you when you select the team.
- **Deploys fail after step 3 but before you merge.** Vercel is building a folder your repository doesn't have yet. Finish steps 4 and 5 and merge, or set the Root Directory back to the old folder until you're ready.

## Video and checks
- **Video: still to find.** This card was written on 2026-10-14 and no video has been checked against it yet. The steps stand on the official docs until a checked video is added.
- **Steps checked against:**
  - Vercel Docs, "Configuring a Build", for Root Directory (https://vercel.com/docs/builds/configure-a-build);
  - Vercel's guide "How do I use a Vercel API Access Token?", for creating, scoping, reading in and deleting the token (https://vercel.com/kb/guide/how-do-i-use-a-vercel-api-access-token);
  - "Deploying GitHub Projects with Vercel", for the pull-request preview (https://vercel.com/docs/git/vercel-for-github).

  All read 2026-10-14.
- **Not stated in those docs:** which expiration choices Vercel offers (the guide only says to choose one), the label of the control that deletes a token on the Account Tokens page, and whether a Root Directory may start with `/`. The `git` and upgrade commands are ours, written for a Mac or Linux terminal. Vercel's guide reads the token with `read -s` and then exports it; this card passes it to the one command instead.
