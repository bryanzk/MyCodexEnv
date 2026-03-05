#!/usr/bin/env bash
set -euo pipefail

# 同步仓库内 Claude workflow 到目标 Claude home，并注入集成指令块。
REPO_ROOT=""
CLAUDE_HOME="${HOME}/.claude"

usage() {
  cat <<USAGE
Usage: sync_claude_home.sh --repo-root <path> [--claude-home <path>]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
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

if [[ ! -d "${REPO_ROOT}" ]]; then
  echo "Repo root does not exist: ${REPO_ROOT}" >&2
  exit 1
fi

WORKFLOW_SOURCE="${REPO_ROOT}/claude/workflow"
BLOCK_SOURCE="${REPO_ROOT}/claude/CLAUDE_INTEGRATION_BLOCK.md"
if [[ ! -d "${WORKFLOW_SOURCE}" ]]; then
  echo "Missing workflow source directory: ${WORKFLOW_SOURCE}" >&2
  exit 1
fi
if [[ ! -f "${BLOCK_SOURCE}" ]]; then
  echo "Missing integration block: ${BLOCK_SOURCE}" >&2
  exit 1
fi

mkdir -p "${CLAUDE_HOME}"
mkdir -p "${CLAUDE_HOME}/workflow"
rsync -a --delete "${WORKFLOW_SOURCE}/" "${CLAUDE_HOME}/workflow/"

CLAUDE_MAIN="${CLAUDE_HOME}/CLAUDE.md"
if [[ -f "${CLAUDE_MAIN}" ]]; then
  backup="${CLAUDE_MAIN}.backup.$(date +%Y%m%d%H%M%S)"
  cp "${CLAUDE_MAIN}" "${backup}"
  echo "Backed up existing Claude entry to ${backup}"
fi

START_MARK='<!-- ccwf:integration:start -->'
END_MARK='<!-- ccwf:integration:end -->'
tmp_file="$(mktemp)"

if [[ -f "${CLAUDE_MAIN}" ]]; then
  if rg -n "${START_MARK}" "${CLAUDE_MAIN}" >/dev/null 2>&1; then
    awk -v start="${START_MARK}" -v end="${END_MARK}" -v block_file="${BLOCK_SOURCE}" '
      BEGIN {
        while ((getline line < block_file) > 0) {
          block = block line ORS
        }
        in_block = 0
        replaced = 0
      }
      {
        if ($0 == start) {
          if (replaced == 0) {
            printf "%s", block
            replaced = 1
          }
          in_block = 1
          next
        }
        if (in_block == 1 && $0 == end) {
          in_block = 0
          next
        }
        if (in_block == 0) {
          print
        }
      }
      END {
        if (replaced == 0) {
          print ""
          printf "%s", block
        }
      }
    ' "${CLAUDE_MAIN}" > "${tmp_file}"
  else
    cat "${CLAUDE_MAIN}" > "${tmp_file}"
    echo "" >> "${tmp_file}"
    cat "${BLOCK_SOURCE}" >> "${tmp_file}"
  fi
else
  {
    echo "# Claude Memory Entry"
    echo ""
    cat "${BLOCK_SOURCE}"
  } > "${tmp_file}"
fi

cp "${tmp_file}" "${CLAUDE_MAIN}"
rm -f "${tmp_file}"

echo "Claude home synchronized: ${CLAUDE_HOME}"
