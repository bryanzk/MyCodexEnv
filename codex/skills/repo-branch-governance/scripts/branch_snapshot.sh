#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  echo "ERROR: run inside a git repository." >&2
  exit 1
fi
cd "${repo_root}"

main_branch="${MAIN_BRANCH:-main}"

if ! git show-ref --verify --quiet "refs/heads/${main_branch}"; then
  echo "ERROR: local branch '${main_branch}' not found." >&2
  exit 1
fi

git fetch --all --prune >/dev/null

echo "== Branch Snapshot =="
echo "repo=${repo_root}"
echo "main_branch=${main_branch}"
echo

echo "-- Branch Table (vs main) --"
printf "branch\tupstream\tahead_main\tbehind_main\tlast_commit_utc\n"
while IFS= read -r branch; do
  upstream="$(git for-each-ref --format='%(upstream:short)' "refs/heads/${branch}")"
  if [[ -z "${upstream}" ]]; then
    upstream="-"
  fi
  counts="$(git rev-list --left-right --count "${main_branch}...${branch}")"
  behind_main="$(awk '{print $1}' <<<"${counts}")"
  ahead_main="$(awk '{print $2}' <<<"${counts}")"
  last_commit_utc="$(git log -1 --format=%cI "${branch}")"
  printf "%s\t%s\t%s\t%s\t%s\n" "${branch}" "${upstream}" "${ahead_main}" "${behind_main}" "${last_commit_utc}"
done < <(git for-each-ref --sort=refname --format='%(refname:short)' refs/heads)

echo
echo "-- Merged Into ${main_branch} --"
git branch --merged "${main_branch}"

echo
echo "-- Not Merged Into ${main_branch} --"
git branch --no-merged "${main_branch}"

echo
echo "-- Worktrees --"
git worktree list

echo
echo "-- Remote Summary (origin) --"
git remote show origin
