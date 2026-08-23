#!/bin/zsh

set -euo pipefail

codex_root="/Users/kezheng/.codex"
backup_root="/Volumes/BAK4Bryan2T/CodexSessionBak"
snapshots_root="$backup_root/snapshots"
latest_link="$backup_root/latest"
stamp=$(/bin/date -u '+%Y%m%dT%H%M%SZ')
working="$snapshots_root/.incomplete-$stamp"
snapshot="$snapshots_root/$stamp"

abort_if_codex_running() {
  if /usr/bin/pgrep -x Codex >/dev/null ||
    /usr/bin/pgrep -x ChatGPT >/dev/null ||
    /usr/bin/pgrep -x codex >/dev/null; then
    echo "ERROR: quit Codex, ChatGPT, and all Codex CLI sessions first"
    exit 1
  fi
}

abort_if_codex_running

test -d "/Volumes/BAK4Bryan2T" || {
  echo "ERROR: BAK4Bryan2T is not mounted"
  exit 1
}

for required in \
  "$codex_root/sessions" \
  "$codex_root/archived_sessions" \
  "$codex_root/session_index.jsonl" \
  "$codex_root/state_5.sqlite"; do
  test -e "$required" || {
    echo "ERROR: missing $required"
    exit 1
  }
done

if test -e "$latest_link" && ! test -L "$latest_link"; then
  echo "ERROR: $latest_link exists but is not a symlink"
  exit 1
fi

/bin/mkdir -p "$snapshots_root"
/bin/mkdir "$working"

previous=""
if test -L "$latest_link"; then
  previous=$(/usr/bin/readlink "$latest_link")
  test -d "$previous" || {
    echo "ERROR: latest points to a missing snapshot: $previous"
    exit 1
  }
fi

session_link_opts=()
archive_link_opts=()
file_link_opts=()

if test -n "$previous"; then
  session_link_opts=(--link-dest="$previous/sessions")
  archive_link_opts=(--link-dest="$previous/archived_sessions")
  file_link_opts=(--link-dest="$previous")
fi

/usr/bin/rsync -a \
  "${session_link_opts[@]}" \
  "$codex_root/sessions/" \
  "$working/sessions/"

/usr/bin/rsync -a \
  "${archive_link_opts[@]}" \
  "$codex_root/archived_sessions/" \
  "$working/archived_sessions/"

state_sources=(
  "$codex_root/session_index.jsonl"
  "$codex_root/state_5.sqlite"
)

test -f "$codex_root/state_5.sqlite-wal" &&
  state_sources+=("$codex_root/state_5.sqlite-wal")

test -f "$codex_root/state_5.sqlite-shm" &&
  state_sources+=("$codex_root/state_5.sqlite-shm")

/usr/bin/rsync -a \
  "${file_link_opts[@]}" \
  "${state_sources[@]}" \
  "$working/"

source_count=$(
  /usr/bin/find \
    "$codex_root/sessions" \
    "$codex_root/archived_sessions" \
    -type f |
    /usr/bin/wc -l |
    /usr/bin/tr -d ' '
)

backup_count=$(
  /usr/bin/find \
    "$working/sessions" \
    "$working/archived_sessions" \
    -type f |
    /usr/bin/wc -l |
    /usr/bin/tr -d ' '
)

test "$source_count" = "$backup_count"
test -f "$working/session_index.jsonl"

/usr/bin/sqlite3 -readonly "$working/state_5.sqlite" \
  'PRAGMA quick_check;' |
  /usr/bin/grep -qx 'ok'

abort_if_codex_running

/bin/mv "$working" "$snapshot"
/bin/ln -sfn "$snapshot" "$latest_link"

echo "Incremental backup complete: $snapshot"
/usr/bin/du -sh "$snapshot" "$snapshots_root"
