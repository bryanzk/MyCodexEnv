#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
EIGENPHI_BACKEND_ROOT=""
DRY_RUN="false"
SKIP_AGENTS="false"
SKIP_SKILLS="false"
SKIP_WORKFLOW="false"
SKIP_CONFIG="false"

usage() {
  cat <<'USAGE'
Usage: import_codex_home.sh --repo-root <path> [--codex-home <path>] [--eigenphi-backend-root <path>] [--dry-run] [--skip-agents] [--skip-skills] [--skip-workflow] [--skip-config]
USAGE
}

log() {
  printf '%s\n' "$*"
}

sync_file() {
  local src="$1"
  local dst="$2"
  local label="$3"

  if [[ ! -f "$src" ]]; then
    log "SKIP ${label}: source not found (${src})"
    return 0
  fi

  mkdir -p "$(dirname "$dst")"

  if [[ "$DRY_RUN" == "true" ]]; then
    if [[ ! -f "$dst" ]]; then
      log "CREATE ${label}: ${dst}"
    elif cmp -s "$src" "$dst"; then
      log "UNCHANGED ${label}: ${dst}"
    else
      log "UPDATE ${label}: ${dst}"
    fi
    return 0
  fi

  cp "$src" "$dst"
  log "SYNC ${label}: ${dst}"
}

render_config_template() {
  local src="$1"
  local root_hint="$2"

  python3 - "$src" "$root_hint" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
root_hint = sys.argv[2]
content = src.read_text()
root = root_hint.strip()

if not root:
    match = re.search(r'args = \["run", "(.+?)/cmd/mcp-server/main\.go"\]', content)
    if match:
        root = match.group(1)

if root:
    content = content.replace(root, "${EIGENPHI_BACKEND_ROOT}")

sys.stdout.write(content)
PY
}

sync_rendered_config() {
  local src="$1"
  local dst="$2"

  if [[ ! -f "$src" ]]; then
    log "SKIP config: source not found (${src})"
    return 0
  fi

  mkdir -p "$(dirname "$dst")"
  local rendered_tmp
  rendered_tmp="$(mktemp)"
  render_config_template "$src" "$EIGENPHI_BACKEND_ROOT" > "$rendered_tmp"

  if [[ "$DRY_RUN" == "true" ]]; then
    if [[ ! -f "$dst" ]]; then
      log "CREATE config.template.toml: ${dst}"
    elif cmp -s "$rendered_tmp" "$dst"; then
      log "UNCHANGED config.template.toml: ${dst}"
    else
      log "UPDATE config.template.toml: ${dst}"
    fi
    rm -f "$rendered_tmp"
    return 0
  fi

  cp "$rendered_tmp" "$dst"
  rm -f "$rendered_tmp"
  log "SYNC config.template.toml: ${dst}"
}

sync_tree() {
  local src="$1"
  local dst="$2"
  shift 2
  local -a excludes=("$@")
  local -a rsync_args=(-ai)

  if [[ "$DRY_RUN" == "true" ]]; then
    rsync_args=(-ain)
  fi

  if [[ ! -d "$src" ]]; then
    log "SKIP tree: source not found (${src})"
    return 0
  fi

  mkdir -p "$dst"

  local -a cmd=(rsync "${rsync_args[@]}")
  local pattern
  for pattern in "${excludes[@]}"; do
    cmd+=(--exclude "$pattern")
  done
  cmd+=("${src}/" "${dst}/")
  "${cmd[@]}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
      shift 2
      ;;
    --codex-home)
      CODEX_HOME="${2:-}"
      shift 2
      ;;
    --eigenphi-backend-root)
      EIGENPHI_BACKEND_ROOT="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --skip-agents)
      SKIP_AGENTS="true"
      shift
      ;;
    --skip-skills)
      SKIP_SKILLS="true"
      shift
      ;;
    --skip-workflow)
      SKIP_WORKFLOW="true"
      shift
      ;;
    --skip-config)
      SKIP_CONFIG="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$REPO_ROOT" ]]; then
  echo "--repo-root is required" >&2
  usage
  exit 1
fi

if [[ ! -d "$REPO_ROOT/codex" ]]; then
  echo "Repo codex directory not found: ${REPO_ROOT}/codex" >&2
  exit 1
fi

if [[ ! -d "$CODEX_HOME" ]]; then
  echo "Codex home not found: ${CODEX_HOME}" >&2
  exit 1
fi

log "Repo root: ${REPO_ROOT}"
log "Codex home: ${CODEX_HOME}"
log "Mode: $([[ "$DRY_RUN" == "true" ]] && echo dry-run || echo apply)"

if [[ "$SKIP_AGENTS" != "true" ]]; then
  sync_file "${CODEX_HOME}/AGENTS.md" "${REPO_ROOT}/codex/AGENTS.md" "AGENTS.md"
fi

if [[ "$SKIP_SKILLS" != "true" ]]; then
  sync_tree \
    "${CODEX_HOME}/skills" \
    "${REPO_ROOT}/codex/skills" \
    ".backup-skills/" \
    "__pycache__/" \
    "*.pyc" \
    ".DS_Store"
fi

if [[ "$SKIP_WORKFLOW" != "true" ]]; then
  sync_tree \
    "${CODEX_HOME}/workflow" \
    "${REPO_ROOT}/codex/workflow" \
    "memory/" \
    "__pycache__/" \
    "*.pyc" \
    ".DS_Store"
fi

if [[ "$SKIP_CONFIG" != "true" ]]; then
  sync_rendered_config \
    "${CODEX_HOME}/config.toml" \
    "${REPO_ROOT}/codex/config.template.toml"
fi

log "Import complete."
