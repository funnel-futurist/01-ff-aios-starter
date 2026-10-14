# Remove someone from your GitHub organization

**What it's for:** when someone leaves, or no longer needs access, they lose access to the organization's private repositories at once (see the exceptions below). About 2 minutes. You must be an **owner** of the organization.

**Where:** `https://github.com/orgs/<your-org>/people`

## Before you do it, know this
- If your organization is on GitHub Enterprise Cloud and membership is managed by SCIM provisioning or by IdP groups, don't remove them here. Remove them from the GitHub application in your identity provider, and from any IdP groups linked to teams with access to the organization.
- Send them a leaving checklist so they delete confidential files. GitHub's example is "Prepare for job change".
- They keep any copies already on their own computer, though they can no longer sync them with your repositories. Removal stops future access; it can't take back what was downloaded.

## Steps
1. Sign in to GitHub. Click your profile picture (top right), then **Organizations**.
2. Click your organization's name.
3. Under your organization name, click **People**.
4. Tick the box next to the person (or people) to remove.
5. Above the list of members, open the **X members selected...** menu and choose **Remove from organization**.
6. Review who will be removed, then click **Remove members**.

## It worked when
The person is no longer in the **People** list.

## What removal does and doesn't do
- They lose access to private forks of your organization's private repositories.
- If a private repository was forked into another organization, that organization controls the fork, so they may keep access to it.
- On Enterprise Cloud, someone who is still in another organization of the same enterprise keeps access to repositories with internal visibility.
- GitHub saves their membership data for three months. If you invite them back within that time, you can restore it, along with any private forks they owned of your repositories.
- Invitations they sent that nobody has accepted yet are cancelled.
- With volume license billing, your paid license count doesn't go down by itself.
- Change any shared password or key they knew. Removal doesn't do that.

## Send back
"Removed `<their GitHub username>` from `<org>` on `<date>`", plus a list of any shared secrets you changed.

## Video and checks
- **Video: still to find.** No video found on 2026-10-01 showed these organization-removal steps; the closest ones remove a collaborator from a single repository, which is a different action. The steps stand on the official docs until a checked video is added.
- **Steps checked against:** GitHub Docs, "Removing a member from your organization" (https://docs.github.com/en/organizations/managing-membership-in-your-organization/removing-a-member-from-your-organization), read 2026-10-14.
- **Not stated on that page:** the "It worked when" line and the advice to change shared secrets. Both are our own, not GitHub's.
