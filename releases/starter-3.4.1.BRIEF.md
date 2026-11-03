# Starter 3.4.1: preserve the approved payload's ancestry

This corrective release packages the same payload Phoenix approved for 3.4.0. It repairs the release carrier's history so the existing installer can verify it. It adds no installed behavior.

The published `starter-3.4.0` tag remains at `0772f12acc5749f19abddc56796ad6352d4b8612`. Its package bytes match the approved record, but the squash merge removed payload commit `509908d696a87dadbd8e87b0def549fb3ef202f8` from its ancestry. The official `release check-tag` refuses it. The [actual failure receipt](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244#issuecomment-6583507173) records the missed prepublication check. Preserve that tag and its records unchanged.

## Payload and approval

`starter-3.4.1.json` retains pin `509908d696a87dadbd8e87b0def549fb3ef202f8`, all 174 path/class/mode/SHA256 tuples, 109 managed files, 65 seed files and 25 skills. Compatibility, layout, credentials and other payload metadata are unchanged. Only release ID, version and explanatory approval basis differ from the approved 3.4.0 record, whose SHA256 remains `591457ec9ac76861643ea59d78b97f555e761027600cc168d5ce9a1205ec1ef5`.

The [existing exact payload approval](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/419#issuecomment-6556546363), approver and original timestamp are reused. This is not a new Phoenix vote for a release named 3.4.1. The [local repair claim](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244#issuecomment-6583672191) separates routine technical repair, independent review and subsequent release custody. The original 3.4.0 brief retains the feature description, fixture evidence and real-use limits. Approved 3.2 and frozen 3.3 remain unchanged.

## Two source contexts

The catalog branch adds only this brief, the new manifest and `tests/aios/test_release_tag_ancestry.py` to current main. This makes the release record available to existing discovery, which requires both main and the tag to carry an approved record with the same payload pin.

The separate release carrier takes the complete approval tree from `0772f12acc5749f19abddc56796ad6352d4b8612`, adds only those same three excluded paths, and has the actual payload commit `509908d696a87dadbd8e87b0def549fb3ef202f8` as its direct parent. It preserves the original approved record and every package tuple. Future source PRs 69 and 70 on main are excluded from this carrier. Neither the catalog head nor its eventual squash merge is the tag target.

## Publisher's acceptance check

Before creating any remote tag, resolve the exact reviewed carrier commit and run the unchanged official CLI against that full commit ID:

```sh
python3 -B scripts/aios/aios.py release check-tag "$CARRIER_COMMIT" \
  --release-id starter-3.4.1 --repo "$SOURCE_REPO"
```

Require exit 0, actual payload ancestry and exact package parity. The focused regression exercises this command on a tree-identical carrier with missing ancestry (refused), a proper descendant (accepted), and an ancestor-preserving package mutation (refused). No checker or installer guard changes.

Freeze both source heads/trees, the carrier parent, manifest digest, package fingerprint and affected controls for one independent review. After review, the existing release owner separately assigns the exact remote tag resource and normal catalog publication/integration route. Publish only the frozen carrier target; read back the actual remote target and run `check-tag` again on that tag. A local candidate check is not a published tag or discoverable release.

No installation, fresh-session behavior, customer rollout or learner acceptance is established here. No existing tag is moved, deleted or replaced, and no default pin, paid execution, provider, deployment or client-owned content changes.
