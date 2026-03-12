# Manual Install

If you do not want to run `install.sh`, do the plugin install manually.

## 1. Choose Agent Zero root

Example:

```bash
export A0_ROOT=/a0
```

## 2. Copy plugin into `usr/plugins`

```bash
mkdir -p "$A0_ROOT/usr/plugins/terminal0"
cp -f plugin.yaml README.md hooks.md install.sh uninstall.sh initialize.py LICENSE "$A0_ROOT/usr/plugins/terminal0/"
mkdir -p "$A0_ROOT/usr/plugins/terminal0/runtime" "$A0_ROOT/usr/plugins/terminal0/scripts"
cp -rf runtime/* "$A0_ROOT/usr/plugins/terminal0/runtime/"
cp -f scripts/install-into-agent0.sh "$A0_ROOT/usr/plugins/terminal0/scripts/"
```

## 3. Run initializer

```bash
python3 "$A0_ROOT/usr/plugins/terminal0/initialize.py" --a0-root "$A0_ROOT" --plugin-root "$A0_ROOT/usr/plugins/terminal0"
```

## 4. Enable plugin + symlink

```bash
touch "$A0_ROOT/usr/plugins/terminal0/.toggle-1"
mkdir -p "$A0_ROOT/plugins"
ln -sfn "$A0_ROOT/usr/plugins/terminal0" "$A0_ROOT/plugins/terminal0"
```

## 5. Restart Agent Zero

A full backend restart is required.

## Rollback

```bash
LATEST_BACKUP="$(find "$A0_ROOT/.terminal0/backups" -maxdepth 1 -name '*.patch' | sort | tail -1)"
git -C "$A0_ROOT" apply -R "$LATEST_BACKUP"
```
