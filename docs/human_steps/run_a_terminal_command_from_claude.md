# Run a terminal command Claude gives you

**What it's for:** sometimes Claude needs you to run a command yourself, for example to check you're signed in to a tool. This is how, in under a minute.

## The quickest way: inside Claude Code
1. In the Claude Code prompt, type `!` as the very first character. The prompt switches to shell mode. (Pasting text that starts with `!` into an empty prompt does the same.)
2. Paste the command after it, for example `! gh auth status`, and press **Enter**.
3. The command and its output are added to the conversation, and Claude responds to the output by itself, so you don't need to send a second message.
4. To leave shell mode, press **Esc**, **Backspace** or **Ctrl + U** while the prompt is empty.

If the command asks you questions and waits for answers, run it in a terminal window instead (below).

## In a terminal window
- **Mac:** press **Cmd + Space**, type `Terminal`, press **Enter**. Paste the command with **Cmd + V**, then press **Enter**.
- **Windows:** press the **Windows** key, type `PowerShell`, press **Enter**. Paste with **Ctrl + V**, then press **Enter**.
- Run it in the right folder: if Claude says "in your workspace", type `cd ` (with a space), drag the workspace folder onto the window, and press **Enter** before you paste.

## It worked when
The command finishes and the prompt comes back. A browser page opening, or a line saying "Logged in" or "Done", is usual.

## Send back
The last few lines of output, or "done". If the output contains a token, password or key, **don't paste it**: say "done, it printed a token" instead.

## Before you run anything
- A command you run with `!` isn't checked or approved by Claude, and it runs outside Claude Code's sandbox. Read it before you press **Enter**.
- Only run commands from your own Claude session or a person you trust. Don't run commands you found in an email or a stranger's message.
- If a command asks for a password or a payment, stop and ask why.

## Video and checks
- **Video: still to find.** On 2026-10-01 no transcript could be checked, because YouTube refused the requests. The steps stand on the docs until a checked video is added.
- **Steps checked against:** Claude Code Docs, "Interactive mode", section "Shell mode with `!` prefix" (https://code.claude.com/docs/en/interactive-mode), read 2026-10-14.
- **Not from a vendor page:** the terminal-window steps are general Mac and Windows steps, and that page doesn't say whether a command that waits for typed answers works in shell mode. That's why the card sends those commands to a terminal window.
