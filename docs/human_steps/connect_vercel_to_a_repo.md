# Connect Vercel to a GitHub repository

**What it's for:** your site deploys from the repository's `main` branch on every merge, with a preview for every pull request, instead of from someone's laptop. About 10 minutes.

**You need:**
- a Vercel account in your company's Vercel team. If the repository is private and belongs to a GitHub organization, that team must be on a paid plan: Vercel can't deploy one to a Hobby team.
- on GitHub, to be an **owner** of the organization, or a **member** with access to the repository. An outside collaborator can't import or connect it. On a personal account, only the repository's owner can.

## A new Vercel project from a repository
1. Open https://vercel.com/new.
2. In the list of repositories, choose your GitHub account or organization from the dropdown at the top left of the list.
   - The repository isn't listed? Click **Configure GitHub App**, add the repository to the ones Vercel can access, save, then return to the import screen.
3. Click **Import** next to the repository.
4. Name the project with the repository's exact name.
5. **Root Directory:** choose the folder that holds the site. If the site is the whole repository, leave it at the top level.
6. Leave the framework preset and build settings Vercel detected, unless the person asking told you otherwise.
7. Click **Deploy**.

## An existing project that isn't connected yet
1. Open the project in Vercel, then **Settings > Git**.
2. Under **Connected Git Repository**, connect the repository.
3. **Settings > Build and Deployment > Root Directory:** enter the folder path, then click **Save**. This applies from the next deployment.

## It worked when
- the first deployment finishes and its page opens;
- the next pull request gets a Vercel commit status and a Vercel bot comment with its preview link.

## Send back
- the Vercel project name and its address;
- the Root Directory you set;
- the repository it's connected to.

## If it goes wrong
The repository doesn't appear in the import list. Either the Vercel GitHub App hasn't been given that repository (fix it with **Configure GitHub App**), or you're an outside collaborator or a member without access to it. Ask a GitHub organization owner: organization repositories often need an owner to approve or install the Vercel app.

Commits from someone with no access to the Vercel project won't deploy from a private repository, so give each person who commits access to the project.

## Video and checks
- **Video: still to find.** On 2026-10-01 YouTube refused the transcript requests for every candidate, so none could be checked. The steps stand on the official docs until a checked video is added.
- **Steps checked against:**
  - Vercel Docs, "Deploying Git Repositories with Vercel" (https://vercel.com/docs/git);
  - "Deploying GitHub Projects with Vercel" (https://vercel.com/docs/git/vercel-for-github);
  - "Configuring a Build", for Root Directory (https://vercel.com/docs/builds/configure-a-build);
  - Vercel's guide "How to fix 'unable to find your GitHub repository' on Vercel" (https://vercel.com/kb/guide/unable-to-find-github-repository).

  All read 2026-10-14.
- **Not stated in those docs:** the label of the project-name field, and the edit control for Root Directory during import.
