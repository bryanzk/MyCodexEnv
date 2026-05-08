#!/usr/bin/env bash
set -euo pipefail

# 入口脚本：clone 后只需执行本脚本即可完成环境复现。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

EIGENPHI_BACKEND_ROOT=""
CODEX_HOME="${HOME}/.codex"
CLAUDE_HOME="${HOME}/.claude"
NON_INTERACTIVE="false"

usage() {
  cat <<USAGE
Usage: ./bootstrap.sh [--eigenphi-backend-root <path>] [--codex-home <path>] [--claude-home <path>] [--non-interactive]

Options:
  --eigenphi-backend-root   本地 eigenphi backend 源码根目录（可选；EigenPhi MCP 默认禁用）
  --codex-home              Codex home 目录（默认: ~/.codex）
  --claude-home             Claude home 目录（默认: ~/.claude）
  --non-interactive         非交互模式（缺少 Homebrew 时直接失败）
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --eigenphi-backend-root)
      EIGENPHI_BACKEND_ROOT="${2:-}"
      shift 2
      ;;
    --codex-home)
      CODEX_HOME="${2:-}"
      shift 2
      ;;
    --claude-home)
      CLAUDE_HOME="${2:-}"
      shift 2
      ;;
    --non-interactive)
      NON_INTERACTIVE="true"
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

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This bootstrap only supports macOS (Darwin)." >&2
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "This bootstrap only supports Apple Silicon (arm64)." >&2
  exit 1
fi

echo "[1/5] Installing prerequisites..."
"${SCRIPT_DIR}/scripts/install_prereqs.sh" $( [[ "${NON_INTERACTIVE}" == "true" ]] && echo "--non-interactive" )

echo "[2/5] Syncing Codex home content..."
sync_args=(
  --repo-root "${SCRIPT_DIR}" \
  --codex-home "${CODEX_HOME}"
)
if [[ -n "${EIGENPHI_BACKEND_ROOT}" ]]; then
  sync_args+=(--eigenphi-backend-root "${EIGENPHI_BACKEND_ROOT}")
fi
"${SCRIPT_DIR}/scripts/sync_codex_home.sh" "${sync_args[@]}"

echo "[3/5] Syncing Claude workflow content..."
"${SCRIPT_DIR}/scripts/sync_claude_home.sh" \
  --repo-root "${SCRIPT_DIR}" \
  --claude-home "${CLAUDE_HOME}"

SUPERPOWERS_BIN="${CODEX_HOME}/superpowers/.codex/superpowers-codex"
if [[ -x "${SUPERPOWERS_BIN}" ]]; then
  echo "[4/5] Running superpowers bootstrap..."
  "${SUPERPOWERS_BIN}" bootstrap >/dev/null
else
  echo "[WARN] superpowers bootstrap binary not found at ${SUPERPOWERS_BIN}" >&2
fi

echo "[5/5] Verifying environment..."
"${SCRIPT_DIR}/scripts/verify_codex_env.sh" \
  --repo-root "${SCRIPT_DIR}" \
  --codex-home "${CODEX_HOME}" \
  --claude-home "${CLAUDE_HOME}"

echo "Bootstrap finished."
if codex login status >/dev/null 2>&1; then
  echo "Authentication appears configured."
else
  echo "Run 'codex login' to authenticate on this machine."
fi
