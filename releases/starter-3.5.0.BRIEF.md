# Starter 3.5.0 draft: native Codex entries and current workspace context

This draft packages the reviewed native Codex source now merged into Starter main. It is not approved or installable, and it has no published tag. The source payload is pinned to `fe8d115a6bd716f5165b224b96fce770e5ad31e6`, tree `97feafd063808946484681bb8e9222a9579bcba5`. Source integration and its independent reviews are recorded in [#244](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244#issuecomment-6597096309); release approval remains separate.

## Identity and package

`starter-3.5.0` is the next unused minor draft after published 3.4.1. The existing generator accepts a full commit pin and semantic version, always emits `status: draft` with blank approval, and has no approval path. The minor increment describes added managed native capabilities; it does not claim new folder-layout behavior or actual compatibility in a customer session. Frozen earlier records and published tags stay unchanged.

The manifest selects 185 files: 120 managed, 65 seed and 25 canonical skills. Compared with published 3.4.1, it adds 11 managed files, changes 10 managed files and removes none. All 65 seed tuples are unchanged. The existing `min_upgrade_from: 2.6.0`, layout declaration, credential-reference requirements and null AIOS-release consumption are retained. This receiving run tested fresh installation and upgrade from 3.4.1 only; older migration evidence is retained, not rerun or newly claimed.

The eight new native entries are `start`, `start-my-day`, `context_load`, `grill_me`, `onboard_wizard`, `project_management`, `wrap-up` and `review-queue`. They refer to canonical instructions and resources under `.claude/skills/`; the other canonical workflows do not gain automatic native wrappers.

The three added helpers are `codex-session-start.js`, `codex-dangerous-git.js` and `codex-pre-edit.py`. Source wires local startup status and supported Bash/apply_patch guards alongside the existing sounds. Startup does not fetch releases. The handlers require available runtimes and normal project/exact-definition trust. Files, offline contracts and package verification do not prove native enforcement, arbitrary shell writes, hosted tools or connectors are covered.

The managed `AGENTS.md` becomes a thin bootstrap instructing explicit reads of current client-owned `CLAUDE.md` and its permitted nested imports. It is not a snapshot, automatic native `@` import or runtime security boundary. Business customization stays in client-owned context. A root override can replace the bootstrap; actual loaded context needs its own fresh-session evidence.

## Upgrade and customization contract

An ordinary installed workspace upgrades through the new release's installer. Existing client-owned `CLAUDE.md`, README, foundations, permitted context files and `.claude/settings.local.json` remain theirs. This draft does not relocate company records or authorize account, provider or spending changes.

If a managed root instruction file has been edited, or a newly managed path already contains a client-owned file, the installer refuses. Preserve and reconcile the custom instructions through the existing owner/source route; do not delete them or change the record seal to force an upgrade. Existing adopted instances retain their explicit adoption boundaries. FF's historical 3.1 adoption excludes AGENTS and Codex hooks and needs its own reviewed treatment; a generic package fixture is not FF adoption.

## Actual bounded receiving evidence

The real draft's official release verification and attempted installation both returned exit 2, with no target files written. The real draft remains unchanged and its approval fields remain null.

Positive receiving used a separate local source with the literal `fixture-approval (test only)`, invented company/identity data and the same 185 payload tuples. That record is not a human approval, published release or actual GitHub identity. The full fixture carrier commit is a direct descendant of the payload pin and passed the official carrier check without creating a tag.

- Fresh fixture installation and source-backed verification passed: 120 managed files, 65 seeds and eight native entry files present. The installed bootstrap matched the source.
- A customized published-3.4.1 fixture upgraded and verified at 3.5.0. All 67 client-owned file hashes were preserved: 65 seed files, an imported company-context file and local settings. The new bootstrap did not flatten the invented company context into a snapshot.
- An edited managed AGENTS fixture refused both dry-run and application with exit 6; a preexisting client-owned root AGENTS refused fresh installation with exit 5. Every refused target was unchanged and its instructions were retained unreconciled.
- After committing the upgraded fixture, one rollback and source-backed verification restored 3.4.1/109 managed files. All 67 client-owned hashes and baseline file contents matched, except retained installer backups; all 11 newly added managed files were removed.

Exact commands, logs, fixture approval boundaries and hashes are frozen in the candidate receipts under #244. Existing source/hook/review evidence is reused. No broad old suite, native skill discovery, hook trust/events, assistant/model task, independent teammate profile, complete onboarding or real customer use was run here. Claude/profile authorization and actual-use acceptance remain separate. The historical FF checkout and its hold were not touched.

## Protected-text scan and classifications

The full FF protected-text comparison ran on 2026-11-03 at draft carrier `d905c3f4b0dca9c1ef842f2f18d36e50cd37d74c`. It covered 15,157 declared protected blobs from seven FF repositories against all 283 tracked public blobs, under the existing owner exclusion for Creative Engine. The exact source commits, tool hashes and private custody receipts are recorded under [#244](https://github.com/funnel-futurist/03a-ff-ai-augmented-team-intelligence/issues/244). No Creative Engine, LifeOS or personal-vault source was accessed.

The private maintainer reverse scanner compared every normalized 12-word window with the three-distinct-window rule, without subtracting an assumed public baseline. Its streaming self-check matched 60 real blobs. All five over-limit blobs were streamed, with zero unscanned. The supplementary pass covered 46 PDF/over-limit sources, with zero unreadable PDFs and zero finding pairs. The reverse pass found 238 pairs sharing any window; 130 met the rule.

Every rule-level pair was recomputed and classified: 128 contain only measured windows already published in approved 3.4.1; one is covered by an unchanged, exact approved public-method pin; one is shared public worker/coordinator closeout workflow. For that last pair, the candidate file is byte-identical to the public file Phoenix approved at exact PR #69 head `80c74b8fde560e3c4cf0411fb4da8a6defb1c844`, [review 5730009467](https://github.com/funnel-futurist/01-ff-aios-starter/pull/69#pullrequestreview-5730009467). The published 3.4.1 carrier passed the official check. No earlier full-scan result was assumed, and no new disclosure permission or release approval was inferred. No findings or owner content decisions remain unresolved for this scanned tree.

The existing private fingerprint list SHA256 is `33eba38ac5ebc94cee40235fa61c2af498edc666928e8cbc41524ff73f6b08ef`. It samples one window in eight with minimum one hit and was recorded for provenance; it was not used as a substitute for the full comparison or rebuilt. Raw findings, protected paths, matching windows and source details remain in private FF custody. No such data is included in this brief. The comparison detects exact text reuse within its declared scope; paraphrases and words in images, audio or video remain outside it. Release approval must also inspect the final-tree scan receipt for this subsequent brief-only carrier under #244. The seven existing public-method pins remain unchanged.

## Carrier and next release gates

This source change adds only the draft manifest and this brief under excluded `releases/`. Its carrier must descend from the exact payload pin and preserve all package tuples. The unchanged official checker accepts a full carrier commit ID; a tree-equivalent commit without payload ancestry is insufficient.

The draft carrier is not a tag target for publication. After the existing release owner obtains approval for the exact new payload/record, freeze and review the approved-record carrier at its actual revision and check that full commit before any separately authorized tag. Normal source publication/integration, workflow effects, main/tag discovery and remote readback remain distinct gates. Do not substitute the eventual catalog merge or copy the old 3.4 approval into this release.

No tag, default, push, PR, Preview, actual FF installation, trust change, native/model call, production/provider action or owner acceptance is authorized or performed by this draft.
