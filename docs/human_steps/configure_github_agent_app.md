# Give your agent App the access its work needs

**What it's for:** your company's agent can prepare changes and inspect the evidence needed before a merge. Missing read permissions can make a valid check look unavailable. Broad write permissions can also let a token do more than the job requires. Choose the capabilities once, then verify what the installation actually received.

**Who acts:** the owner of your company's GitHub App and an owner of the organization where it is installed. An authorized operator can do supported steps; use an owner only where GitHub requires that account. A private App owned by the client organization keeps its credentials and installation separate from other clients.

**Where:** open your organization's GitHub **Settings**, then **Developer settings > GitHub Apps** to configure its App. Open **Settings > GitHub Apps > Installed GitHub Apps** to configure the installation. For an App owned by a personal account, use that account's Developer settings instead. Use your own organization and App, not a provider's internal identifiers.

## Choose the profile

Start with **Builder and merge checks**. Add only the options your operator will use. An existing App may already publish checks: inspect that use before reducing its permissions.

| Permission | Builder and merge checks | Add when needed |
|---|---|---|
| Metadata | Read | No extra access |
| Contents | Read and write | Prepare commits and branches; existing merge rules still apply |
| Pull requests | Read and write | Open PRs, comments and reviews; a review must still come from an eligible identity |
| Issues | Read | Read and write if your agent records claims and progress in issues |
| Commit statuses | Read | Write only if this App publishes commit statuses |
| Checks | Read | Write only if this App publishes check runs |
| Actions | Read | **CI operator: Read and write**, to dispatch or control authorized workflow runs |
| Administration | Read | Inspect repository protection; no write access by default |
| Deployments | Read | Write only if this App publishes deployment records |
| Workflows | No access | **Workflow author: Read and write**, to change workflow files |
| Organization Members | No access | **Team code owners: Read**, to verify team membership and repository access |

A full operating profile adds issue coordination, CI operator, workflow author and team code-owner reads. Check publishing is still optional. Members access covers organization membership, not just the selected repositories; explain that scope before accepting it. Individual code owners do not require that team option.

Do not add Administration write, Members write, secret management, environment write, or ruleset bypass as defaults. Use a separate, concrete request if a future job needs one of them.

**Permission is not execution authority.** Actions write makes workflow dispatch possible; it does not authorize every workflow, paid run or deployment. Contents and Pull requests write do not waive reviews, code-owner requirements or release conditions. Workflows write changes workflow files; Actions write controls runs. They are different capabilities.

## Configure and accept

1. Identify the client-owned App and the exact repositories it needs. If none exists, register one under the client's account or organization using GitHub's [registration instructions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app). Choose its private key storage and authentication owner before using it. Do not put a private key in the repository or chat.
2. In the App's **Permissions & events**, set the selected repository and organization permissions from the table. Save the changes. Subscribe only to events the implementation actually handles; do not add hooks or event processing just for this setup.
3. Install the App on **Only select repositories**, selecting this client's intended repositories. Keep separate clients' installations, keys and token caches separate.
4. If the App was already installed, open its pending permission request and accept the selected changes as the installation owner. Saving App permissions and accepting installation permissions are separate steps. Do not interpret “already installed” as acceptance of the new permissions.
5. Have the existing authentication helper mint a fresh installation token for that installation and repository selection. Discard its stale cached token through the helper's supported refresh route. Narrow token permissions to the current job where supported; never print the token.
6. Ask the operator to perform the readback below. Do not dispatch a workflow or change a secret merely to test whether access works.

## It worked when

The operator records these separately, with no token, private key or secret value:

- The App's requested profile, the installation's accepted profile, and its selected repositories.
- The newly issued token's installation, repository selection and granted permission names.
- Successful reads of a private target repository's content, PR reviews, check runs, combined commit statuses, Actions runs and repository protection/rules. A successful check-run read does not prove commit-status access.
- For team code owners, the team's visibility, active membership and explicit repository write access. A team member's separate personal access does not prove the team qualifies as a code owner.
- Any capability not tested, and the next owner for that test. Read-only checks cannot prove an optional write action worked. Test writes only through an already-authorized, bounded job.

Use the same executing identity for the readback that the agent will use for its work. A successful read through a founder's personal token does not verify the App token.

## Send back

“App profile: `<selected options>`; installation accepted: `<time>`; selected repositories: `<names>`; fresh App-token readback: `<passed capabilities>`; unavailable: `<capability and status>`; next owner: `<role>`.” Keep sensitive repository names in the client's own private record. Record no credentials.

## If a read is still refused

A403 is not success, even after the owner accepted the request. Check the App, installation, selected repository, accepted permissions and token issuance time. Refresh through the existing helper if it reused an older token. Do not switch to a more privileged identity to conceal the failed App check. Missing or unreadable approval evidence must hold the affected merge; it must not be treated as approval.

To remove an unused capability, first check whether an active job depends on it, then update the App and installation through the same owner route. Suspend or uninstall the App to stop its access if needed. Neither action reverses changes the App already made; use the affected system's recovery procedure for those.

## Video and checks

- **Video:** still to find; no transcript verified.
- **Steps checked against:** official GitHub documentation, read 2026-10-30:
- [Choose App permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app) and [endpoint permission reference](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps).
- [Accept updated permissions](https://docs.github.com/en/apps/using-github-apps/approving-updated-permissions-for-a-github-app).
- [Workflow dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event), [team membership](https://docs.github.com/en/rest/teams/members), and [code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

The profile choices, client separation, readback receipt and action-authorization rules are this workspace's operating guidance, not a claim that GitHub enforces every step. Settings labels may differ by account role. No live installation is proved by reading this card.
