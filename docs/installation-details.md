# Installation Details

This document describes exactly what the `terminal0` plugin installer does.

## Install model

`agent0-terminal` is now packaged as a true plugin repository:

- root [plugin.yaml](../plugin.yaml) defines plugin metadata
- install places plugin files under `usr/plugins/terminal0`
- initializer copies runtime payload files into Agent Zero core paths

The plugin is enabled with `.toggle-1` and symlinked to `plugins/terminal0`.

## What `install.sh` does

1. Detect Agent Zero root (`/a0` fallback or passed path).
2. Copy plugin repo files into `usr/plugins/terminal0`.
3. Run [initialize.py](../initialize.py).
4. Enable plugin (`.toggle-1`) and write `.installed-from-commit`.
5. Create symlink: `plugins/terminal0 -> usr/plugins/terminal0`.
6. Print hard restart notice.

## What `initialize.py` does

1. Verify target looks like Agent Zero and is a git checkout.
2. Create rollback patch at:
   - `<a0-root>/.terminal0/backups/<timestamp>.patch`
3. Copy runtime payload files from `runtime/` into Agent Zero:
   - `python/api/terminal.py`
   - `python/api/terminal_log_insert.py`
   - `python/tools/terminal_log.py`
   - `python/helpers/shell_local.py`
   - `python/helpers/tty_session.py`
   - `python/websocket_handlers/terminal_handler.py`
   - `tests/test_inline_chat_terminal.py`
   - `webui/components/chat/input/*.html|*.js` (terminal wiring)
   - `webui/components/modals/terminal/*`
   - `webui/css/messages.css`
   - `webui/vendor/xterm/*`

## What `uninstall.sh` does

1. Find the newest rollback patch in `.terminal0/backups` (or use passed path).
2. Reverse apply it with `git apply -R`.
3. Remove plugin files:
   - `usr/plugins/terminal0`
   - `plugins/terminal0`
4. Print hard restart notice.

## Theme behavior

The terminal follows Agent Zero’s dark-mode preference:

- dark mode => dark terminal palette
- light mode => light terminal palette
- live re-theme on UI theme changes

## Known limitation

Safari/iPad nested scrolling in the terminal modal is functional but still less smooth than Chromium.
