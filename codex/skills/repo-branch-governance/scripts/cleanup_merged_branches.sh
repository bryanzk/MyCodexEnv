#!/usr/bin/env bash
set -euo pipefail

main_branch="main"
remote_name="origin"
apply_changes="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --main)
      main_branch="$2"
      shift 2
      ;;
    --remote)
      remote_name="$2"
      shift 2
      ;;
    --apply)
      apply_changes="true"
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  cleanup_merged_branches.sh [--main main] [--remote origin] [--apply]

Behavior:
  - Without --apply: dry-run only (print actions).
  - With --apply: remove merged local branches, attached worktrees, and remote branches.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument '$1'" >&2
      exit 1
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  echo "ERROR: run inside a git repository." >&2
  exit 1
fi
cd "${repo_root}"

if ! git show-ref --verify --quiet "refs/heads/${main_branch}"; then
  echo "ERROR: local branch '${main_branch}' not found." >&2
  exit 1
fi

current_branch="$(git branch --show-current)"

echo "mode=$([[ "${apply_changes}" == "true" ]] && echo apply || echo dry-run) main=${main_branch} remote=${remote_name}"

found_candidate="false"
while IFS= read -r branch; do
  if [[ "${branch}" == "${main_branch}" || "${branch}" == "${current_branch}" ]]; then
    continue
  fi
  found_candidate="true"

  wt_path="$(git worktree list --porcelain | awk -v target="refs/heads/${branch}" '
    $1 == "worktree" { worktree = substr($0, index($0, " ") + 1) }
    $1 == "branch" && $2 == target { print worktree; exit }
  ')"
  if [[ -n "${wt_path}" ]]; then
    echo "[worktree] branch=${branch} path=${wt_path}"
    if [[ "${apply_changes}" == "true" ]]; then
      git worktree remove "${wt_path}"
    fi
  fi

  echo "[local] delete branch=${branch}"
  if [[ "${apply_changes}" == "true" ]]; then
    git branch -d "${branch}"
  fi

  if git ls-remote --exit-code --heads "${remote_name}" "${branch}" >/dev/null 2>&1; then
    echo "[remote] delete ${remote_name}/${branch}"
    if [[ "${apply_changes}" == "true" ]]; then
      git push "${remote_name}" --delete "${branch}"
    fi
  fi
done < <(git for-each-ref --format='%(refname:short)' --merged "${main_branch}" refs/heads)

if [[ "${found_candidate}" != "true" ]]; then
  echo "No merged branches found."
  exit 0
fi

if [[ "${apply_changes}" == "true" ]]; then
  git fetch --all --prune >/dev/null
  echo "Cleanup complete."
else
  echo "Dry-run complete. Re-run with --apply to execute."
fi
