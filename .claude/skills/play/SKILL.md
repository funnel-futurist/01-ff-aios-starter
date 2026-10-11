---
name: play
description: Turn the Claude Code and Codex sounds back on for this computer after /pause. Runs only when the user types /play. NOT for pausing them (that is /pause) and NOT for changing which sounds play.
disable-model-invocation: true
allowed-tools: Bash(rm -f ~/.claude/sounds-paused), Bash(test:*), Bash(echo:*)
---

# /play - turn the sounds back on

Sound switch now reads: !`rm -f ~/.claude/sounds-paused; test -f ~/.claude/sounds-paused && echo PAUSED || echo PLAYING`

The line above ran the moment /play was typed. It removes the pause file `~/.claude/sounds-paused`, which `.claude/hooks/notify-sound.js` checks before every sound, for Claude Code and Codex alike. One file per computer, so this turns sounds on in every workspace on it. On a Mac the Glass sound plays when this reply finishes; Windows and Linux stay silent either way.

Reply with exactly one line and nothing else:
- If it reads PLAYING: `Sounds on for Claude and Codex - you'll hear Glass when this reply finishes. /pause stops them.`
- Otherwise: `Couldn't turn sounds on: ~/.claude/sounds-paused is still there.`

## Boundaries
| Ask | Skill |
|---|---|
| "Quiet the sounds" | `/pause` |
| "Change which sound plays" or "add a sound" | A founder change to `.claude/hooks/notify-sound.js`; route it to the repo owner |
| "I hear nothing on Windows or Linux" | Expected: the sounds are Mac only |

## Definition of done
- [ ] **D-1 - The reply matches the switch.**
  - **Example:** The line above reads PLAYING, and the reply says the sounds are on.
  - **Counter-example:** Replying "sounds on" while the line reads PAUSED.
- [ ] **D-2 - One line back, nothing else.**
  - **Example:** "Sounds on for Claude and Codex - you'll hear Glass when this reply finishes."
  - **Counter-example:** A paragraph explaining how hooks work.
- [ ] **D-3 - Nothing else changed.**
  - **Example:** Only the pause file was removed; `.claude/settings.json` is untouched.
  - **Counter-example:** Editing `.claude/settings.json` to add or change sound hooks.

## QC gate
Check D-1 to D-3 before replying. If the line reads PAUSED, say it didn't work and hand it to the repo owner: the pause file couldn't be removed.

No approved gold standard yet.
