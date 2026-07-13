#!/usr/bin/env bash
set -euo pipefail

# Run this from Terminal only after the Codex Desktop/CLI processes are closed.
# The selected JSONL files must already exist in the timestamped backup.

BACKUP_DIR="${1:-$HOME/Codes/Codex/codex-backups/codex-fluent-20260710-1800}"
ARCHIVE_DIR="$HOME/.codex/archived_sessions"
HANDOFF_FILE="docs/handoffs/2026-07-10-codex-fluent-top-session-archive-handoffs.md"

if [[ ! -f "$HANDOFF_FILE" ]]; then
  echo "handoff file is missing: $HANDOFF_FILE" >&2
  exit 2
fi

if [[ ! -f "$BACKUP_DIR/2026-07-10-codex-fluent-top-session-archive-handoffs.md" ]]; then
  echo "backup handoff is missing: $BACKUP_DIR" >&2
  exit 2
fi

active_processes="$({
  ps -axo pid=,command=
} | awk '
  {
    pid = $1
    $1 = ""
    sub(/^[[:space:]]+/, "", $0)
    if ($0 ~ /(^|[[:space:]])codex([[:space:]]|$)/ || $0 ~ /\/codex([_-]|[[:space:]]|$)/) {
      print pid ": " $0
    }
  }
')"
if [[ -n "$active_processes" ]]; then
  echo "Codex is still running; close Codex and retry." >&2
  echo "$active_processes" >&2
  exit 3
fi

sources=(
  "$HOME/.codex/sessions/2026/05/13/rollout-2026-05-13T06-50-47-019e20f5-eb24-7a32-aee3-1e437f0be7f5.jsonl"
  "$HOME/.codex/sessions/2026/04/20/rollout-2026-04-20T20-08-09-019dad5d-a726-7241-af6d-49481862bfb3.jsonl"
  "$HOME/.codex/sessions/2026/05/11/rollout-2026-05-11T22-50-05-019e1a17-73cc-7ee3-8f87-d6e874d46079.jsonl"
  "$HOME/.codex/sessions/2026/01/07/rollout-2026-01-07T10-44-59-019b9921-f9e6-72d0-bff9-b6481c3992d6.jsonl"
  "$HOME/.codex/sessions/2026/06/02/rollout-2026-06-02T08-26-36-019e884c-d369-75f0-9a7f-71ad9e013f4c.jsonl"
  "$HOME/.codex/sessions/2026/05/06/rollout-2026-05-06T16-40-14-019dff05-0df0-7701-b08d-716973155c5a.jsonl"
  "$HOME/.codex/sessions/2026/04/28/rollout-2026-04-28T08-25-10-019dd40c-efc3-7b21-ac67-9157568c3271.jsonl"
  "$HOME/.codex/sessions/2026/05/20/rollout-2026-05-20T09-33-14-019e4597-2942-7503-a85a-8d147957bb85.jsonl"
  "$HOME/.codex/sessions/2026/05/23/rollout-2026-05-23T12-53-31-019e55c1-9ab4-7543-afec-c7e85d7d8afb.jsonl"
  "$HOME/.codex/sessions/2026/02/24/rollout-2026-02-24T09-39-47-019c9017-87be-7581-8bce-b73025f83a8b.jsonl"
  "$HOME/.codex/sessions/2026/05/26/rollout-2026-05-26T17-13-20-019e6622-89e2-7ce1-af85-35cc59395e50.jsonl"
  "$HOME/.codex/sessions/2026/05/02/rollout-2026-05-02T10-32-34-019de91b-034e-7150-bb8a-301a4a77c2f7.jsonl"
  "$HOME/.codex/sessions/2026/05/15/rollout-2026-05-15T09-31-03-019e2bd5-5d30-7e33-b706-d00d66b23160.jsonl"
  "$HOME/.codex/sessions/2026/06/04/rollout-2026-06-04T09-52-24-019e92e8-15b5-7643-907c-d79ce62844d3.jsonl"
)

for source in "${sources[@]}"; do
  base="${source##*/}"
  backup="$BACKUP_DIR/sessions/$base"
  destination="$ARCHIVE_DIR/$base"
  [[ -f "$source" ]] || { echo "source is missing: $source" >&2; exit 4; }
  [[ -f "$backup" ]] || { echo "backup is missing: $backup" >&2; exit 4; }
  [[ ! -e "$destination" ]] || { echo "archive destination already exists: $destination" >&2; exit 5; }
  source_hash="$(shasum -a 256 "$source" | awk '{print $1}')"
  backup_hash="$(shasum -a 256 "$backup" | awk '{print $1}')"
  [[ "$source_hash" == "$backup_hash" ]] || {
    echo "backup hash mismatch: $base" >&2
    exit 6
  }
done

mkdir -p "$ARCHIVE_DIR"
for source in "${sources[@]}"; do
  base="${source##*/}"
  mv "$source" "$ARCHIVE_DIR/$base"
done

for source in "${sources[@]}"; do
  base="${source##*/}"
  [[ ! -e "$source" ]] || { echo "source still exists: $source" >&2; exit 7; }
  [[ -f "$ARCHIVE_DIR/$base" ]] || { echo "archive file is missing: $base" >&2; exit 7; }
done

echo "archived ${#sources[@]} sessions to $ARCHIVE_DIR"
python3 codex/skills/codex-fluent/scripts/report_active_sessions.py \
  --codex-home "$HOME/.codex" --older-than-days 30 --limit 30 --format markdown \
  | sed -n '1,12p'
