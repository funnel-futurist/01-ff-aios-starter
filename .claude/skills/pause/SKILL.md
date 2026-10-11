---
name: pause
description: Pause the sounds Claude Code and Codex play on this computer (finished, helper finished, needs you). Runs only when the user types /pause. NOT for turning them back on (that is /play) and NOT for changing which sounds play.
disable-model-invocation: true
allowed-tools: Bash(touch:*), Bash(test:*), Bash(echo:*), Edit(~/.ai-sounds-paused)
---

# /pause - quiet the sounds on this computer

Sound switch now reads: !`touch ~/.ai-sounds-paused; test -f ~/.ai-sounds-paused && echo PAUSED || echo PLAYING`

The line above ran the moment /pause was typed. It creates the pause file `~/.ai-sounds-paused`, which `.claude/hooks/notify-sound.js` checks before every sound, for Claude Code and Codex alike. One file per computer, so this pauses every workspace on it. Nothing else changes.

Reply with exactly one line and nothing else:
- If it reads PAUSED: `Sounds paused for Claude and Codex. /play turns them back on.`
- Otherwise: `Couldn't pause: ~/.ai-sounds-paused wasn't created.`

## Boundaries
| Ask | Skill |
|---|---|
| "Turn the sounds back on" | `/play` |
| "Change which sound plays" or "add a sound" | A founder change to `.claude/hooks/notify-sound.js`; route it to the repo owner |
| "Mute everything on my Mac" | macOS Focus or Do Not Disturb, not a skill |

## Definition of done
- [ ] **D-1 - The reply matches the switch.**
  - **Example:** The line above reads PAUSED, and the reply says the sounds are paused.
  - **Counter-example:** Replying "paused" while the line reads PLAYING.
- [ ] **D-2 - One line back, nothing else.**
  - **Example:** "Sounds paused for Claude and Codex. /play turns them back on."
  - **Counter-example:** A paragraph explaining how hooks work.
- [ ] **D-3 - Nothing else changed.**
  - **Example:** Only the pause file was created; `.claude/settings.json` is untouched.
  - **Counter-example:** Editing `.claude/settings.json` to delete the sound hooks.

## QC gate
Check D-1 to D-3 before replying. If the line reads PLAYING, say it didn't work and hand it to the repo owner: the home folder usually isn't writable.

No approved gold standard yet.
