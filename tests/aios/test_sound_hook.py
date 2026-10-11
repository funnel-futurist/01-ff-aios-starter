"""The sound hook: Stop, SubagentStop and Notification each play a sound, and one file pauses all.

The real hook command from the shipped settings runs here the way Claude Code runs it: through a
shell, with hook JSON on stdin. A stand-in `afplay` on PATH records what it was asked to play, so a
test never makes a real sound, and a throwaway home folder holds the pause switch.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import harness

REAL_ROOT = harness.REPO_ROOT
HOOK = os.path.join(REAL_ROOT, ".claude", "hooks", "notify-sound.js")
WIRED = {"Stop": "done", "SubagentStop": "subagent", "Notification": "needs-you"}
SOUND_FILE = {"done": "Glass.aiff", "subagent": "Hero.aiff", "needs-you": "Pop.aiff"}


def settings_hooks():
    with open(os.path.join(REAL_ROOT, ".claude", "settings.json")) as fh:
        return json.load(fh)["hooks"]


def plan(event, platform, home):
    script = ("const h = require(process.argv[1]);"
              "process.stdout.write(JSON.stringify(h.plan(process.argv[2], process.argv[3],"
              " process.argv[4])));")
    out = subprocess.check_output(["node", "-e", script, HOOK, event, platform, home])
    return json.loads(out.decode())


class Wiring(unittest.TestCase):

    def test_each_event_runs_the_sound_hook_with_its_own_sound(self):
        hooks = settings_hooks()
        for event, arg in WIRED.items():
            commands = [h["command"] for group in hooks[event] for h in group["hooks"]]
            self.assertEqual(
                commands, ['node "$CLAUDE_PROJECT_DIR/.claude/hooks/notify-sound.js" ' + arg],
                event)


class Plan(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.home, True)

    def pause(self):
        os.makedirs(os.path.join(self.home, ".claude"), exist_ok=True)
        open(os.path.join(self.home, ".claude", "sounds-paused"), "w").close()

    def test_each_event_plays_its_system_sound_on_macos(self):
        for event, sound in SOUND_FILE.items():
            self.assertEqual(plan(event, "darwin", self.home),
                             {"cmd": "afplay", "args": ["/System/Library/Sounds/" + sound]},
                             event)

    def test_the_pause_file_silences_every_event(self):
        self.pause()
        for event in SOUND_FILE:
            self.assertIsNone(plan(event, "darwin", self.home), event)

    def test_removing_the_pause_file_turns_sound_back_on(self):
        self.pause()
        os.remove(os.path.join(self.home, ".claude", "sounds-paused"))
        self.assertIsNotNone(plan("done", "darwin", self.home))

    def test_other_systems_and_unknown_events_are_silent(self):
        for platform in ("linux", "win32"):
            self.assertIsNone(plan("done", platform, self.home), platform)
        for event in ("", "Stop", "toString", "constructor"):
            self.assertIsNone(plan(event, "darwin", self.home), event)


class RealHook(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.home, ".claude"))
        self.log = os.path.join(self.tmp, "played.log")
        bin_dir = os.path.join(self.tmp, "bin")
        os.makedirs(bin_dir)
        stub = os.path.join(bin_dir, "afplay")
        with open(stub, "w") as fh:
            # Records the request at once, then holds on: a hook that waited for it would be slow.
            fh.write('#!/bin/sh\necho "$@" >> "%s"\nsleep 3\n' % self.log)
        os.chmod(stub, 0o755)
        self.env = dict(os.environ, HOME=self.home, CLAUDE_PROJECT_DIR=REAL_ROOT,
                        PATH=bin_dir + os.pathsep + os.environ.get("PATH", ""))

    def run_hook(self, event):
        command = settings_hooks()[event][0]["hooks"][0]["command"]
        payload = json.dumps({"hook_event_name": event, "session_id": "test"})
        started = time.time()
        done = subprocess.run(["sh", "-c", command], input=payload.encode(), env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return done, time.time() - started

    def played(self, wait):
        deadline = time.time() + wait
        while time.time() < deadline:
            if os.path.exists(self.log):
                with open(self.log) as fh:
                    return fh.read()
            time.sleep(0.05)
        return ""

    @unittest.skipUnless(sys.platform == "darwin", "the sound plays on macOS only")
    def test_the_real_command_plays_its_sound_and_returns_at_once(self):
        done, took = self.run_hook("Stop")
        self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"", b""))
        self.assertLess(took, 2.5, "the hook waited for the player")
        self.assertEqual(self.played(5).strip(), "/System/Library/Sounds/Glass.aiff")

    def test_the_real_command_is_silent_and_exits_0_while_paused(self):
        open(os.path.join(self.home, ".claude", "sounds-paused"), "w").close()
        for event in WIRED:
            done, _ = self.run_hook(event)
            self.assertEqual((done.returncode, done.stdout, done.stderr), (0, b"", b""), event)
        self.assertEqual(self.played(1), "")


if __name__ == "__main__":
    unittest.main()
