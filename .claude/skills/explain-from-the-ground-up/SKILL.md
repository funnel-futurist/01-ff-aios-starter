---
name: explain-from-the-ground-up
description: Explain an unfamiliar topic or decision through background context, plain definitions, concrete examples and one mapped metaphor, so the reader understands the question before judging an answer. Use when a learner or operator asks why something exists, needs the context behind the context, or wants a simpler explanation before deciding. NOT for making or approving the decision (a decision-testing skill such as grill_me does that, if your workspace has one) and NOT for carrying out a change.
---

<!-- Provenance: adapted from the explain-from-the-ground-up skill, sha256 513476f46caf85a12a1c344e058bb0c94f89572a12f6e6206241c954620bef4c (46 lines). The body below is kept as written. Changed from that source: the trigger is generic, and the sections "How to start it", "Boundaries", "Definition of done" and "QC gate" are added. -->

# Explain from the ground up

Help the reader understand why a topic exists and how its parts fit together before asking them to judge a recommendation. Speak to an intelligent person who may not know this domain's vocabulary. Simplicity must preserve the real distinction being explained.

## Start before the confusing part

Identify the reader's missing prerequisite. Usually explain the larger goal, the system that serves it, the current problem, and only then the proposed change. Go back another layer when the reader still cannot see why the system or problem exists. Do not merely repeat the same explanation with shorter words.

Use enough background to answer: What are we trying to accomplish? What exists today? Why does it exist? What happened that makes this question relevant now? Which parts are established facts, intended design, and unresolved assumptions?

For claims about an actual project, inspect the relevant authoritative records before explaining historical reasons or current architecture. Never invent a reassuring migration story or rationale from a folder name. If evidence establishes what exists but not why, say so plainly. A prior assistant explanation is not source evidence.

## Define each necessary piece

Introduce unfamiliar terms in ordinary language before using them to explain another unfamiliar term. Give the real term alongside its meaning so the reader can recognize it later. Avoid definitions that require three more undefined terms. Distinguish similarly named components and explain what each actually stores or does.

Use a small concrete example throughout. Show what a person would see or experience before and after the change. Counts, labels and examples should be sourced when factual; clearly mark invented teaching examples.

## Use a useful metaphor

Choose a familiar situation, such as a filing cabinet, library, school, kitchen or delivery service, that explains the important relationship. Explicitly map its parts to the real system. Prefer one consistent metaphor over several competing ones.

Explain where the metaphor stops being accurate when that matters. A folder label, for example, is not automatically a security lock; an analogy must not imply permissions, safety or ownership the implementation does not establish.

After the metaphor, translate back into the real situation. The reader should understand both the story and what it represents.

## Make a decision understandable

When comparing choices, explain what each changes, why someone would choose it, what the reader gains or loses, and what happens if nothing changes. Distinguish the immediate repair from the larger architectural question. Explain the recommendation's assumptions and evidence without treating it as already approved.

Do not push for an answer while the reader is still trying to understand the question. An explanation request authorizes explanation and relevant investigation, not an architectural change or approval on the reader's behalf.

## Presentation

Use connected, conversational paragraphs and short lists only where they help. A compact comparison table or simple diagram can clarify several relationships. Adjust depth to the reader's questions rather than forcing every answer into a fixed template or three layers.

When asked for an even simpler explanation, move further back in the causal chain, reduce the number of concepts introduced at once, and add a concrete example. Do not become childish, patronizing or vague. Finish with the practical meaning for the reader, rather than another pile of terminology.

## How to start it

- **Claude Code:** type `/explain-from-the-ground-up` and then the topic or decision, or ask in plain words and Claude matches the request to this skill by its description. `/` lists every skill in this workspace.
- **Codex or another AI tool:** this skill does not register itself there. Open `.claude/skills/explain-from-the-ground-up/SKILL.md`, give it to the assistant and ask it to follow it.
- **No skill at all (the fallback):** ask in plain words. "Explain the background, purpose and consequences before asking me to approve. Define each term, use one familiar example or metaphor, say what is established and what is unknown, compare the choices, and tell me what happens if nothing changes."

Example: "/explain-from-the-ground-up Why does anything need a second reviewer before it is published? Start with why the system exists, define the individual parts, use one mapped metaphor, and show what each option changes in practice."

## Boundaries

| Ask | Skill |
|---|---|
| "Pressure-test this decision before I make it" | A decision-testing skill such as `grill_me`, if your workspace has one. This skill explains the question; it does not test or decide it. |
| "Make this change", or "approve it for me" | Not this skill. An explanation never approves anything on your behalf: the person who owns the decision decides, after the explanation. |
| "Carry out the change" | The skill or person that owns that change. Explain first, then route it to the owner. |

## Definition of done

- [ ] **D-1 - Start from the reader's missing prerequisite.**
  - **Example:** The first paragraph says what the team is trying to accomplish and what exists today, before it mentions the proposed change.
  - **Counter-example:** Opening with the recommendation, or repeating the same explanation in shorter words when the reader still cannot see why the system exists.
- [ ] **D-2 - Define every term in ordinary words before it explains another term.**
  - **Example:** "A review rule is a setting that says who must approve a change before it is published" comes before any sentence that relies on it.
  - **Counter-example:** Defining "review rule" as a "branch protection ruleset", a term the reader has not met yet.
- [ ] **D-3 - One metaphor, mapped part by part, with its limit.**
  - **Example:** A visitor badge opens only the doors written on it: the badge is the access, the doors are the permissions, and the picture stops where a badge says nothing about what the visitor does once a door is open.
  - **Counter-example:** A filing cabinet, then a kitchen, with no mapping back and no limit, so the reader assumes a folder label is a lock.
- [ ] **D-4 - Separate what is established, what is intended and what is unknown, and mark invented examples.**
  - **Example:** "The record shows the setting is on; it does not say why it was turned on", and a made-up customer is labelled invented.
  - **Counter-example:** Inventing a reassuring reason for a setting from its folder name.
- [ ] **D-5 - Compare the choices, including doing nothing.**
  - **Example:** Each option states what it changes, who gains or loses, and what happens if nothing changes.
  - **Counter-example:** One recommendation presented as if it were already approved.
- [ ] **D-6 - Finish with the practical meaning and next action.**
  - **Example:** The answer says what the choice changes in practice and what happens next within the existing authority, then answers any follow-up questions.
  - **Counter-example:** Requiring a founder or operator to repeat the explanation before continuing already-authorized work, or ending on another pile of terminology.

## QC gate

Check D-1 to D-6 before you finish. When the reader asks for more background, go one layer further back (D-1) instead of adding terms. In normal founder/operator conversation, finish with the practical meaning and next action, answer follow-up questions, and continue otherwise authorized work without requiring a repeat-back.

Use teach-back only in an explicitly requested learning or coaching exercise, or an adopted competency assessment. Preserve that exercise's or assessment's required checks. A written demonstration does not establish that a real reader understood it.

No approved gold standard yet.
