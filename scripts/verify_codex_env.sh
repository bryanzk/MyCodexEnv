#!/usr/bin/env bash
set -euo pipefail

# 对复现后的环境做一致性校验，并记录测试证据。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"

usage() {
  echo "Usage: verify_codex_env.sh --repo-root <path> [--codex-home <path>]"
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

lock_path="${REPO_ROOT}/locks/superpowers.lock"
if [[ ! -f "${lock_path}" ]]; then
  echo "Missing lock file: ${lock_path}" >&2
  exit 1
fi

expected_commit="$(awk -F= '/^commit=/{print $2}' "${lock_path}" | head -n1)"
if [[ -z "${expected_commit}" ]]; then
  echo "Missing commit in lock file" >&2
  exit 1
fi

check() {
  local name="$1"
  local cmd="$2"
  if bash -c "${cmd}" >/dev/null 2>&1; then
    echo "PASS:${name}"
  else
    echo "FAIL:${name}"
  fi
}

results=()
results+=("$(check os_darwin '[[ "$(uname -s)" == "Darwin" ]]')")
results+=("$(check arch_arm64 '[[ "$(uname -m)" == "arm64" ]]')")
results+=("$(check cmd_codex 'command -v codex')")
results+=("$(check cmd_go 'command -v go')")
results+=("$(check cmd_node 'command -v node && command -v npx')")
results+=("$(check codex_home_exists '[[ -d "'"${CODEX_HOME}"'" ]]')")
results+=("$(check config_exists '[[ -f "'"${CODEX_HOME}"'"/config.toml ]]')")
results+=("$(check agents_exists '[[ -f "'"${CODEX_HOME}"'"/AGENTS.md ]]')")
results+=("$(check config_has_mcp 'rg -n "\[mcp_servers\.\"eigenphi-blockchain\"\]" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check config_placeholder_resolved '! rg -n "\$\{EIGENPHI_BACKEND_ROOT\}" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check superpowers_git '[[ -d "'"${CODEX_HOME}"'"/superpowers/.git ]]')")
results+=("$(check superpowers_commit '[[ "$(git -C "'"${CODEX_HOME}"'"/superpowers rev-parse --short HEAD)" == "'"${expected_commit}"'"* ]]')")

repo_skills_count="$(find "${REPO_ROOT}/codex/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
codex_skills_count="$(find "${CODEX_HOME}/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
if [[ "${repo_skills_count}" == "${codex_skills_count}" ]]; then
  results+=("PASS:skills_count_match")
else
  results+=("FAIL:skills_count_match")
fi

codex_version="$(codex --version | awk '{print $2}')"
if [[ "${codex_version}" == 0.104.0* ]]; then
  results+=("PASS:codex_version")
else
  results+=("FAIL:codex_version")
fi

if codex login status >/dev/null 2>&1; then
  login_status="authenticated"
else
  login_status="not_authenticated"
fi

failed=0
for line in "${results[@]}"; do
  echo "${line}"
  if [[ "${line}" == FAIL:* ]]; then
    failed=$((failed + 1))
  fi
done

report_file="${REPO_ROOT}/TEST_VERIFICATION.md"
{
  echo ""
  echo "## Codex Env Verification ($(date '+%Y-%m-%d %H:%M:%S'))"
  echo "- codex_home: ${CODEX_HOME}"
  echo "- codex_version: ${codex_version}"
  echo "- repo_skills_count: ${repo_skills_count}"
  echo "- codex_skills_count: ${codex_skills_count}"
  echo "- expected_superpowers_commit: ${expected_commit}"
  echo "- auth_status: ${login_status}"
  echo ""
  echo "### Checks"
  for line in "${results[@]}"; do
    status="${line%%:*}"
    name="${line#*:}"
    if [[ "${status}" == "PASS" ]]; then
      echo "- [x] ${name}"
    else
      echo "- [ ] ${name}"
    fi
  done
  echo ""
} >> "${report_file}"

if [[ ${failed} -gt 0 ]]; then
  echo "Verification failed with ${failed} failed checks." >&2
  exit 1
fi

echo "Verification passed."
if [[ "${login_status}" == "not_authenticated" ]]; then
  echo "Run 'codex login' to authenticate this machine."
fi
