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

declare -A branch_to_worktree=()
current_worktree=""
while IFS= read -r line; do
  key="${line%% *}"
  value="${line#* }"
  if [[ "${key}" == "worktree" ]]; then
    current_worktree="${value}"
  elif [[ "${key}" == "branch" ]]; then
    b="${value#refs/heads/}"
    branch_to_worktree["${b}"]="${current_worktree}"
  fi
done < <(git worktree list --porcelain)

mapfile -t merged_candidates < <(git for-each-ref --format='%(refname:short)' --merged "${main_branch}" refs/heads)

if [[ "${#merged_candidates[@]}" -eq 0 ]]; then
  echo "No merged branches found."
  exit 0
fi

echo "mode=$([[ "${apply_changes}" == "true" ]] && echo apply || echo dry-run) main=${main_branch} remote=${remote_name}"

for branch in "${merged_candidates[@]}"; do
  if [[ "${branch}" == "${main_branch}" || "${branch}" == "${current_branch}" ]]; then
    continue
  fi

  wt_path="${branch_to_worktree[${branch}]:-}"
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
done

if [[ "${apply_changes}" == "true" ]]; then
  git fetch --all --prune >/dev/null
  echo "Cleanup complete."
else
  echo "Dry-run complete. Re-run with --apply to execute."
fi
