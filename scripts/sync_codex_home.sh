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
  exit 0
fi

if [[ -z "${EIGENPHI_BACKEND_ROOT}" ]]; then
  echo "--eigenphi-backend-root is required unless --sync-agents-only is used" >&2
  usage
  exit 1
fi

if [[ ! -d "${EIGENPHI_BACKEND_ROOT}" ]]; then
  echo "Invalid eigenphi backend root: ${EIGENPHI_BACKEND_ROOT}" >&2
  exit 1
fi

if [[ ! -f "${EIGENPHI_BACKEND_ROOT}/cmd/mcp-server/main.go" ]]; then
  echo "Missing MCP server entrypoint: ${EIGENPHI_BACKEND_ROOT}/cmd/mcp-server/main.go" >&2
  exit 1
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
escaped_root="$(printf '%s' "${EIGENPHI_BACKEND_ROOT}" | sed 's/[\/&]/\\&/g')"
escaped_npm_global_bin="$(printf '%s' "${npm_global_bin}" | sed 's/[\/&]/\\&/g')"
rendered_tmp="$(mktemp)"
sed \
  -e "s|\${EIGENPHI_BACKEND_ROOT}|${escaped_root}|g" \
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
