"""The intake skill: its question list, its instructions and its registration.

The intake asks one question at a time from `.claude/skills/intake/questions.md` and writes each
answer under a fixed section of the answers file. That only works while every question names a
topic, who may answer it, the question, a strawman and the section it writes to, and while those
sections match the six the skill creates. A list that drifts from that shape makes the skill write
into the wrong place or ask nothing about a topic, so the shape is checked here, and each check is
shown to fail on a broken list.
"""

import json
import os
import re
import unittest

import harness

ROOT = harness.REPO_ROOT
QUESTIONS = (".claude", "skills", "intake", "questions.md")
SKILL = (".claude", "skills", "intake", "SKILL.md")

TOPICS = ["role", "business", "priorities", "voice samples", "current tools", "immediate goals"]
SECTION = {
    "role": "## Role",
    "business": "## Business",
    "priorities": "## Priorities",
    "voice samples": "## Voice samples",
    "current tools": "## Current tools",
    "immediate goals": "## Immediate goals",
}
FIELDS = ["Topic", "Who answers", "Ask", "Strawman", "Writes to"]
HEADER_RE = re.compile(r"^## Q(\d+) - \S")
FIELD_RE = re.compile(r"^- \*\*([^*]+):\*\* ?(.*)$")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def split_blocks(text):
    """The intro, then one list of lines per '## Q' heading."""
    intro, blocks = [], []
    for line in text.splitlines():
        if line.startswith("## Q"):
            blocks.append([line])
        elif blocks:
            blocks[-1].append(line)
        else:
            intro.append(line)
    return intro, blocks


def join_blocks(intro, blocks):
    return "\n".join(intro + [line for block in blocks for line in block]) + "\n"


def renumber(blocks):
    return [["## Q%d - %s" % (i, b[0].split(" - ", 1)[1])] + b[1:] for i, b in enumerate(blocks, start=1)]


def topic_of(block):
    for line in block[1:]:
        m = FIELD_RE.match(line.strip())
        if m and m.group(1) == "Topic":
            return m.group(2).strip().lower()
    return None


def validate_questions(text):
    """Every way the list can be wrong, as readable strings; empty means it is valid."""
    errors = []
    if not text.startswith("# Intake questions\n"):
        errors.append("the first line must be '# Intake questions'")
    _, blocks = split_blocks(text)
    if not 10 <= len(blocks) <= 14:
        errors.append("there must be 10 to 14 questions, found %d" % len(blocks))
    seen, last_rank = set(), -1
    for expected, block in enumerate(blocks, start=1):
        m = HEADER_RE.match(block[0])
        if not m:
            errors.append("bad question heading: %r" % block[0])
            continue
        if int(m.group(1)) != expected:
            errors.append("expected Q%d, found Q%s" % (expected, m.group(1)))
        label = "Q%s" % m.group(1)
        found = [FIELD_RE.match(l.strip()) for l in block[1:] if l.strip().startswith("- **")]
        names = [f.group(1) if f else None for f in found]
        if names != FIELDS:
            errors.append("%s must have exactly the fields %s, in order; found %s" % (label, FIELDS, names))
        values = dict((f.group(1), f.group(2).strip()) for f in found if f)
        for name in FIELDS:
            if name in values and not values[name]:
                errors.append("%s has an empty %s" % (label, name))
        topic = values.get("Topic", "").lower()
        if topic not in SECTION:
            errors.append("%s has an unknown topic %r" % (label, topic))
            continue
        seen.add(topic)
        if values.get("Writes to") != SECTION[topic]:
            errors.append("%s writes to %r; topic %r writes to %r"
                          % (label, values.get("Writes to"), topic, SECTION[topic]))
        if values.get("Who answers", "").lower() not in ("founder", "anyone"):
            errors.append("%s: Who answers must be founder or anyone" % label)
        rank = TOPICS.index(topic)
        if rank < last_rank:
            errors.append("%s is out of topic order (%s after a later topic)" % (label, topic))
        last_rank = max(last_rank, rank)
    missing = [t for t in TOPICS if t not in seen]
    if missing:
        errors.append("no question covers: %s" % ", ".join(missing))
    return errors


class QuestionList(unittest.TestCase):

    def setUp(self):
        self.text = read(*QUESTIONS)
        self.intro, self.blocks = split_blocks(self.text)

    def test_the_shipped_list_is_valid(self):
        self.assertEqual(validate_questions(self.text), [])

    def test_a_list_with_no_voice_sample_question_fails(self):
        kept = [b for b in self.blocks if topic_of(b) != "voice samples"]
        self.assertLess(len(kept), len(self.blocks))
        errors = validate_questions(join_blocks(self.intro, kept))
        self.assertTrue(any("no question covers: voice samples" in e for e in errors), errors)

    def test_a_repeated_question_number_fails(self):
        mutant = self.text.replace("## Q2 - ", "## Q1 - ", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(any("expected Q2, found Q1" in e for e in validate_questions(mutant)))

    def test_a_question_missing_a_field_fails(self):
        block = [l for l in self.blocks[0] if not l.startswith("- **Strawman:**")]
        self.assertLess(len(block), len(self.blocks[0]))
        errors = validate_questions(join_blocks(self.intro, [block] + self.blocks[1:]))
        self.assertTrue(any(e.startswith("Q1 must have exactly the fields") for e in errors), errors)

    def test_a_wrong_section_fails(self):
        mutant = self.text.replace("- **Writes to:** ## Business", "- **Writes to:** ## Priorities", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(any("topic 'business' writes to '## Business'" in e
                            for e in validate_questions(mutant)))

    def test_a_question_out_of_topic_order_fails(self):
        moved = self.blocks[1:] + [self.blocks[0]]
        errors = validate_questions(join_blocks(self.intro, renumber(moved)))
        self.assertTrue(any("out of topic order" in e for e in errors), errors)

    def test_a_wrong_first_line_fails(self):
        mutant = self.text.replace("# Intake questions\n", "# Questions\n", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertIn("the first line must be '# Intake questions'", validate_questions(mutant))

    def test_too_few_or_too_many_questions_fail(self):
        one_per_topic = [next(b for b in self.blocks if topic_of(b) == t) for t in TOPICS]
        few = validate_questions(join_blocks(self.intro, renumber(one_per_topic)))
        self.assertIn("there must be 10 to 14 questions, found 6", few)
        extra = [self.blocks[0]] * (15 - len(self.blocks)) + self.blocks
        many = validate_questions(join_blocks(self.intro, renumber(extra)))
        self.assertIn("there must be 10 to 14 questions, found 15", many)

    def test_a_badly_shaped_heading_fails(self):
        mutant = self.text.replace("## Q1 - ", "## Q1 ", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertTrue(any(e.startswith("bad question heading") for e in validate_questions(mutant)))

    def test_an_empty_field_fails(self):
        block = [("- **Ask:**" if l.startswith("- **Ask:**") else l) for l in self.blocks[0]]
        self.assertNotEqual(block, self.blocks[0])
        errors = validate_questions(join_blocks(self.intro, [block] + self.blocks[1:]))
        self.assertIn("Q1 has an empty Ask", errors)

    def test_an_unknown_topic_fails(self):
        mutant = self.text.replace("- **Topic:** role", "- **Topic:** marketing", 1)
        self.assertNotEqual(mutant, self.text)
        self.assertIn("Q1 has an unknown topic 'marketing'", validate_questions(mutant))

    def test_a_founder_question_opened_to_everyone_fails(self):
        # Q5 asks for revenue, which only the founder answers.
        self.assertIn("revenue", self.blocks[4][3])
        block = [l.replace("- **Who answers:** founder", "- **Who answers:** everyone") for l in self.blocks[4]]
        self.assertNotEqual(block, self.blocks[4])
        errors = validate_questions(join_blocks(self.intro, self.blocks[:4] + [block] + self.blocks[5:]))
        self.assertIn("Q5: Who answers must be founder or anyone", errors)


class SkillInstructions(unittest.TestCase):

    def test_frontmatter_names_the_skill_and_what_it_is_not_for(self):
        text = read(*SKILL)
        front = text.split("---", 2)[1]
        self.assertRegex(front, r"(?m)^name: intake$")
        self.assertIn("NOT for", front)
        for other in ("onboard_wizard", "grill_me", "f6_completeness_check", "env_keys"):
            self.assertIn(other, front)

    def test_it_reads_the_list_and_writes_the_six_sections(self):
        text = read(*SKILL)
        self.assertIn("`.claude/skills/intake/questions.md`", text)
        self.assertIn("`00_AIOS/company/profile_snapshot/intake.md`", text)
        for heading in SECTION.values():
            self.assertIn("`%s`" % heading, text)
        self.assertIn("*Last updated:*", text)

    def test_it_forbids_secrets_and_keeps_voice_samples_word_for_word(self):
        text = read(*SKILL)
        self.assertIn("Never ask for or write down a password, API key or token", text)
        self.assertIn("Voice samples stay word for word", text)


class Registration(unittest.TestCase):

    def test_the_skill_is_registered_everywhere_the_starter_lists_skills(self):
        declared = json.loads(read(".template_version.json"))
        self.assertIn("intake", declared["skills"])
        claude_files = json.loads(read("release", "adapters.json"))["tools"]["claude-code"]["files"]
        self.assertIn(".claude/skills/intake/SKILL.md", claude_files)
        self.assertIn(".claude/skills/intake/questions.md", claude_files)
        entries = json.loads(read(".aios", "roles.json"))["entries"]
        self.assertIn("intake", entries["founder"]["skills"])
        self.assertIn("intake", entries["operator"]["skills"])
        self.assertIn("| **intake** |", read(".claude", "skills", "README.md"))

    def test_the_onboarding_wizard_runs_it_after_the_vision_step(self):
        wizard = read(".claude", "skills", "onboard_wizard", "SKILL.md")
        step4 = re.search(r"(?ms)^## Step 4:.*?(?=^## Step 5:)", wizard)
        self.assertIsNotNone(step4, "the wizard lost its Step 4 or Step 5 heading")
        self.assertIn("`/intake`", step4.group(0))
        self.assertIn("`00_AIOS/company/profile_snapshot/intake.md`", step4.group(0))


if __name__ == "__main__":
    unittest.main()
