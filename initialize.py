#!/usr/bin/env python3
"""Initializer for Agent0 Terminal plugin runtime payload.

Copies runtime files into an Agent Zero checkout and writes a rollback patch.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _create_backup(a0_root: Path) -> Path:
    backup_dir = a0_root / ".terminal0" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_file = backup_dir / f"{stamp}.patch"
    result = subprocess.run(
        ["git", "-C", str(a0_root), "diff", "--binary"],
        check=True,
        capture_output=True,
        text=True,
    )
    backup_file.write_text(result.stdout, encoding="utf-8")
    return backup_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a0-root", required=True)
    parser.add_argument("--plugin-root", required=True)
    args = parser.parse_args()

    a0_root = Path(args.a0_root).resolve()
    plugin_root = Path(args.plugin_root).resolve()
    runtime = plugin_root / "runtime"

    if not (a0_root / "run_ui.py").is_file() or not (a0_root / "webui").is_dir():
        raise RuntimeError(f"Target does not look like Agent Zero root: {a0_root}")
    if not (a0_root / ".git").exists():
        raise RuntimeError(f"Target must be a git checkout: {a0_root}")
    if not runtime.is_dir():
        raise RuntimeError(f"Missing runtime directory: {runtime}")

    backup_file = _create_backup(a0_root)

    targets = [
        "python/api/terminal.py",
        "python/api/terminal_log_insert.py",
        "python/tools/terminal_log.py",
        "python/helpers/shell_local.py",
        "python/helpers/tty_session.py",
        "python/websocket_handlers/terminal_handler.py",
        "tests/test_inline_chat_terminal.py",
        "webui/components/chat/input/bottom-actions.html",
        "webui/components/chat/input/chat-bar.html",
        "webui/components/chat/input/input-store.js",
        "webui/components/chat/input/terminal-store.js",
        "webui/components/modals/terminal/terminal.html",
        "webui/components/modals/terminal/terminal-store.js",
        "webui/css/messages.css",
        "webui/vendor/xterm/addon-fit.js",
        "webui/vendor/xterm/xterm.css",
        "webui/vendor/xterm/xterm.js",
    ]

    for rel in targets:
        src = runtime / rel
        dst = a0_root / rel
        if not src.is_file():
            raise RuntimeError(f"Missing runtime file: {src}")
        _copy(src, dst)

    print("Agent0 Terminal initialization completed.")
    print(f"Rollback patch: {backup_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
