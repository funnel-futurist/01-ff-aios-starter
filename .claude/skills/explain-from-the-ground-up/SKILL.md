---
name: explain-from-the-ground-up
description: Explain an unfamiliar topic or decision through background context, plain definitions, concrete examples and one mapped metaphor, so the reader understands the question before judging an answer. Use when a learner or operator asks why something exists, needs the context behind the context, or wants a simpler explanation before deciding. NOT for making or approving the decision (a decision-testing skill such as grill_me does that, if your workspace has one) and NOT for carrying out a change.
---

<!-- Provenance: adapted from the explain-from-the-ground-up skill, sha256 513476f46caf85a12a1c344e058bb0c94f89572a12f6e6206241c954620bef4c (46 lines). Changed from that source: the trigger is generic; the sections "How to start it", "Boundaries", "Definition of done" and "QC gate" are added; on 2026-11-12 the FF writing standard and check D-7 were added and the whole text was rewritten to follow that standard (one sentence per line). The rules themselves are unchanged. -->

# Explain from the ground up

Help the reader understand why a topic exists before asking them to judge anything.
Speak to an intelligent person who may not know this field's words.
Keep it simple, but keep the real difference you are explaining.

## The FF writing standard (adopted 2026-11-12)

Every explanation, lesson and setup guide follows these rules.
- Explain the basics behind the basics, for a normal person.
- Use short, simple sentences.
- Put each sentence on its own line.
- Define every technical term in parentheses the first time it appears.
  Example: "OAuth App (a small registration that lets a website use Sign in with GitHub)".

Existing lessons are checked against this standard too.
When you are asked to review a lesson or guide, check every rule above and list each line that breaks one.

## Start before the confusing part

Find the piece of background the reader is missing.
Usually that means four steps, in this order:
- the larger goal;
- the system that serves it;
- the problem with it today;
- only then, the proposed change.

If the reader still cannot see why the system or problem exists, go back one more step.
Do not just repeat the same explanation with shorter words.

Give enough background to answer these questions.
- What are we trying to do?
- What exists today?
- Why does it exist?
- What happened that makes this question matter now?
- Which parts are facts, which are plans, and which are guesses?

For claims about a real project, read the records that decide it before you explain.
Never invent a comforting story from a folder name.
If the records show what exists but not why, say so.
An earlier answer from an AI assistant is not evidence.

## Define each necessary piece

Explain each unfamiliar word in plain language before you use it to explain another word.
Give the real term next to its meaning, so the reader recognises it later.
Avoid a definition that needs three more undefined words.
When two parts have similar names, say what each one actually stores or does.

Use one small, concrete example all the way through.
Show what a person would see before and after the change.
Use real counts and labels when you state facts.
Mark any made-up teaching example as made up.

## Use a useful metaphor

Pick one familiar situation, such as a filing cabinet, a library, a school, a kitchen or a delivery service.
Map each of its parts to the real system, out loud.
Use one metaphor, not several.

Say where the metaphor stops being true, when that matters.
For example, a folder label is not a lock.
A metaphor must not suggest permissions, safety or ownership that the real system does not have.

Then translate back to the real situation.
The reader should understand both the story and what it stands for.

## Make a decision understandable

When you compare choices, say for each one:
- what it changes;
- why someone would pick it;
- what the reader gains or loses;
- what happens if nothing changes.

Keep the quick fix apart from the bigger design question.
Explain the recommendation's assumptions and evidence.
Do not treat it as approved.

Do not push for an answer while the reader is still trying to understand the question.
A request to explain allows explaining and checking the facts.
It does not allow changing anything or approving on the reader's behalf.

## Presentation

Write one short sentence per line, as the writing standard above says.
Group related lines into short blocks under plain headings.
Use lists only where they help.
A small table or simple diagram can show how several parts relate.
Match the depth to the reader's questions, not to a fixed template.

When asked for something even simpler:
- go further back in the chain of causes;
- introduce fewer ideas at once;
- add a concrete example.

Do not become childish, patronising or vague.
End with what it means for the reader in practice, not with more terms.

## How to start it

- **Claude Code:** type `/explain-from-the-ground-up` and then the topic or decision.
  Or ask in plain words, and Claude matches the request to this skill by its description.
  `/` lists every skill in this workspace.
- **Codex or another AI tool:** this skill does not register itself there.
  Open `.claude/skills/explain-from-the-ground-up/SKILL.md`, give it to the assistant, and ask it to follow it.
- **No skill at all (the fallback):** ask in plain words.
  "Explain the background, purpose and consequences before asking me to approve.
  Define each term.
  Use one familiar example or metaphor.
  Say what is known and what is unknown.
  Compare the choices, and tell me what happens if nothing changes."

Example: "/explain-from-the-ground-up Why does anything need a second reviewer before it is published?"

## Boundaries

| Ask | Skill |
|---|---|
| "Pressure-test this decision before I make it" | A decision-testing skill such as `grill_me`, if your workspace has one. This skill explains the question. It does not test or decide it. |
| "Make this change", or "approve it for me" | Not this skill. An explanation never approves anything for you. The person who owns the decision decides, after the explanation. |
| "Carry out the change" | The skill or person that owns that change. Explain first, then hand it to the owner. |

## Definition of done

- [ ] **D-1 - Start from the reader's missing background.**
  - **Example:** The first lines say what the team is trying to do and what exists today, before the proposed change.
  - **Counter-example:** Opening with the recommendation, or repeating the same explanation in shorter words.
- [ ] **D-2 - Define every term in plain words before it explains another term.**
  - **Example:** "A review rule (a setting that says who must approve a change before it is published)" comes before any line that relies on it.
  - **Counter-example:** Defining "review rule" as a "branch protection ruleset", a term the reader has not met.
- [ ] **D-3 - One metaphor, mapped part by part, with its limit.**
  - **Example:** A visitor badge opens only the doors written on it. The badge is the access, and the doors are the permissions. The picture stops where a badge says nothing about what the visitor does inside.
  - **Counter-example:** A filing cabinet, then a kitchen, with no mapping and no limit.
- [ ] **D-4 - Separate what is known, what is planned and what is unknown, and mark made-up examples.**
  - **Example:** "The record shows the setting is on. It does not say why." A made-up customer is labelled made up.
  - **Counter-example:** Inventing a comforting reason for a setting from its folder name.
- [ ] **D-5 - Compare the choices, including doing nothing.**
  - **Example:** Each option says what it changes, who gains or loses, and what happens if nothing changes.
  - **Counter-example:** One recommendation presented as if it were already approved.
- [ ] **D-6 - Finish with the practical meaning and the next action.**
  - **Example:** The answer says what the choice changes in practice and what happens next, then answers follow-up questions.
  - **Counter-example:** Asking a founder to repeat the explanation back before already-approved work continues.
- [ ] **D-7 - Meets the FF writing standard.**
  - **Example:** The basics come first, for a normal person. One short sentence per line. "Repository (a project folder that remembers every change)" the first time "repository" appears.
  - **Counter-example:** A long paragraph that uses "PR", "branch" or "OAuth" without saying what they are.

## QC gate

Check D-1 to D-7 before you finish.
When the reader asks for more background, go one step further back (D-1) instead of adding terms.
In normal conversation, finish with the practical meaning and the next action.
Then answer follow-up questions and continue work that is already approved.
Do not ask the reader to repeat the explanation back.

Use a teach-back (asking the learner to explain it in their own words) only in two cases:
- a learning or coaching exercise that asks for one;
- an adopted skills test.

Keep that exercise's or test's own checks.
A written demonstration does not prove that a real reader understood it.

No approved gold standard yet.
