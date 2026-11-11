# This repository, in context

**What it is:** one company's private AIOS instance: its context, decisions, people, projects, configuration, work and records. It uses the seven domain folders established in Starter 3.0 and an approved, versioned Starter release.

**Who owns it:** the company owns the repository in its own account or organization and grants helpers the access it chooses. Company work stays here. Separate deployed applications and restricted data stores keep their existing boundaries where required; a domain folder does not require another instance repository.

**Where reusable intelligence lives:** the planned FF private Evergreen repository (shared with entitled clients) contains Copy, Creation, AI-Augmented Team, Profit OS and Attention. The company assistant reads an authorized method at a known commit and applies it here. [The read contract](docs/architecture/evergreen_aios.md) explains what must be verified. The company reference in [00_AIOS/evergreen.json](00_AIOS/evergreen.json) starts planned and unverified.

**How it is arranged:** [00_AIOS/routing.md](00_AIOS/routing.md) maps requests to a brain and a company destination. The [customer journey](03_RevOps/customer_journey/journey_map.md) maps commercial and delivery handoffs; the [operator journey](02_Team_Ops/onboarding/operator_journey.md) maps a person's progress toward independent work.

The release owns the managed operating layer identified by `release/package_spec.json`. Company domain files, README and CLAUDE are seeds written once and preserved on later upgrades. An upgrade of managed files does not rewrite the company's constitution, change its folders or install a new business process by itself.

## Setup and operation

- Setup: [SETUP.md](SETUP.md).
- Daily operation: [START_HERE.md](START_HERE.md).
- Install, upgrade, ownership and rollback: [docs/INSTALL_AND_UPGRADE.md](docs/INSTALL_AND_UPGRADE.md).
- Existing-company adoption: [Evergreen adoption](docs/architecture/evergreen_aios.md#adopt-this-in-an-existing-company).

## What the evidence means

Installed-file verification, GitHub permissions, a completed method read and a useful company output are separate checks. A successful local check or a passing PR does not prove a running integration. Verify the actual assistant host and the repository's enforced review rules.

Keep the existing operational limits visible: a missing Python or Node runtime can leave an assistant hook unable to run; a configured hook is not evidence it executed. Server-side review enforcement depends on the repository's actual plan and protection settings. A hosted assistant session may not have an authenticated GitHub CLI even when a desktop session does. Verify the intended route, and report unavailable checks honestly.

A folder, branch name, role label or instruction file does not limit what an authorized repository reader can see. Material that some collaborators must not read stays in its existing restricted store.

No hosted Core, or FF key-issuance service is required for ordinary company work. Evergreen access is still needed to retrieve a fresh method. Work from known private context can continue during an outage; a latest-method claim cannot.

## Dependency references

- Installed Starter release: `.aios/install.json`.
- Company registry row: `estate.yaml`.
- Planned or verified Evergreen connection: `00_AIOS/evergreen.json`.
- Layout and release decisions: `docs/decisions/`.

Pinned, approved releases remain the upgrade route. Keep existing company edits and use a reviewed adoption PR for new seed guidance.
