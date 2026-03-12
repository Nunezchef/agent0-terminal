# Agent0 Terminal (`terminal0`)

True plugin packaging for Agent Zero that installs a seamless PTY-backed terminal modal into chat.

## What this plugin provides

- Real terminal modal inside Agent Zero chat
- Persistent sessions keyed by chat + folder
- TUI-friendly behavior (`xterm-256color`, resize sync)
- Terminal log capture per chat
- `TerminalLog` insertion into native Agent Zero process stream
- Light/dark theme sync with Agent Zero preferences

## Plugin manifest

Root plugin metadata is in [plugin.yaml](plugin.yaml):

- `name: terminal0`
- `title: Agent0 Terminal`
- plugin tags/version/settings fields for plugin ecosystem compatibility

## Install (plugin-first)

From an Agent Zero environment:

```bash
cd /a0/usr/workdir
rm -rf .terminal0-install
git clone --branch main https://github.com/Nunezchef/agent0-terminal.git .terminal0-install
bash /a0/usr/workdir/.terminal0-install/install.sh /a0
```

Alternative wrapper:

```bash
bash /a0/usr/workdir/.terminal0-install/scripts/install-into-agent0.sh /a0
```

After install:

- plugin files are placed in `/a0/usr/plugins/terminal0`
- symlink is created at `/a0/plugins/terminal0`
- runtime payload is copied into Agent Zero core paths by `initialize.py`
- restart Agent Zero backend

## Runtime payload layout

The plugin ships runtime files under `runtime/` and applies them during initialization.

- `runtime/python/*`: terminal API/tool/helper/websocket runtime
- `runtime/webui/*`: chat action wiring, modal UI, xterm assets
- `runtime/tests/*`: terminal regression coverage

## Why runtime copy exists

Current Agent Zero plugin extension points do not yet expose a fully isolated way to inject this terminal UI directly into chat action rows and modal flow without touching core paths.

So `terminal0` is packaged as a true plugin repo/manifest, but installs a runtime payload into Agent Zero to preserve seamless UX.

## Uninstall

```bash
bash /a0/usr/plugins/terminal0/uninstall.sh
```

This reverts the most recent rollback patch from `/a0/.terminal0/backups/` and removes plugin symlink/files.

## Notes

- Known limitation: Safari/iPad nested scrolling still feels less smooth than Chromium.
- Legacy patch file remains in `patches/` for compatibility, but plugin install is the canonical path.
