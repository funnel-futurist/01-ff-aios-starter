# Verify the assistant's GitHub access

## Default: use the assistant's existing integration

The company owns one private AIOS repository. Connect the company's own assistant through its provider's existing GitHub integration, selected for the actual repositories it needs. FF receives scoped installation or support access where agreed. This existing integration is the default.

**Who acts:** the account or organization owner for provider consent and any installation choices that require them. An authorized operator can prepare the setup and perform available readbacks.

1. Identify the assistant identity, the private company repository and the actual Evergreen source. The [Evergreen reference](../../00_AIOS/evergreen.json) begins planned and unverified.
2. Follow the assistant provider's supported connection flow. Select the intended repositories and review its requested access. Do not claim capabilities from another assistant's connection.
3. Verify a private AIOS read. If the agreed work includes PRs, prove that capability through an authorized bounded company change.
4. Separately verify the authorized Evergreen method read at an exact commit. Evergreen remains Read-only. If the provider route cannot preserve the required boundary, report that limitation and prepare a supported scoped route; do not broaden access silently.
5. Record identity, selected repositories, observed capabilities, missing capabilities and the setup receipt in the company workspace. Never record a token.
6. For work that depends on checks or reviews, verify those read capabilities with the same executing identity. A founder's personal read does not prove the assistant's route.

The [Evergreen read contract](../architecture/evergreen_aios.md) defines source provenance, private outputs and honest unavailable-source behavior. This setup does not grant an entitlement, run a workflow or approve a deployment.

## A custom App

The existing integration above is the default. A custom GitHub App is used only when the client's owner records that decision in the company's decision log (decision D1 = A: the AIOS is client-owned). It is not a prerequisite for ordinary AIOS setup.

## It worked when

The company workspace records the assistant identity, its selected repositories, a successful private AIOS read and, separately, an authorized Evergreen method read at an exact commit. Missing capabilities are named, not assumed.

## Send back

"Assistant identity: `<label>`; selected repositories: `<names>`; AIOS read: `<passed/refused>`; Evergreen read at commit: `<sha or refused>`; missing: `<capability>`." Record no credentials.

## Video and checks

- **Video:** still to find; no transcript verified.
- **Steps checked against:** official GitHub documentation, read 2026-10-30: [About GitHub Apps and integrations](https://docs.github.com/en/apps/using-github-apps/about-using-github-apps).
