# Troubleshooting

## Installer cannot find Agent Zero root

Pass it explicitly:

```bash
bash install.sh /a0
```

## Plugin installed but terminal behavior did not change

You must restart Agent Zero backend after install.

Browser refresh alone is not enough.

## `initialize.py` fails with missing runtime file

Your plugin copy is incomplete. Re-clone this repository and run `install.sh` again.

## Terminal still has wrong colors in light mode

- Verify Agent Zero dark mode is actually set to light.
- Close and reopen the terminal modal.
- Hard refresh browser assets.

## Safari/iPad scroll still feels rough

Known limitation. Terminal remains usable, but nested scrolling is less smooth than Chromium.

## Rollback

```bash
LATEST_BACKUP="$(find /a0/.terminal0/backups -maxdepth 1 -name '*.patch' | sort | tail -1)"
git -C /a0 apply -R "$LATEST_BACKUP"
```
