#!/usr/bin/env bash
set -euo pipefail

root="${1:-${A0_ROOT:-}}"
[ -n "${root}" ] || {
  printf 'Usage: %s <agent-zero-root>\n' "$0" >&2
  exit 1
}

[ -d "${root}" ] || {
  printf 'Missing directory: %s\n' "${root}" >&2
  exit 1
}
[ -f "${root}/run_ui.py" ] || {
  printf 'Missing %s/run_ui.py\n' "${root}" >&2
  exit 1
}
[ -d "${root}/python" ] || {
  printf 'Missing %s/python\n' "${root}" >&2
  exit 1
}
[ -d "${root}/webui" ] || {
  printf 'Missing %s/webui\n' "${root}" >&2
  exit 1
}
git -C "${root}" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  printf 'Target is not a git checkout: %s\n' "${root}" >&2
  exit 1
}

printf 'OK: %s\n' "${root}"
