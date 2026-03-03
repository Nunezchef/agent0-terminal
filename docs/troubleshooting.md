# Troubleshooting

## The Installer Cannot Find Agent Zero

Set the target explicitly:

```bash
A0_ROOT=/a0 curl -fsSL https://raw.githubusercontent.com/Nunezchef/agent0-terminal/main/install.sh | bash
```

## The Patch Does Not Apply

This usually means your Agent Zero checkout differs from the expected baseline.

- inspect the `git apply --check` failure
- resolve local changes in the same files
- apply the patch manually if needed

## The UI Refreshes But The Terminal Still Behaves Like Old Code

You need a full backend restart.

Browser refresh alone does not reload Python websocket handlers or API modules.

## Terminal Scroll Feels Janky On Safari Or iPad

The terminal modal uses nested scroll containment, and Safari can still make that feel rough even when the terminal works correctly.

What you may notice:

- scrolling inside the terminal can feel less smooth than desktop browsers
- iPad Safari may still feel awkward with pointer or touch input inside the terminal viewport

Current status:

- this is a known limitation of the current release
- the terminal is still usable
- the issue is documented so contributors can improve it later

Current workaround:

- use the terminal as-is for now
- if possible, use a desktop Chromium-based browser for the smoothest current experience

## Rollback

Use the saved backup patch:

```bash
git -C /a0 apply -R /a0/.agent0-terminal/backups/<timestamp>.patch
```
