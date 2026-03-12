#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${1:-}" ]]; then
  A0_ROOT="$1"
elif [[ -n "${A0_ROOT:-}" && -d "${A0_ROOT}" ]]; then
  A0_ROOT="${A0_ROOT}"
elif [[ -d "/a0/usr" && -d "/a0/webui" ]]; then
  A0_ROOT="/a0"
elif [[ -d "/git/agent-zero/usr" && -d "/git/agent-zero/webui" ]]; then
  A0_ROOT="/git/agent-zero"
else
  echo "Error: Cannot find Agent Zero root. Pass it as first argument." >&2
  exit 1
fi

PLUGIN_NAME="terminal0"
PLUGIN_DIR="$A0_ROOT/usr/plugins/$PLUGIN_NAME"
SYMLINK="$A0_ROOT/plugins/$PLUGIN_NAME"

echo "=== Agent0 Terminal Plugin Installer ==="
echo "Source: $SCRIPT_DIR"
echo "Target plugin dir: $PLUGIN_DIR"
echo "Agent Zero root: $A0_ROOT"
if git -C "$SCRIPT_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
  PLUGIN_COMMIT="$(git -C "$SCRIPT_DIR" rev-parse HEAD)"
  echo "Plugin commit: $PLUGIN_COMMIT"
else
  PLUGIN_COMMIT="unknown"
  echo "Plugin commit: unknown"
fi
echo

mkdir -p "$PLUGIN_DIR"

echo "[1/5] Copying plugin files..."
cp -f "$SCRIPT_DIR/plugin.yaml" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/README.md" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/hooks.md" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/install.sh" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/uninstall.sh" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/initialize.py" "$PLUGIN_DIR/"
cp -f "$SCRIPT_DIR/LICENSE" "$PLUGIN_DIR/"
mkdir -p "$PLUGIN_DIR/scripts" "$PLUGIN_DIR/runtime" "$PLUGIN_DIR/docs" "$PLUGIN_DIR/patches"
cp -f "$SCRIPT_DIR/scripts/install-into-agent0.sh" "$PLUGIN_DIR/scripts/"
cp -rf "$SCRIPT_DIR/runtime/"* "$PLUGIN_DIR/runtime/"
cp -rf "$SCRIPT_DIR/docs/"* "$PLUGIN_DIR/docs/" 2>/dev/null || true
cp -rf "$SCRIPT_DIR/patches/"* "$PLUGIN_DIR/patches/" 2>/dev/null || true

echo "[2/5] Running plugin initializer..."
python3 "$PLUGIN_DIR/initialize.py" --a0-root "$A0_ROOT" --plugin-root "$PLUGIN_DIR"

echo "[3/5] Enabling plugin..."
touch "$PLUGIN_DIR/.toggle-1"
printf '%s\n' "$PLUGIN_COMMIT" > "$PLUGIN_DIR/.installed-from-commit"

echo "[4/5] Creating plugin symlink..."
mkdir -p "$A0_ROOT/plugins"
ln -sfn "$PLUGIN_DIR" "$SYMLINK"

echo "[5/5] Done."
echo
echo "HARD RESTART REQUIRED"
echo "Fully restart the Agent Zero backend now. A browser refresh alone is not enough."
echo "Rollback patch saved under: $A0_ROOT/.terminal0/backups/"
