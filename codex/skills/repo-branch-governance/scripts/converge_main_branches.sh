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
  converge_main_branches.sh [--main main] [--remote origin] [--apply]

Behavior:
  - Default: dry-run. Only print ahead/behind and merge plan.
  - --apply: merge every ahead-only local branch into main with --ff-only, then push main.

Rules:
  - Merge candidates are branches with main...branch = 0/N (N>0).
  - Branches behind main or diverged are never merged by this script.
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

git fetch --all --prune >/dev/null

current_branch="$(git branch --show-current)"

if [[ "${apply_changes}" == "true" ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: working tree is dirty. stash/commit first." >&2
    exit 1
  fi
fi

declare -a candidates=()
declare -a skipped=()

echo "mode=$([[ "${apply_changes}" == "true" ]] && echo apply || echo dry-run) main=${main_branch} remote=${remote_name}"
printf "branch\tahead_main\tbehind_main\tdecision\n"
while IFS= read -r branch; do
  if [[ "${branch}" == "${main_branch}" ]]; then
    continue
  fi
  counts="$(git rev-list --left-right --count "${main_branch}...${branch}")"
  behind_main="$(awk '{print $1}' <<<"${counts}")"
  ahead_main="$(awk '{print $2}' <<<"${counts}")"

  if [[ "${behind_main}" -eq 0 && "${ahead_main}" -gt 0 ]]; then
    decision="merge_candidate"
    candidates+=("${branch}")
  elif [[ "${behind_main}" -gt 0 && "${ahead_main}" -eq 0 ]]; then
    decision="skip_behind_only"
    skipped+=("${branch}")
  elif [[ "${behind_main}" -gt 0 && "${ahead_main}" -gt 0 ]]; then
    decision="skip_diverged"
    skipped+=("${branch}")
  else
    decision="skip_synced"
  fi
  printf "%s\t%s\t%s\t%s\n" "${branch}" "${ahead_main}" "${behind_main}" "${decision}"
done < <(git for-each-ref --sort=refname --format='%(refname:short)' refs/heads)

if [[ "${#candidates[@]}" -eq 0 ]]; then
  echo "No ahead-only branches to merge."
  exit 0
fi

echo
echo "merge_candidates=${candidates[*]}"
if [[ "${apply_changes}" != "true" ]]; then
  echo "Dry-run complete. Re-run with --apply to execute."
  exit 0
fi

if [[ "${current_branch}" != "${main_branch}" ]]; then
  git checkout "${main_branch}"
fi
git pull --ff-only "${remote_name}" "${main_branch}"

for branch in "${candidates[@]}"; do
  echo "Merging ${branch} -> ${main_branch}"
  git merge --ff-only "${branch}"
done

git push "${remote_name}" "${main_branch}"

echo "Converge complete."
if [[ "${current_branch}" != "${main_branch}" ]]; then
  if git show-ref --verify --quiet "refs/heads/${current_branch}"; then
    git checkout "${current_branch}" || true
  fi
fi
