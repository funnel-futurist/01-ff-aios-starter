# README pass/fail checklist

A person who does not code should be able to answer what the repo does, where it runs, and what to do next without opening source files. A new repo passes when its README has these sections:

1. **What this is and who it is for:** one direct sentence, followed by the user or team it serves.
2. **How it works:** an Excalidraw diagram linked or embedded, with the important inputs and outputs named. Do not invent a diagram if one has not been made; mark the README incomplete.
3. **Folder map:** numbered, human-browsable folders and any framework-required folders explained in plain language.
4. **Setup:** ordered steps a non-coder can follow, with prerequisites and how to verify success.
5. **Where it runs:** the real Vercel URL/project and Supabase project, or “not used.” Do not guess or expose secrets.
6. **Connections:** Slack bots, webhooks and other integrations; list key *names* only, never values.
7. **Training:** the matching portal lesson or certification, or “none yet” with owner.
8. **Owner and last reviewed:** named accountable person and date.

Use [the template](template/README.md). The automated check verifies headings and numbering for **new template-based README files**; human review still checks whether the answers and diagram are true. Existing READMEs are migrated in their repo's approved pass, not auto-rewritten.
