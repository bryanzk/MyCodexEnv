#!/usr/bin/env bash
set -euo pipefail

# 安装并验证 bootstrap 依赖。
NON_INTERACTIVE="false"
CHROME_DEVTOOLS_MCP_VERSION="0.20.0"
ACCEPTED_CODEX_VERSION_PREFIXES=("0.104.0" "0.130.0")

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

ensure_google_chrome() {
  if open -Ra "Google Chrome" >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing cask: google-chrome"
  brew install --cask google-chrome
}

ensure_npm_package() {
  local package="$1"
  local version="$2"
  local installed_version=""

  installed_version="$(
    npm list -g --depth=0 --json "${package}" 2>/dev/null \
      | jq -r --arg package "${package}" '.dependencies[$package].version // empty' \
      || true
  )"

  if [[ "${installed_version}" == "${version}" ]]; then
    return 0
  fi

  echo "Installing npm package: ${package}@${version}"
  npm install -g "${package}@${version}"
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
ensure_google_chrome
ensure_npm_package chrome-devtools-mcp "${CHROME_DEVTOOLS_MCP_VERSION}"

for cmd in git jq rg node npm npx pnpm uv go codex; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Required command not found after installation: ${cmd}" >&2
    exit 1
  fi
done

npm_global_bin="$(npm prefix -g)/bin"
if [[ ! -x "${npm_global_bin}/chrome-devtools-mcp" ]]; then
  echo "Required MCP binary not found after installation: ${npm_global_bin}/chrome-devtools-mcp" >&2
  exit 1
fi

codex_version_raw="$(codex --version | awk '{print $2}')"
codex_version_ok="false"
for accepted_prefix in "${ACCEPTED_CODEX_VERSION_PREFIXES[@]}"; do
  if [[ "${codex_version_raw}" == "${accepted_prefix}"* ]]; then
    codex_version_ok="true"
    break
  fi
done
if [[ "${codex_version_ok}" != "true" ]]; then
  echo "Expected codex version prefix in [${ACCEPTED_CODEX_VERSION_PREFIXES[*]}], got: ${codex_version_raw}" >&2
  exit 1
fi

echo "Prerequisites verified. codex=${codex_version_raw}"
