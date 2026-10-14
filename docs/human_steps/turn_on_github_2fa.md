# Turn on GitHub two-factor sign-in (2FA)

**What it's for:** a stolen password alone can no longer open your GitHub account, and with it your company's repositories. About 5 minutes. You need an authenticator app on your phone or computer, such as Google Authenticator, Microsoft Authenticator or 1Password. GitHub recommends one that backs up to the cloud.

**Where:** https://github.com/settings/security

## Steps
1. Sign in to GitHub. Click your profile picture (top right), then **Settings**.
2. In the **Access** section of the sidebar, click **Password and authentication**.
3. In the **Two-factor authentication** section, click **Enable two-factor authentication**.
4. GitHub shows a QR code. In your authenticator app, add an account and scan it. (Can't scan? Click **setup key** and type the key into the app instead.)
5. The app now shows a six-digit code for GitHub. Type it into the field under **Verify the code from the app**.
6. Under **Save your recovery codes**, click **Download**. Keep the file somewhere safe and private, such as your password manager. These codes are how you get back in if you lose your phone.
7. Click **I have saved my recovery codes**.
8. Optional: add a second method (a security key or GitHub Mobile), so losing one device can't lock you out.

## It worked when
You're back on **Password and authentication**, and **Authenticator app** is listed under **Two-factor methods**.

For the next 28 days GitHub checks that your 2FA works. Sign in with a code once in that time, or GitHub will ask you for one on day 28.

## Send back
"2FA on for `<your GitHub username>`". Never send a code or the recovery-codes file to anyone.

## If it goes wrong
- The code is refused: codes change every 30 seconds, so type the current one. If it's still refused, check your device's clock is set automatically.
- Lost your phone later: sign in with one of your recovery codes.

## Video and checks
- **Video:** [How to Secure GitHub with 2FA and an Authenticator App](https://www.youtube.com/watch?v=jBPMS-WA-fs) (Tutorial Brief, 2 min 30 s). Its transcript was checked on 2026-10-01 against the steps as they read then, and it followed them in order. It uses Microsoft Authenticator; any authenticator app works the same way.
- **Steps checked against:** GitHub Docs, "Configuring two-factor authentication" (https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication), read 2026-10-14.
- **Not stated on that page:** the **Where** address, the screen you see afterwards (taken from GitHub's "Changing your two-factor authentication method" page) and the clock tip.
