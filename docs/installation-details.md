# Installation Details

This document exists so you can inspect exactly what `agent0-terminal` does before you run it.

## What `install.sh` Does

`install.sh` is the one-line installer used by:

```bash
curl -fsSL https://raw.githubusercontent.com/Nunezchef/agent0-terminal/main/install.sh | bash
```

Its flow is:

1. Detect the Agent Zero root.
2. Verify the target looks like a valid Agent Zero git checkout.
3. Create a rollback patch in `.agent0-terminal/backups/`.
4. Download `patches/agent0-terminal.patch` from this repo.
5. Run `git apply --check` against the target.
6. Apply the patch with `git apply`.
7. Print a hard restart notice.

The installer stops immediately if any validation or patch check fails.

## What `uninstall.sh` Does

`uninstall.sh` reverses a saved rollback patch.

Its flow is:

1. Detect the Agent Zero root.
2. Find the newest backup patch, or use the patch path you provide.
3. Run `git apply -R` to reverse that saved patch.
4. Print a hard restart notice.

## Helper Scripts

### `scripts/detect-a0-root.sh`

Detects the Agent Zero root in this order:

- `A0_ROOT`
- `/a0`
- current working directory if it contains `run_ui.py`, `python/`, and `webui/`

### `scripts/verify-target.sh`

Checks that the target:

- exists
- contains `run_ui.py`
- contains `python/`
- contains `webui/`
- is a valid git checkout

### `scripts/backup-target.sh`

Creates a rollback patch using the current target diff:

```bash
git -C <agent-zero-root> diff --binary
```

That output is saved under:

```bash
<agent-zero-root>/.agent0-terminal/backups/<timestamp>.patch
```

## Shell Commands The Installer Runs

These are the meaningful commands used by the installer and why they exist:

### Download the patch

```bash
curl -fsSL <patch-url> -o <tmpfile>
```

Purpose:
- download the exact patch bundle from this repo

Why it matters:
- you can inspect the raw patch URL yourself before running the installer

### Validate the target is a git checkout

```bash
git -C <agent-zero-root> rev-parse --is-inside-work-tree
```

Purpose:
- ensure the installer can use `git apply`

### Create the rollback patch

```bash
git -C <agent-zero-root> diff --binary > <backup-file>
```

Purpose:
- preserve a reversible snapshot of the target's current uncommitted state before the add-on changes are applied

### Check whether the add-on patch can apply

```bash
git -C <agent-zero-root> apply --check <patch-file>
```

Purpose:
- fail safely if the target checkout is incompatible or already diverged too far

### Apply the add-on patch

```bash
git -C <agent-zero-root> apply <patch-file>
```

Purpose:
- install the terminal integration files and modifications

### Roll back the saved patch

```bash
git -C <agent-zero-root> apply -R <backup-file>
```

Purpose:
- reverse a saved backup patch during uninstall

## Agent Zero Files Added Or Modified

The current patch touches these files.

### Modified Files

- `python/helpers/shell_local.py`
- `python/helpers/tty_session.py`
- `webui/components/chat/input/bottom-actions.html`
- `webui/components/chat/input/chat-bar.html`
- `webui/components/chat/input/input-store.js`
- `webui/css/messages.css`

### Added Files

- `python/api/terminal.py`
- `python/api/terminal_log_insert.py`
- `python/tools/terminal_log.py`
- `python/websocket_handlers/terminal_handler.py`
- `tests/test_inline_chat_terminal.py`
- `webui/components/chat/input/terminal-store.js`
- `webui/components/modals/terminal/terminal.html`
- `webui/components/modals/terminal/terminal-store.js`
- `webui/vendor/xterm/addon-fit.js`
- `webui/vendor/xterm/xterm.css`
- `webui/vendor/xterm/xterm.js`

## Theme Behavior

The terminal modal follows the same Agent Zero dark-mode preference used by the rest of the UI.

That means:

- dark mode keeps the terminal on a dark terminal palette
- light mode switches the terminal to a light terminal palette
- changing the Agent Zero preference updates the terminal theme instead of leaving it on a fixed black background

This keeps the modal visually aligned with the current app theme while preserving a terminal-appropriate color palette.

## What The `TerminalLog` Tool Does

Agent Zero does not watch the terminal live by default. Instead, terminal activity is written to per-chat log files, and the chatbot can inspect those logs by explicitly calling the `TerminalLog` tool.

`TerminalLog` supports these modes:

- `latest`: return the full latest terminal session log
- `list`: list available `session-*.log` files
- `tail`: return only the last `N` lines
- `commands`: return only command lines marked with `[COMMAND]`

It also supports:

- `lines`: used with `tail`
- `session`: target a specific `session-*.log` file

Example usage:

- `TerminalLog(mode="latest")`
- `TerminalLog(mode="list")`
- `TerminalLog(mode="tail", lines=100)`
- `TerminalLog(mode="commands")`
- `TerminalLog(mode="tail", session="session-20260303T033955Z.log", lines=50)`

The terminal modal also exposes an `Insert terminal log` action. That action calls the same backend tool path and injects the result into the chat as a native Agent Zero process step, so the agent can treat it as structured chat context instead of a loose pasted block.

## Trust Model

This repo is intentionally patch-based so it remains auditable:

- the installer is a small shell script
- the patch is plain text
- the touched files are explicit
- rollback is based on a saved patch

You do not need to trust a hidden binary or opaque installer.

## Known UI Limitation

The current terminal modal contains its own scroll area, and scroll containment is implemented so the surrounding Agent Zero UI should not take over while you are interacting with the terminal.

That behavior works, but it is not fully polished on Safari, especially on iPad:

- nested scrolling can still feel janky
- pointer and touch interaction may feel rougher than on desktop browsers
- the terminal remains usable, but the scroll experience is not yet ideal

This is a known limitation of the current release and a good candidate for future contribution work.
