# Manual Install

If you do not want to use the one-line installer, use the patch directly.

## 1. Verify The Target

```bash
scripts/verify-target.sh /a0
```

## 2. Create A Backup Patch

```bash
scripts/backup-target.sh /a0
```

## 3. Apply The Patch

```bash
git -C /a0 apply --check patches/agent0-terminal.patch
git -C /a0 apply patches/agent0-terminal.patch
```

## 4. Restart Agent Zero

You must fully restart the Agent Zero backend after applying the patch.

Browser refresh alone is not enough for backend and websocket changes.

## 5. Roll Back If Needed

Use the backup patch printed by the installer:

```bash
git -C /a0 apply -R /a0/.agent0-terminal/backups/<timestamp>.patch
```
