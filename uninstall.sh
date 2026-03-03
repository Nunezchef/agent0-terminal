#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[agent0-terminal] %s\n' "$*"
}

die() {
  printf '[agent0-terminal] ERROR: %s\n' "$*" >&2
  exit 1
}

detect_a0_root() {
  if [ -n "${A0_ROOT:-}" ] && [ -d "${A0_ROOT}" ]; then
    printf '%s\n' "${A0_ROOT}"
    return 0
  fi
  if [ -d /a0 ]; then
    printf '/a0\n'
    return 0
  fi
  return 1
}

main() {
  local root
  root="$(detect_a0_root)" || die "Unable to detect Agent Zero. Set A0_ROOT=/path/to/agent-zero and retry."

  local backup_file="${1:-}"
  if [ -z "${backup_file}" ]; then
    backup_file="$(find "${root}/.agent0-terminal/backups" -maxdepth 1 -type f -name '*.patch' 2>/dev/null | sort | tail -1 || true)"
  fi

  [ -n "${backup_file}" ] || die "No backup patch found. Provide a patch path explicitly."
  [ -f "${backup_file}" ] || die "Backup patch does not exist: ${backup_file}"

  git -C "${root}" apply -R "${backup_file}" || die "Rollback patch failed"
  log "Rollback applied from ${backup_file}"
  printf '\n'
  printf 'HARD RESTART REQUIRED\n'
  printf 'Fully restart the Agent Zero backend now. A browser refresh alone is not enough.\n'
}

main "$@"
