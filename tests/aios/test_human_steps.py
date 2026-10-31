"""Client-safety content in the next Starter line: the human-step cards, the wizard order, SECURITY.md.

The cards are only useful while they match the vendors' screens, so each one must say which
official page it was checked against and when. The wizard must secure the workspace before it
invites anyone. SECURITY.md must not promise that the deny rules stop every read: Claude Code's
own docs say they don't cover a command that reads without naming the file, or a script.
"""

import os
import re
import unittest

import harness

ROOT = harness.REPO_ROOT
CARDS_DIR = os.path.join(ROOT, "docs", "human_steps")
CARDS = [
    "turn_on_github_2fa.md",
    "remove_an_org_member.md",
    "create_a_supabase_token.md",
    "download_a_supabase_backup.md",
    "connect_vercel_to_a_repo.md",
    "run_a_terminal_command_from_claude.md",
    "move_a_vercel_site.md",
    "restore_founder_review.md",
    "configure_github_agent_app.md",
]


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class HumanStepCards(unittest.TestCase):

    def test_the_index_lists_exactly_the_cards_on_disk(self):
        on_disk = sorted(f for f in os.listdir(CARDS_DIR) if f != "README.md")
        self.assertEqual(on_disk, sorted(CARDS))
        index = read("docs", "human_steps", "README.md")
        for card in CARDS:
            self.assertIn("(%s)" % card, index, card)

    def test_every_card_names_a_vendor_page_and_the_date_it_was_read(self):
        for card in CARDS:
            text = read("docs", "human_steps", card)
            checked = text.split("**Steps checked against:**", 1)
            self.assertEqual(len(checked), 2, "%s has no 'Steps checked against' line" % card)
            self.assertRegex(checked[1], r"https://\S+", card)
            self.assertRegex(checked[1], r"read \d{4}-\d{2}-\d{2}", card)

    def test_every_card_has_the_house_sections(self):
        for card in CARDS:
            text = read("docs", "human_steps", card)
            for heading in ("## It worked when", "## Send back", "## Video and checks"):
                self.assertIn(heading, text, "%s lacks %s" % (card, heading))

    def test_no_card_sends_people_to_a_2x_folder_or_a_skill_that_does_not_exist(self):
        # Until 3.0 this test forbade the 3.0 folder names, because 3.0 wasn't approved. In the 3.0
        # candidate they are the release's own folders, so the guard turns round: no card may
        # present a Starter 2.x folder as current. Only the card about the move itself names one.
        old = re.compile(r"\b(01_Foundations|02_Deliverables|03_Quality_Control|04_Customer_Journey|"
                         r"05_Assets|06_Communication|07_Setup|08_Automations|09_Archive|"
                         r"10_Departments|11_Projects)\b")
        for name in CARDS + ["README.md"]:
            text = read("docs", "human_steps", name)
            if name not in ("move_a_vercel_site.md", "restore_founder_review.md"):
                self.assertIsNone(old.search(text), name)
            self.assertNotRegex(text, r"human_step(?!s)", name)

    def test_the_install_guide_points_at_the_cards(self):
        self.assertIn("human_steps/README.md", read("docs", "INSTALL_AND_UPGRADE.md"))


class WizardOrder(unittest.TestCase):

    def test_airlocks_come_before_the_team_invite(self):
        lines = read(".claude", "skills", "onboard_wizard", "SKILL.md").splitlines()
        airlock = next(i for i, l in enumerate(lines)
                       if re.search(r"^\s*\d+\.\s+\*\*Secure it \(airlocks\)", l))
        invite = next(i for i, l in enumerate(lines)
                      if re.search(r"^\s*\d+\.\s+\*\*Invite your team\*\*", l))
        self.assertLess(airlock, invite)
        self.assertIn("2FA", lines[airlock])


class ApprovedReleaseRoute(unittest.TestCase):

    def test_every_setup_consumer_uses_the_approved_release_route(self):
        consumers = {
            "onboard_wizard": read(".claude", "skills", "onboard_wizard", "SKILL.md"),
            "skills_readme": read(".claude", "skills", "README.md"),
        }
        stale_positive_routes = (
            re.compile(r"get it through the portal.*Use this template", re.I),
            re.compile(r"green\s+\*{0,2}[\"']?Use this template", re.I),
        )
        for name, text in consumers.items():
            with self.subTest(consumer=name):
                self.assertIn("approved release", text.lower(), name)
                self.assertIn("INSTALL_AND_UPGRADE.md", text, name)
                for route in stale_positive_routes:
                    self.assertIsNone(route.search(text), "%s still recommends %s" % (name, route.pattern))


class SecurityClaims(unittest.TestCase):

    def test_security_md_does_not_promise_the_deny_rules_stop_every_read(self):
        text = read("SECURITY.md")
        self.assertNotIn("can't read your secrets", text)
        self.assertNotIn("never enter a Claude session", text)
        # It says what the rules don't cover, and what to do about it.
        self.assertIn("script that opens files itself", text)
        self.assertIn("sandbox", text)


if __name__ == "__main__":
    unittest.main()
