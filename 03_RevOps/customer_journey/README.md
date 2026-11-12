# Customer journey: where each Bowtie stage lives

**Status: proposed.** This page says which folder in your AIOS holds the records for each Bowtie stage. The Bowtie is FF's eleven-stage customer lifecycle: four stages to win a customer, three to deliver, four to compound. This page moves no files and runs nothing.

The canonical stage list, with owners and course modules, is FF's [Bowtie map](https://github.com/funnel-futurist/ff-evergreen-intelligence/blob/main/00_system/maps/bowtie.md) (Evergreen `00_system/maps/bowtie.md`). Use its stage names in headings, file names and metric tags.

## Stage folders

| Technical term | Business term | Folders in your AIOS |
| --- | --- | --- |
| **Attention** | They find out you exist | `04_Attention/` (accounts, campaigns, content, performance, publishing) |
| **Capture** | They become a contact you own | `03_RevOps/funnels/`, `03_RevOps/crm/`, `03_RevOps/site/` |
| **Conversion** | They raise a hand | `03_RevOps/crm/`, `03_RevOps/automations/`, `03_RevOps/customer_journey/` |
| **Close** | They buy | `03_RevOps/sales/`, `03_RevOps/records/` |
| **Onboard** | They begin | `03_RevOps/customer_journey/` |
| **Activate** | They get the thing working | `03_RevOps/customer_journey/` ([90-day roadmap](activation_roadmap_90_days.md)); delivery work in `02_Team_Ops/projects/` |
| **Succeed** | They get the outcome | `03_RevOps/customer_journey/`, `03_RevOps/reports/`, `02_Team_Ops/projects/` |
| **Retain** | They stay | `03_RevOps/customer_journey/`, `03_RevOps/reports/` |
| **Review** | The outcome becomes evidence | `03_RevOps/records/`; proof assets in `01_Creation/asset_library/` |
| **Refer** | They send someone | `03_RevOps/customer_journey/`, `03_RevOps/crm/` |
| **Resell** | They buy again | `03_RevOps/sales/` |
| *Operating base (not a stage)* | What the funnel runs on, and whether it pays | `00_AIOS/company/`, `00_AIOS/systems/`, `02_Team_Ops/`, `05_Jobs/` |

Some offers skip a stage, and some customers enter further down (a referral, for example). Where a stage does not exist for your offer, say so rather than inventing one.

## The other files here

[`journey_map.md`](journey_map.md) is your service journey: the handoffs your team runs. Its stage names are yours and can differ from the Bowtie names above.

## Metrics

No formulas here. Each stage's measures and formulas come from the Profit OS method `docs/methods/bowtie_stage_metrics.md`. Record your own results in `03_RevOps/reports/`.
