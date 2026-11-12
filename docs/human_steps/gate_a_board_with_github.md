# Let approved people open a private board

Draft guide for an owner-approved setup.

A board can contain work that only a few people should see.
The board asks GitHub to identify each visitor.
It then checks an allowlist (the exact GitHub usernames permitted to enter).

This guide assumes the board already has reviewed middleware (server code that checks a request before serving a page).
That code must protect `/board`, everything under `/board/`, and the sign-in routes under `/auth/board/`.
A written guide alone does not install that code.

## Understand the sign-in journey

An OAuth App (a GitHub registration that lets a website ask who signed in) connects the board to GitHub.
A visitor selects sign in and approves the request on GitHub.
GitHub sends the browser back to a callback URL (the exact web address where the board finishes sign-in).
The board checks the returned identity against its allowlist.
An approved visitor receives a session cookie (a small browser value that proves a recent sign-in).

The reviewed implementation signs that cookie (adds a tamper-detection code) and expires it after four hours.
It checks the allowlist again on each board request.
Keep any existing hosting sign-in requirement enabled as a separate access check.

## Prepare the owner-approved settings

Choose the board's stable HTTPS address (its encrypted web address).
Use a placeholder such as `https://board.example.com` while drafting.
Replace it with the approved real address during setup.
Record the exact GitHub usernames the owner permits.

1. In GitHub, open Settings, Developer settings, OAuth Apps, then New OAuth App.
2. Choose a name the owner will recognize.
3. Set Homepage URL to the board's stable address.
4. Set Authorization callback URL to that same address followed by `/auth/board/callback`.
For the example above, use `https://board.example.com/auth/board/callback`.
Use the exact address without a wildcard (a `*` that stands for several addresses).
5. Leave device flow (sign-in intended for devices with limited browser input) disabled.
6. Register the application.

Copy its client ID (the application's identifier).
The authorized owner generates its client secret (the private credential used to finish sign-in).
Keep the secret in the approved secret store.
Never paste a secret into a chat, issue, screenshot or committed file.

In the hosting project's environment settings (named values supplied to running code), set these four variables for the intended environment.

| Variable | Value and purpose |
| --- | --- |
| `BOARD_OAUTH_CLIENT_ID` | The OAuth App's client ID. |
| `BOARD_OAUTH_CLIENT_SECRET` | The OAuth App's private client secret. |
| `BOARD_SESSION_KEY` | A unique random secret of at least 32 characters, generated with the approved secret tool, used to sign cookies. |
| `BOARD_ALLOWED_LOGINS` | The exact allowed GitHub usernames, separated by commas. |

Use GitHub usernames, not display names or email addresses.
Set all four before the approved deployment (publishing the reviewed code to its hosting environment).
The owner must authorize credential creation, settings changes and deployment under the project's rules.

## Check the deployed board

Ask the engineer to confirm the hosting service actually runs the middleware.
Test `/board`, `/board/`, `/board/index.html` and `/%62oard/` (an encoded spelling of the same board path).
Each must enforce the same sign-in check.
A web status page or a successful deployment alone cannot prove this.

Open a fresh browser session and request each path without a board session cookie.
Expect a redirect (a response sending the browser to another address) into sign-in.
Complete sign-in with an allowed account and confirm the board opens.
Use an owner-approved test account outside the allowlist and confirm access is refused.
Record the date, deployed revision (the exact version of the code), tested paths and outcomes.
Keep credentials and cookie values out of the evidence.

Before release, the engineer also tests missing settings in a sandbox (an isolated test environment).
Missing settings must return HTTP 503 (a web response code meaning the service is unavailable) and withhold the board.
A valid GitHub identity outside the allowlist must receive HTTP 403 (access refused).
A GitHub sign-in service failure must receive HTTP 502 (an upstream service failed).
Expired, tampered and wrong-type cookies must fail the sign-in check.
The successful callback must clear its temporary state cookie (the value linking the sign-in request to its reply).

If a protected path exposes the board, stop the rollout and have the engineer restore the previous approved access protection.
If sign-in fails, check the exact callback address, environment selection and username spelling.
Record a specific failed check for the engineer instead of sharing secret values.

## Source check

GitHub's OAuth App creation page was read on 2026-11-12.
It confirms the settings route, homepage field, callback field and optional device flow.
The board-specific variable names, cookie lifetime and failure responses come from the reviewed board implementation.
The GitHub page does not establish that a hosting service runs this board's middleware.
[Create an OAuth App](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app).

A walkthrough video with a checked transcript is still to find.
