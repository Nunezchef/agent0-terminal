#!/usr/bin/env bash
set -euo pipefail

root="${1:-${A0_ROOT:-}}"
[ -n "${root}" ] || {
  printf 'Usage: %s <agent-zero-root>\n' "$0" >&2
  exit 1
}

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="${root}/.agent0-terminal/backups"
mkdir -p "${backup_dir}"
git -C "${root}" diff --binary > "${backup_dir}/${stamp}.patch"
printf '%s\n' "${backup_dir}/${stamp}.patch"
