# Routing: the method and the company's work

This private repository is one company's instance. First identify the business outcome and its owning folder. Then read the required shared method, if any, from the verified Evergreen source. Five brains do not require five company repositories.

## Choose the company home

| A request about... | Authoritative company home |
|---|---|
| Company identity, offer, approved pricing, positioning or ideal customer | `00_AIOS/company/` |
| An item waiting for review | `00_AIOS/review_queue/`, pointing to the actual artifact |
| Brand, design, production assets or finished documents | `01_Creation/` |
| People, roles, projects, onboarding, policies or daily operations | `02_Team_Ops/` |
| Site, funnels, CRM, sales, automation, payments, support or customer journey | `03_RevOps/` |
| Campaigns, publishing, social accounts or content performance | `04_Attention/` |
| A recurring job's configuration, owner, trigger or run receipt | `05_Jobs/` |
| Finished material retained for history | `99_Archive/` |

A decision that changes the business belongs in `00_AIOS/decisions_log.md`. Project plans reference approved commercial facts instead of creating another pricing authority. Keep a customer record in the authorized CRM or data store when it already owns that fact; store the working reference here.

## Choose the shared brain

The brains below are planned in FF's private Evergreen repository (shared with entitled clients). Their listing is not proof that content is published or readable. Resolve them through [evergreen.json](evergreen.json) and follow the [read contract](../docs/architecture/evergreen_aios.md).

| Task | Primary brain ID | Brain | Company result |
|---|---|---|---|
| Offer, message, persuasive script, sales copy or funnel copy | `copy` | Copy | Owning offer or campaign; reusable finished copy in `01_Creation/outputs/copy/` |
| Design, deck, document, image, video or production check | `creation` | Creation | `01_Creation/` |
| Hiring, role setup, delegation, SOP, operator development or job method | `team` | AI-Augmented Team | `02_Team_Ops/`; recurring configuration in `05_Jobs/` |
| Capture, nurture, sales process, deal handoff, revenue or economics | `profit` | Profit OS | `03_RevOps/`; approved offer decisions stay in `00_AIOS/company/` |
| Authority content, channel strategy, distribution, publishing or performance | `attention` | Attention | `04_Attention/` |

For a cross-domain request, name one outcome owner and the handoff between contributors. A campaign can use Attention's brief, Copy's persuasion method and Creation's production method without duplicating their sources. Record each method revision actually used.

## Connect the two journeys

The [customer journey](../03_RevOps/customer_journey/journey_map.md) follows attention, capture, conversion, close, contract, onboarding, activation and delivery. It names the output and exit evidence for each stage.

The [operator journey](../02_Team_Ops/onboarding/operator_journey.md) follows the person who carries out that work: role and access, orientation, practice, reviewed first result, independent work and development. Assign skills to real customer-stage outputs.

An activated customer has a [90-day roadmap](../03_RevOps/customer_journey/activation_roadmap_90_days.md). An operator has a role-specific 30/60/90 plan. Link shared outcomes once; do not create parallel task lists.

## Read and write boundaries

- Read a shared method only after confirming access and exact revision. The owning brain remains the method authority.
- Write company inputs, customized workflows, outputs and provenance to the company destination. Evergreen stays read-only from this workspace.
- If access is missing, describe the precise read that failed and continue independent work. Do not invent another source or use another company's context.
- A repository reader may read all of its folders and history. Keep restricted records in their existing authorized store; a folder label does not restrict access.
- Keep secrets in the approved secret store or ignored local configuration. Committed references contain names and purposes, never values.

## Where the Starter 2.x folders went

| Old folder | New home |
|---|---|
| `01_Foundations/` | `00_AIOS/company/` |
| `02_Deliverables/_review_queue/`, `03_Quality_Control/` | `00_AIOS/review_queue/` |
| `02_Deliverables/copy/` | `01_Creation/outputs/copy/` |
| `02_Deliverables/funnels/`, `audits/`, `reports/` | `03_RevOps/funnels/`, `audits/`, `reports/` |
| `02_Deliverables/ads/`, `emails/`, `webinars/` | `04_Attention/campaigns/ads/`, `emails/`, `webinars/` |
| the rest of `02_Deliverables/` | `01_Creation/outputs/` |
| `04_Customer_Journey/` | `03_RevOps/customer_journey/` |
| `05_Assets/brand_guide/` | `01_Creation/brand/` |
| the rest of `05_Assets/` | `01_Creation/asset_library/` |
| `06_Communication/decisions_log.md` | `00_AIOS/decisions_log.md` |
| the rest of `06_Communication/` | `02_Team_Ops/routines/` |
| `07_Setup/` (your own files there) | `99_Archive/07_Setup/` |
| `08_Automations/` | `03_RevOps/automations/` |
| `09_Archive/` | `99_Archive/` |
| `10_Departments/` | `02_Team_Ops/departments/` |
| `11_Projects/` | `02_Team_Ops/projects/` |
