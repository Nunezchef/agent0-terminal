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

## Rollback

Use the saved backup patch:

```bash
git -C /a0 apply -R /a0/.agent0-terminal/backups/<timestamp>.patch
```
