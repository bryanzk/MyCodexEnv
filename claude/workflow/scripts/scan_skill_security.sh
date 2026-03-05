#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scan_skill_security.sh <skill_or_dir> [more_paths...]" >&2
  exit 1
fi

status=0
patterns=(
  'https?://'
  'curl[[:space:]]+'
  'requests\.post\('
  'fetch\('
  'axios\.'
  'upload|backup to|exfiltrat'
  'zip[[:space:]]|tar[[:space:]]'
  'rm -rf|shred|encrypt'
  'base64|eval\(|exec\('
)

for target in "$@"; do
  if [[ ! -e "$target" ]]; then
    echo "[WARN] Path not found: $target"
    continue
  fi

  if [[ -d "$target" ]]; then
    files=("$(find "$target" -type f \( -name 'SKILL.md' -o -name '*.md' -o -name '*.sh' -o -name '*.py' \))")
  else
    files=("$target")
  fi

  echo "[SCAN] $target"
  for pattern in "${patterns[@]}"; do
    if rg -n --no-heading -e "$pattern" "$target" >/tmp/skill_scan_hits.txt 2>/dev/null; then
      if [[ -s /tmp/skill_scan_hits.txt ]]; then
        echo "  [RED_FLAG] pattern=$pattern"
        sed 's/^/    /' /tmp/skill_scan_hits.txt
        status=2
      fi
    fi
  done

done

if [[ $status -eq 0 ]]; then
  echo "✅ Skill security scan passed"
else
  echo "⚠️ Skill security scan found red flags; require explicit confirmation before enable"
fi

exit $status
