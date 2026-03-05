#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=""
MODE="claude"

usage() {
  echo "Usage: workflow_health_check.sh --repo-root <path> [--mode claude|codex]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
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

if [[ -z "$REPO_ROOT" || ! -d "$REPO_ROOT" ]]; then
  echo "Invalid --repo-root: $REPO_ROOT" >&2
  exit 1
fi

fails=0
check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    echo "PASS:file_exists:${path}"
  else
    echo "FAIL:file_exists:${path}"
    fails=$((fails + 1))
  fi
}

check_file "$REPO_ROOT/rules/behaviors.md"
check_file "$REPO_ROOT/rules/skill-triggers.md"
check_file "$REPO_ROOT/rules/memory-flush.md"
check_file "$REPO_ROOT/memory/today.md"
check_file "$REPO_ROOT/memory/active-tasks.json"

if rg -n "verification-before-completion|systematic-debugging|session-end" "$REPO_ROOT/rules/skill-triggers.md" >/dev/null 2>&1; then
  echo "PASS:trigger_core_skills_present"
else
  echo "FAIL:trigger_core_skills_present"
  fails=$((fails + 1))
fi

if [[ "$MODE" == "codex" ]]; then
  if [[ -x "$REPO_ROOT/scripts/scan_skill_security.sh" ]]; then
    echo "PASS:security_scan_script_executable"
  else
    echo "FAIL:security_scan_script_executable"
    fails=$((fails + 1))
  fi
fi

if [[ $fails -gt 0 ]]; then
  echo "Health check failed: $fails" >&2
  exit 1
fi

echo "Health check passed"
