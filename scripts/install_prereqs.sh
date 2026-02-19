#!/usr/bin/env bash
set -euo pipefail

# 安装并验证 bootstrap 依赖。
NON_INTERACTIVE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive)
      NON_INTERACTIVE="true"
      shift
      ;;
    -h|--help)
      echo "Usage: install_prereqs.sh [--non-interactive]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

ensure_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi

  if [[ "${NON_INTERACTIVE}" == "true" ]]; then
    echo "Homebrew not found; non-interactive mode cannot install it automatically." >&2
    exit 1
  fi

  echo "Homebrew not found. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
}

ensure_formula() {
  local formula="$1"
  if brew list --formula "${formula}" >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing formula: ${formula}"
  brew install "${formula}"
}

ensure_cask() {
  local cask="$1"
  if brew list --cask "${cask}" >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing cask: ${cask}"
  brew install --cask "${cask}"
}

ensure_homebrew

# 这里使用 Homebrew 统一安装，保证 fresh 机器可复现。
ensure_formula git
ensure_formula jq
ensure_formula ripgrep
ensure_formula node
ensure_formula pnpm
ensure_formula uv
ensure_formula go
ensure_cask codex

for cmd in git jq rg node npm npx pnpm uv go codex; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Required command not found after installation: ${cmd}" >&2
    exit 1
  fi
done

codex_version_raw="$(codex --version | awk '{print $2}')"
if [[ "${codex_version_raw}" != 0.104.0* ]]; then
  echo "Expected codex version prefix 0.104.0, got: ${codex_version_raw}" >&2
  exit 1
fi

echo "Prerequisites verified. codex=${codex_version_raw}"
