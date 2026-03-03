#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="${REPO_OWNER:-Nunezchef}"
REPO_NAME="${REPO_NAME:-agent0-terminal}"
REPO_REF="${REPO_REF:-main}"
RAW_BASE="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_REF}"
PATCH_URL="${PATCH_URL:-${RAW_BASE}/patches/agent0-terminal.patch}"

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

  local cwd
  cwd="$(pwd)"
  if [ -f "${cwd}/run_ui.py" ] && [ -d "${cwd}/python" ] && [ -d "${cwd}/webui" ]; then
    printf '%s\n' "${cwd}"
    return 0
  fi

  return 1
}

verify_target() {
  local root="$1"

  [ -d "${root}" ] || die "Target path does not exist: ${root}"
  [ -f "${root}/run_ui.py" ] || die "Missing ${root}/run_ui.py"
  [ -d "${root}/python" ] || die "Missing ${root}/python"
  [ -d "${root}/webui" ] || die "Missing ${root}/webui"

  if [ -d "${root}/.git" ]; then
    if ! git -C "${root}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      die "Target is not a usable git checkout"
    fi
  else
    die "Target must be a git checkout"
  fi
}

create_backup() {
  local root="$1"
  local backup_dir="${root}/.agent0-terminal/backups"
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "${backup_dir}"
  git -C "${root}" diff --binary > "${backup_dir}/${stamp}.patch"
  printf '%s\n' "${backup_dir}/${stamp}.patch"
}

download_patch() {
  local tmp_patch="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${PATCH_URL}" -o "${tmp_patch}" || die "Failed to download patch from ${PATCH_URL}"
    return 0
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -qO "${tmp_patch}" "${PATCH_URL}" || die "Failed to download patch from ${PATCH_URL}"
    return 0
  fi
  die "curl or wget is required"
}

apply_patch() {
  local root="$1"
  local patch_file="$2"
  git -C "${root}" apply --check "${patch_file}" || die "Patch does not apply cleanly to ${root}. See docs/compatibility.md in ${REPO_NAME}."
  git -C "${root}" apply "${patch_file}" || die "Patch apply failed"
}

main() {
  local root
  root="$(detect_a0_root)" || die "Unable to detect Agent Zero. Set A0_ROOT=/path/to/agent-zero and retry."
  log "Target Agent Zero root: ${root}"
  verify_target "${root}"

  local backup_file
  backup_file="$(create_backup "${root}")"
  log "Created rollback patch: ${backup_file}"

  local tmp_patch
  tmp_patch="$(mktemp)"
  trap 'rm -f "${tmp_patch}"' EXIT

  download_patch "${tmp_patch}"
  apply_patch "${root}" "${tmp_patch}"

  log "Patch applied successfully."
  printf '\n'
  printf 'HARD RESTART REQUIRED\n'
  printf 'Fully restart the Agent Zero backend now. A browser refresh alone is not enough.\n'
  printf 'Rollback patch saved at: %s\n' "${backup_file}"
}

main "$@"
