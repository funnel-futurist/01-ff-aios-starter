# Evergreen methods and your private AIOS

## The intended arrangement

Evergreen is the shared repository of reusable FF intelligence. Your AIOS is the private company workspace. Your own assistant reads an authorized method from Evergreen, uses your permitted company context and produces a reviewable result here.

The public Starter contains generic workspace instructions and templates. It does not contain the five-brain source in FF's private Evergreen repository (shared with entitled clients), grant access to it or establish a working connector. The planned source structure is listed in [the company reference](../../00_AIOS/evergreen.json). Until the actual source and permissions are verified, report it as planned.

## Establish the connection

1. Verify the actual Evergreen repository and its published entry paths with the source owner.
2. Verify the person's authorized entitlement through the owning business process. This JSON file is not an entitlement system.
3. Connect that person's existing assistant integration to the authorized repositories. Establish Read access to Evergreen separately from the ability to propose company changes in AIOS. A link and a local folder name grant no access.
4. Read a published method at an exact commit using the intended assistant identity. Record the route, identity label, time, method path, commit and result in the existing setup evidence. Never include a token.
5. Confirm Evergreen writes are unavailable through a permission readback or a permitted denial test. Do not try an actual content write merely to test the boundary.
6. Set the actual `repository`, access owner, read identity and verification receipt in `00_AIOS/evergreen.json`. Set status to `verified` only when the receipt supports it. It remains a record, not a permission control.

The assistant may need account-owner consent or an App installation that this workspace cannot supply. Report the exact missing capability. Do not create a custom FF service or broaden access as a fallback.

## Use a method

1. Read company instructions and [routing](../../00_AIOS/routing.md). Identify the outcome, permitted input context and destination.
2. Resolve the current source ref to a commit. Read the selected brain's entry and the method, dependencies and QC it points to at that same commit.
3. Keep that revision fixed for the task. If the method changes while work is running, finish or explicitly restart; do not mix revisions silently.
4. Apply the method to the company's authorized inputs. Put drafts, custom configuration and results in the owning company folders.
5. Run the method's relevant checks and present the result in a company PR when a repository change is needed. Publishing content, sending a contract, collecting money or deploying code still needs its own authorized route.
6. Record what method was used and what actually passed. A technical review, a merge and acceptance in use are different events.

Use this compact provenance block in the output or its existing receipt:

```yaml
method_source:
  repository: "<verified Evergreen owner/repository>"
  commit: "<exact commit read for this task>"
  brains:
    - id: "<copy|creation|team|profit|attention>"
      method: "<actual method ID or repository path>"
company_inputs:
  - "<private company path or approved source reference>"
output: "<company path or PR>"
checks:
  - "<check and observed result>"
use_state: "<source complete|reviewed|merged|in use|accepted in use>"
```

This is a documentation example, not a new application schema. Use the actual existing receipt format when one is already established. Record every brain revision used in a cross-domain workflow. Do not put personal records, credentials or full private input text in a receipt that has a wider audience.

## Updates, outages and access changes

For a new task, resolve the current method again and record its new commit. A scheduled job or executable integration can require a reviewed, pinned version so an update does not silently change its behavior. Upgrade that component through a PR with the relevant checks.

If the repository cannot be read, state that fact. Continue tasks that can use the company's own authorized context, and do not represent an older copy as the latest method. The client's agreement governs access and continuity.

Company-owned source, company context and original company outputs stay in their private workspace. Ordinary AIOS work has no hosted-Core runtime requirement. The old thin client is deprecated under [decision 0002](../decisions/0002-hosted-core-thin-client-deprecated.md).

## Protect the actual data boundary

GitHub Read access applies to the repository, not selected folders or branches. Shared Evergreen must contain only material approved for every entitled reader. Internal FF records, credentials and client data do not belong there.

The same principle applies to company AIOS collaborators. If a teammate must not see a personnel or financial record, keep it in the existing restricted store and grant only the access required for that task. Writing “private” on a folder is not enforcement. Use the approved secret store or ignored local `.env` for credentials; committed configuration contains references only.

## Adopt this in an existing company

Starter README, CLAUDE, `00_AIOS/**` and other domain files are seeds. The package writes them once and preserves company copies on later upgrades. Managed docs can be released without replacing those seeds. Do not claim a Starter source merge has updated an existing company workspace.

Prepare a separate company PR that:

- compares the company's current instructions with this model and retains its business rules, access limits and active commitments;
- adds or updates the local source reference and task router;
- updates customer and operator journey records without replacing accepted decisions or inventing milestones;
- maps existing paths and their consumers before moving any file;
- keeps the installed manifest and adoption plan intact until a reviewed release or adoption step changes them.

A company using older folder names can add a routing crosswalk first. Do not rename load-bearing folders just to match a diagram. FF's own AIOS follows this same adoption process; it does not get copied into the public Starter.

## Acceptance evidence

A source document is ready when its links, paths, ownership and public-data boundary check out. A connected method flow is proven only when the intended assistant:

- reads a published method at a recorded commit with authorized Read access;
- produces a useful company PR from permitted company context;
- keeps private inputs out of shared intelligence;
- reads a later method revision on a later task and records the different commit;
- reports a refused or unavailable read honestly, while independent company work can continue.

These checks do not require a paid model run merely to validate documentation. The actual assistant and integration proof is a separate named action.
