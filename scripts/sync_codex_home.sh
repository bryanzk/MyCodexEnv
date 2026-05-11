#!/usr/bin/env bash
set -euo pipefail

# 同步仓库配置到目标 Codex home，并固定 superpowers 版本。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
EIGENPHI_BACKEND_ROOT=""
SKIP_SUPERPOWERS_SYNC="false"
SYNC_AGENTS_ONLY="false"

usage() {
  cat <<USAGE
Usage: sync_codex_home.sh --repo-root <path> [--eigenphi-backend-root <path>] [--codex-home <path>] [--skip-superpowers-sync] [--sync-agents-only]

Options:
  --eigenphi-backend-root   Optional legacy argument; EigenPhi MCP is disabled by default.
USAGE
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
    --skip-superpowers-sync)
      SKIP_SUPERPOWERS_SYNC="true"
      shift
      ;;
    --sync-agents-only)
      SYNC_AGENTS_ONLY="true"
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

if [[ -z "${REPO_ROOT}" ]]; then
  echo "--repo-root is required" >&2
  usage
  exit 1
fi

if [[ ! -d "${REPO_ROOT}" ]]; then
  echo "Repo root does not exist: ${REPO_ROOT}" >&2
  exit 1
fi

mkdir -p "${CODEX_HOME}"

sync_codex_remote_docs() {
  local source target backup
  for filename in remote-access.md remote-hosts.md; do
    source="${REPO_ROOT}/codex/${filename}"
    target="${CODEX_HOME}/${filename}"
    if [[ ! -f "${source}" ]]; then
      echo "Missing Codex remote doc source: ${source}" >&2
      exit 1
    fi
    if [[ -f "${target}" ]]; then
      backup="${target}.backup.$(date +%Y%m%d%H%M%S)"
      cp "${target}" "${backup}"
      echo "Backed up existing ${filename} to ${backup}"
    fi
    cp "${source}" "${target}"
    echo "Codex ${filename} synchronized: ${target}"
  done
}

if [[ "${SYNC_AGENTS_ONLY}" == "true" ]]; then
  AGENTS_SOURCE="${REPO_ROOT}/codex/AGENTS.md"
  AGENTS_TARGET="${CODEX_HOME}/AGENTS.md"
  if [[ ! -f "${AGENTS_SOURCE}" ]]; then
    echo "Missing AGENTS source: ${AGENTS_SOURCE}" >&2
    exit 1
  fi
  if [[ -f "${AGENTS_TARGET}" ]]; then
    backup="${AGENTS_TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    cp "${AGENTS_TARGET}" "${backup}"
    echo "Backed up existing AGENTS to ${backup}"
  fi
  cp "${AGENTS_SOURCE}" "${AGENTS_TARGET}"
  echo "Codex AGENTS synchronized: ${AGENTS_TARGET}"
  sync_codex_remote_docs
  if [[ -f "${REPO_ROOT}/codex/hooks.json" ]]; then
    cp "${REPO_ROOT}/codex/hooks.json" "${CODEX_HOME}/hooks.json"
    echo "Codex hooks config synchronized: ${CODEX_HOME}/hooks.json"
  fi
  if [[ -d "${REPO_ROOT}/codex/hooks" ]]; then
    mkdir -p "${CODEX_HOME}/hooks"
    rsync -a --delete "${REPO_ROOT}/codex/hooks/" "${CODEX_HOME}/hooks/"
    echo "Codex hook scripts synchronized: ${CODEX_HOME}/hooks/"
  fi
  if [[ -d "${REPO_ROOT}/codex/runtime" ]]; then
    mkdir -p "${CODEX_HOME}/runtime"
    rsync -a --delete "${REPO_ROOT}/codex/runtime/" "${CODEX_HOME}/runtime/"
    echo "Codex runtime policy synchronized: ${CODEX_HOME}/runtime/"
  fi
  if [[ -d "${REPO_ROOT}/codex/zsh" ]]; then
    mkdir -p "${CODEX_HOME}/zsh"
    rsync -a --delete "${REPO_ROOT}/codex/zsh/" "${CODEX_HOME}/zsh/"
    echo "Codex zsh helpers synchronized: ${CODEX_HOME}/zsh/"
  fi
  CONFIG_TARGET="${CODEX_HOME}/config.toml"
  if [[ -f "${CONFIG_TARGET}" ]]; then
    python3 - "${CONFIG_TARGET}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

if re.search(r"^codex_hooks\s*=", text, flags=re.MULTILINE):
    updated = re.sub(r"^codex_hooks\s*=.*$", "codex_hooks = true", text, count=1, flags=re.MULTILINE)
elif "[features]" in text:
    updated = text.replace("[features]", "[features]\ncodex_hooks = true", 1)
else:
    updated = text.rstrip() + "\n\n[features]\ncodex_hooks = true\n"

if updated != text:
    path.write_text(updated, encoding="utf-8")
PY
    echo "Codex hooks feature enabled in existing config: ${CONFIG_TARGET}"
  else
    echo "[WARN] Missing ${CONFIG_TARGET}; hooks will activate after the next full config sync." >&2
  fi
  exit 0
fi

CONFIG_TARGET="${CODEX_HOME}/config.toml"
if [[ -f "${CONFIG_TARGET}" ]]; then
  backup="${CONFIG_TARGET}.backup.$(date +%Y%m%d%H%M%S)"
  cp "${CONFIG_TARGET}" "${backup}"
  echo "Backed up existing config to ${backup}"
fi

TEMPLATE_PATH="${REPO_ROOT}/codex/config.template.toml"
if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "Missing config template: ${TEMPLATE_PATH}" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to resolve NPM_GLOBAL_BIN for codex config rendering." >&2
  exit 1
fi

npm_global_prefix="$(npm prefix -g)"
if [[ -z "${npm_global_prefix}" ]]; then
  echo "Failed to resolve npm global prefix." >&2
  exit 1
fi

npm_global_bin="${npm_global_prefix}/bin"
escaped_npm_global_bin="$(printf '%s' "${npm_global_bin}" | sed 's/[\/&]/\\&/g')"
rendered_tmp="$(mktemp)"
sed \
  -e "s|\${NPM_GLOBAL_BIN}|${escaped_npm_global_bin}|g" \
  "${TEMPLATE_PATH}" > "${rendered_tmp}"

if rg -n '\$\{[A-Z0-9_]+\}' "${rendered_tmp}" >/dev/null 2>&1; then
  echo "Template rendering failed: unresolved placeholder remains in ${rendered_tmp}" >&2
  rm -f "${rendered_tmp}"
  exit 1
fi

cp "${rendered_tmp}" "${CONFIG_TARGET}"
rm -f "${rendered_tmp}"

mkdir -p "${CODEX_HOME}/skills"
rsync -a --delete "${REPO_ROOT}/codex/skills/" "${CODEX_HOME}/skills/"

if [[ -d "${REPO_ROOT}/codex/workflow" ]]; then
  mkdir -p "${CODEX_HOME}/workflow"
  # workflow/memory 属于运行态热数据，不从仓库模板回灌。
  rsync -a --delete --exclude 'memory/' "${REPO_ROOT}/codex/workflow/" "${CODEX_HOME}/workflow/"
fi

if [[ -f "${REPO_ROOT}/codex/AGENTS.md" ]]; then
  if [[ -f "${CODEX_HOME}/AGENTS.md" ]]; then
    backup="${CODEX_HOME}/AGENTS.md.backup.$(date +%Y%m%d%H%M%S)"
    cp "${CODEX_HOME}/AGENTS.md" "${backup}"
    echo "Backed up existing AGENTS to ${backup}"
  fi
  cp "${REPO_ROOT}/codex/AGENTS.md" "${CODEX_HOME}/AGENTS.md"
fi

sync_codex_remote_docs

if [[ -f "${REPO_ROOT}/codex/hooks.json" ]]; then
  if [[ -f "${CODEX_HOME}/hooks.json" ]]; then
    backup="${CODEX_HOME}/hooks.json.backup.$(date +%Y%m%d%H%M%S)"
    cp "${CODEX_HOME}/hooks.json" "${backup}"
    echo "Backed up existing hooks config to ${backup}"
  fi
  cp "${REPO_ROOT}/codex/hooks.json" "${CODEX_HOME}/hooks.json"
fi

if [[ -d "${REPO_ROOT}/codex/hooks" ]]; then
  mkdir -p "${CODEX_HOME}/hooks"
  rsync -a --delete "${REPO_ROOT}/codex/hooks/" "${CODEX_HOME}/hooks/"
fi

if [[ -d "${REPO_ROOT}/codex/runtime" ]]; then
  mkdir -p "${CODEX_HOME}/runtime"
  rsync -a --delete "${REPO_ROOT}/codex/runtime/" "${CODEX_HOME}/runtime/"
fi

if [[ -d "${REPO_ROOT}/codex/zsh" ]]; then
  mkdir -p "${CODEX_HOME}/zsh"
  rsync -a --delete "${REPO_ROOT}/codex/zsh/" "${CODEX_HOME}/zsh/"
fi

if [[ "${SKIP_SUPERPOWERS_SYNC}" == "true" ]]; then
  echo "Skipping superpowers sync by request."
  exit 0
fi

LOCK_PATH="${REPO_ROOT}/locks/superpowers.lock"
if [[ ! -f "${LOCK_PATH}" ]]; then
  echo "Missing lock file: ${LOCK_PATH}" >&2
  exit 1
fi

repo_url="$(awk -F= '/^repo=/{print $2}' "${LOCK_PATH}" | head -n1)"
commit_sha="$(awk -F= '/^commit=/{print $2}' "${LOCK_PATH}" | head -n1)"
if [[ -z "${repo_url}" || -z "${commit_sha}" ]]; then
  echo "Invalid superpowers lock file." >&2
  exit 1
fi

SUPERPOWERS_DIR="${CODEX_HOME}/superpowers"
if [[ -d "${SUPERPOWERS_DIR}/.git" ]]; then
  if [[ -n "$(git -C "${SUPERPOWERS_DIR}" status --porcelain)" ]]; then
    echo "Local changes detected in ${SUPERPOWERS_DIR}; aborting to avoid data loss." >&2
    exit 1
  fi
  git -C "${SUPERPOWERS_DIR}" fetch --all --tags --prune
else
  git clone "${repo_url}" "${SUPERPOWERS_DIR}"
fi

git -C "${SUPERPOWERS_DIR}" checkout "${commit_sha}"

echo "Codex home synchronized: ${CODEX_HOME}"
