#!/usr/bin/env bash
set -euo pipefail

if [ -n "${A0_ROOT:-}" ] && [ -d "${A0_ROOT}" ]; then
  printf '%s\n' "${A0_ROOT}"
  exit 0
fi

if [ -d /a0 ]; then
  printf '/a0\n'
  exit 0
fi

cwd="$(pwd)"
if [ -f "${cwd}/run_ui.py" ] && [ -d "${cwd}/python" ] && [ -d "${cwd}/webui" ]; then
  printf '%s\n' "${cwd}"
  exit 0
fi

printf 'Unable to detect Agent Zero root\n' >&2
exit 1
