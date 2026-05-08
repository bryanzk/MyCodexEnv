#!/usr/bin/env bash
set -euo pipefail

# 对复现后的双环境做一致性校验，并记录测试证据。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
CLAUDE_HOME="${HOME}/.claude"

usage() {
  echo "Usage: verify_codex_env.sh --repo-root <path> [--codex-home <path>] [--claude-home <path>]"
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
    --claude-home)
      CLAUDE_HOME="${2:-}"
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
results+=("$(check chrome_devtools_mcp_bin_exists '[[ -x "$(npm prefix -g)/bin/chrome-devtools-mcp" ]]')")
results+=("$(check app_google_chrome 'open -Ra "Google Chrome"')")

results+=("$(check codex_home_exists '[[ -d "'"${CODEX_HOME}"'" ]]')")
results+=("$(check codex_config_exists '[[ -f "'"${CODEX_HOME}"'"/config.toml ]]')")
results+=("$(check codex_agents_source_exists '[[ -f "'"${REPO_ROOT}"'"/codex/AGENTS.md ]]')")
results+=("$(check codex_agents_exists '[[ -f "'"${CODEX_HOME}"'"/AGENTS.md ]]')")
results+=("$(check codex_remote_access_source_exists '[[ -f "'"${REPO_ROOT}"'"/codex/remote-access.md ]]')")
results+=("$(check codex_remote_access_exists '[[ -f "'"${CODEX_HOME}"'"/remote-access.md ]]')")
results+=("$(check codex_remote_hosts_source_exists '[[ -f "'"${REPO_ROOT}"'"/codex/remote-hosts.md ]]')")
results+=("$(check codex_remote_hosts_exists '[[ -f "'"${CODEX_HOME}"'"/remote-hosts.md ]]')")
results+=("$(check codex_hooks_source_exists '[[ -f "'"${REPO_ROOT}"'"/codex/hooks.json ]]')")
results+=("$(check codex_hooks_exists '[[ -f "'"${CODEX_HOME}"'"/hooks.json ]]')")
results+=("$(check codex_hook_script_exists '[[ -f "'"${CODEX_HOME}"'"/hooks/session_start_require_naming.py ]]')")
results+=("$(check codex_zsh_title_hook_exists '[[ -f "'"${CODEX_HOME}"'"/zsh/codex-session-title.zsh ]]')")
results+=("$(check codex_config_eigenphi_mcp_disabled '! rg -n "^[[:space:]]*\[mcp_servers\.\"eigenphi-blockchain\"\]" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_config_has_chrome_devtools_mcp 'rg -n "\[mcp_servers\.\"chrome-devtools\"\]" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_config_chrome_devtools_no_usage_statistics 'rg -n -- "--no-usage-statistics" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_config_chrome_devtools_no_performance_crux 'rg -n -- "--no-performance-crux" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_config_hooks_enabled 'rg -n "^codex_hooks = true$" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_config_placeholder_resolved '! rg -n "\$\{[A-Z0-9_]+\}" "'"${CODEX_HOME}"'"/config.toml')")
results+=("$(check codex_superpowers_git '[[ -d "'"${CODEX_HOME}"'"/superpowers/.git ]]')")
results+=("$(check codex_superpowers_commit '[[ "$(git -C "'"${CODEX_HOME}"'"/superpowers rev-parse --short HEAD)" == "'"${expected_commit}"'"* ]]')")
results+=("$(check codex_workflow_exists '[[ -d "'"${CODEX_HOME}"'"/workflow ]]')")
results+=("$(check codex_workflow_rules '[[ -f "'"${CODEX_HOME}"'"/workflow/rules/behaviors.md ]]')")
results+=("$(check codex_agents_has_gate 'rg -n "P0 强制验证门禁|Verification Gate" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_has_layering 'rg -n "^## Layering$" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_has_remote_operations 'rg -n "^## Remote Operations$" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_routes_remote_access 'rg -n "remote-access.md" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_has_repo_expectations 'rg -n "^## Repo AGENTS Expectations$" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_session_naming_rule 'rg -n "<项目缩写>-<YYYYMMDD>-<概要>" "'"${CODEX_HOME}"'"/AGENTS.md')")
results+=("$(check codex_agents_runtime_matches_source 'cmp -s "'"${REPO_ROOT}"'"/codex/AGENTS.md "'"${CODEX_HOME}"'"/AGENTS.md' )")
results+=("$(check codex_remote_access_runtime_matches_source 'cmp -s "'"${REPO_ROOT}"'"/codex/remote-access.md "'"${CODEX_HOME}"'"/remote-access.md' )")
results+=("$(check codex_remote_hosts_runtime_matches_source 'cmp -s "'"${REPO_ROOT}"'"/codex/remote-hosts.md "'"${CODEX_HOME}"'"/remote-hosts.md' )")
results+=("$(check codex_hooks_runtime_matches_source 'cmp -s "'"${REPO_ROOT}"'"/codex/hooks.json "'"${CODEX_HOME}"'"/hooks.json' )")
results+=("$(check codex_zsh_title_runtime_matches_source 'cmp -s "'"${REPO_ROOT}"'"/codex/zsh/codex-session-title.zsh "'"${CODEX_HOME}"'"/zsh/codex-session-title.zsh' )")
results+=("$(check codex_security_scan_script '[[ -x "'"${CODEX_HOME}"'"/workflow/scripts/scan_skill_security.sh ]]')")

for skill in ccwf-session-end ccwf-verification-before-completion ccwf-systematic-debugging ccwf-planning-with-files ccwf-experience-evolution; do
  results+=("$(check "codex_skill_${skill}" '[[ -f "'"${CODEX_HOME}"'"/skills/'"${skill}"'/SKILL.md ]]')")
done

results+=("$(check claude_home_exists '[[ -d "'"${CLAUDE_HOME}"'" ]]')")
results+=("$(check claude_main_exists '[[ -f "'"${CLAUDE_HOME}"'"/CLAUDE.md ]]')")
results+=("$(check claude_workflow_exists '[[ -d "'"${CLAUDE_HOME}"'"/workflow ]]')")
results+=("$(check claude_workflow_rules '[[ -f "'"${CLAUDE_HOME}"'"/workflow/rules/behaviors.md ]]')")
results+=("$(check claude_integration_block 'rg -n "ccwf:integration:start|ccwf:integration:end" "'"${CLAUDE_HOME}"'"/CLAUDE.md')")
results+=("$(check claude_security_scan_script '[[ -x "'"${CLAUDE_HOME}"'"/workflow/scripts/scan_skill_security.sh ]]')")

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
  echo "## Dual Env Verification ($(date '+%Y-%m-%d %H:%M:%S'))"
  echo "- codex_home: ${CODEX_HOME}"
  echo "- claude_home: ${CLAUDE_HOME}"
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
} >> "${report_file}"

if [[ ${failed} -gt 0 ]]; then
  echo "Verification failed with ${failed} failed checks." >&2
  exit 1
fi

echo "Verification passed."
if [[ "${login_status}" == "not_authenticated" ]]; then
  echo "Run 'codex login' to authenticate this machine."
fi
