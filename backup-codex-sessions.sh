#!/bin/zsh
#
# backup-codex-sessions.sh
#
# 一条命令包干：状态自检 → 残留清理 → 增量备份 → 完整性校验 → 结论。
#
#   ./backup-codex-sessions.sh            # 全流程（默认）
#   ./backup-codex-sessions.sh --status   # 只看状态，不写任何东西
#   ./backup-codex-sessions.sh --size     # 全流程 + 统计整个备份根目录占用（慢，外置盘会转很久）
#
# 设计原则：任何一步失败都必须"响亮地"失败——有行号、有原因、非零退出码，
# 并且自动清掉半成品，绝不在备份盘里留脏数据。

set -euo pipefail

SCRIPT_VERSION="v2 (2026-09-14)"

codex_root="/Users/kezheng/.codex"
volume_root="/Volumes/BAK4Bryan2T"
backup_root="$volume_root/CodexSessionBak"
snapshots_root="$backup_root/snapshots"
latest_link="$backup_root/latest"
lock_dir="$backup_root/.backup.lock"

mode="run"
want_total_size=0

# ---------------------------------------------------------------- 输出助手

info() { printf '%s\n' "$*"; }
step() { printf '\n▶ %s\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
fail() { printf '\n❌ %s\n' "$*" >&2; exit 1; }

usage() {
  /bin/cat <<'USAGE'
用法: ./backup-codex-sessions.sh [选项]

  (无参数)    全流程：状态自检 → 清理残留 → 增量备份 → 校验
  --status    只读模式：只报告当前状态，不清理、不备份
  --size      全流程结束后额外统计整个备份根目录的实际占用（慢）
  -h, --help  显示本帮助
USAGE
}

while (( $# )); do
  case "$1" in
    --status) mode="status" ;;
    --size)   want_total_size=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# ---------------------------------------------------------------- 失败清理

working=""
lock_held=0

on_err() {
  printf '\n❌ 第 %s 行执行失败\n' "$1" >&2
}
trap 'on_err $LINENO' ERR

# 注意：zsh 里 $status 是 $? 的只读别名，不能拿来当变量名。
on_exit() {
  local rc=$?
  if (( rc != 0 )) && [[ -n "$working" && -d "$working" ]]; then
    printf '  🧹 已清除未完成的工作目录: %s\n' "$working" >&2
    /bin/rm -rf "$working"
  fi
  if (( lock_held )); then
    /bin/rm -rf "$lock_dir" 2>/dev/null || true
  fi
  if (( rc != 0 )); then
    printf '\n备份未完成，退出码 %s。上面的第一条 ❌ 就是根因。\n' "$rc" >&2
  fi
  return $rc
}
trap on_exit EXIT

# ---------------------------------------------------------------- 前置检查

abort_if_codex_running() {
  local proc
  for proc in Codex ChatGPT codex; do
    if /usr/bin/pgrep -x "$proc" >/dev/null; then
      fail "检测到 $proc 仍在运行。请退出 Codex、ChatGPT 和所有 Codex CLI 会话后重跑。"
    fi
  done
}

require_volume() {
  test -d "$volume_root" || fail "备份盘 BAK4Bryan2T 未挂载（找不到 $volume_root）。"
}

# ---------------------------------------------------------------- 状态报告

# 找出所有 state_*.sqlite（不写死 state_5，Codex 升级换版本时不会静默漏备）
state_dbs=("$codex_root"/state_*.sqlite(N))

report_state() {
  step "当前状态（脚本 $SCRIPT_VERSION）"

  if ! test -d "$volume_root"; then
    warn "备份盘未挂载：$volume_root"
    return 0
  fi
  ok "备份盘已挂载：$volume_root"

  if ! test -d "$snapshots_root"; then
    warn "还没有任何快照目录（$snapshots_root 不存在）——这会是第一次备份。"
    return 0
  fi

  local -a snaps stale
  snaps=("$snapshots_root"/[0-9]*(N/))
  stale=("$snapshots_root"/.incomplete-*(N/))

  info "  已完成快照: ${#snaps[@]} 个"
  if (( ${#snaps[@]} )); then
    info "  最近 3 个:"
    local s
    for s in "${snaps[@]: -3}"; do
      info "    - ${s:t}"
    done
  fi

  if test -L "$latest_link"; then
    local target
    target=$(/usr/bin/readlink "$latest_link")
    if test -d "$target"; then
      ok "latest → ${target:t}（上一次备份已完整收尾）"
    else
      warn "latest 指向一个不存在的快照：$target"
    fi
  elif test -e "$latest_link"; then
    warn "latest 存在但不是符号链接——需要人工处理。"
  else
    warn "还没有 latest 链接。"
  fi

  if (( ${#stale[@]} )); then
    warn "发现 ${#stale[@]} 个残留的半成品目录（上一次运行中途失败留下的）:"
    local d
    for d in "${stale[@]}"; do
      info "    - ${d:t}"
    done
  else
    ok "无残留的 .incomplete-* 目录"
  fi
}

# ---------------------------------------------------------------- 锁

acquire_lock() {
  if ! /bin/mkdir "$lock_dir" 2>/dev/null; then
    if test -f "$lock_dir/pid"; then
      local owner
      owner=$(/bin/cat "$lock_dir/pid" 2>/dev/null || printf '')
      if [[ -n "$owner" ]] && /bin/kill -0 "$owner" 2>/dev/null; then
        fail "另一个备份进程正在运行（pid $owner）。等它结束，或确认它已死后删除 $lock_dir。"
      fi
      warn "发现过期的锁（pid ${owner:-未知} 已不存在），接管。"
      /bin/rm -rf "$lock_dir"
      /bin/mkdir "$lock_dir"
    else
      fail "无法创建锁目录 $lock_dir（备份盘只读或权限不足？）"
    fi
  fi
  lock_held=1
  printf '%s\n' "$$" > "$lock_dir/pid"
}

# ---------------------------------------------------------------- 清理残留

sweep_incomplete() {
  step "清理残留"
  local -a stale
  stale=("$snapshots_root"/.incomplete-*(N/))
  if (( ${#stale[@]} == 0 )); then
    ok "没有需要清理的东西"
    return 0
  fi
  local d
  for d in "${stale[@]}"; do
    info "  删除 ${d:t}"
    /bin/rm -rf "$d"
  done
  ok "已清除 ${#stale[@]} 个半成品目录"
}

# ---------------------------------------------------------------- 主流程

info "codex-sessions 备份 $SCRIPT_VERSION"

require_volume
report_state

if [[ "$mode" == "status" ]]; then
  printf '\n（--status 只读模式，未做任何改动）\n'
  exit 0
fi

step "前置检查"
abort_if_codex_running
ok "Codex / ChatGPT / codex CLI 均未运行"

for required in \
  "$codex_root/sessions" \
  "$codex_root/archived_sessions" \
  "$codex_root/session_index.jsonl"; do
  test -e "$required" || fail "源数据缺失: $required"
done
(( ${#state_dbs[@]} )) || fail "在 $codex_root 下找不到任何 state_*.sqlite"
ok "源数据齐全（含 ${#state_dbs[@]} 个 state 数据库: ${(j:, :)${(@)state_dbs:t}}）"

if test -e "$latest_link" && ! test -L "$latest_link"; then
  fail "$latest_link 存在但不是符号链接，拒绝覆盖。请人工确认后删除它。"
fi

/bin/mkdir -p "$snapshots_root"
acquire_lock
sweep_incomplete

stamp=$(/bin/date -u '+%Y%m%dT%H%M%SZ')
working="$snapshots_root/.incomplete-$stamp"
snapshot="$snapshots_root/$stamp"

test -e "$snapshot" && fail "快照 $stamp 已存在，说明同一秒内跑了两次。稍等一秒重试。"
/bin/mkdir "$working"

previous=""
if test -L "$latest_link"; then
  previous=$(/usr/bin/readlink "$latest_link")
  test -d "$previous" || fail "latest 指向一个不存在的快照: $previous"
fi

session_link_opts=()
archive_link_opts=()
file_link_opts=()
if [[ -n "$previous" ]]; then
  session_link_opts=(--link-dest="$previous/sessions")
  archive_link_opts=(--link-dest="$previous/archived_sessions")
  file_link_opts=(--link-dest="$previous")
fi

step "增量备份 → ${stamp}"
if [[ -n "$previous" ]]; then
  info "  基线: ${previous:t}（未变动的文件走硬链接，不占额外空间）"
else
  info "  没有基线，本次为全量首备。"
fi

/usr/bin/rsync -a "${session_link_opts[@]}" \
  "$codex_root/sessions/" "$working/sessions/"
ok "sessions 已同步"

/usr/bin/rsync -a "${archive_link_opts[@]}" \
  "$codex_root/archived_sessions/" "$working/archived_sessions/"
ok "archived_sessions 已同步"

# session_index + 所有 state 数据库及其 -wal / -shm 旁文件。
# 注意：这里必须用 if/fi，不能用 `test -f x && arr+=(y)`——
# 后者在文件不存在时整条语句返回 1，set -e 会让脚本"无声退出"。
state_sources=("$codex_root/session_index.jsonl")
for db in "${state_dbs[@]}"; do
  state_sources+=("$db")
  for side in "$db-wal" "$db-shm"; do
    if test -f "$side"; then
      state_sources+=("$side")
    fi
  done
done

/usr/bin/rsync -a "${file_link_opts[@]}" "${state_sources[@]}" "$working/"
ok "索引与 state 数据库已同步（${#state_sources[@]} 个文件）"

step "完整性校验"

source_count=$(/usr/bin/find "$codex_root/sessions" "$codex_root/archived_sessions" -type f | /usr/bin/wc -l | /usr/bin/tr -d ' ')
backup_count=$(/usr/bin/find "$working/sessions" "$working/archived_sessions" -type f | /usr/bin/wc -l | /usr/bin/tr -d ' ')
[[ "$source_count" == "$backup_count" ]] \
  || fail "文件数不一致：源 $source_count，备份 $backup_count。"
ok "会话文件数一致：$source_count"

test -f "$working/session_index.jsonl" || fail "备份里缺少 session_index.jsonl"
ok "session_index.jsonl 存在"

for db in "${state_dbs[@]}"; do
  name="${db:t}"
  /usr/bin/sqlite3 -readonly "$working/$name" 'PRAGMA quick_check;' \
    | /usr/bin/grep -qx 'ok' \
    || fail "$name 的 SQLite 完整性校验未通过，本次备份作废。"
  ok "$name quick_check 通过"
done

abort_if_codex_running

step "落盘"
/bin/mv "$working" "$snapshot"
working=""
/bin/ln -sfn "$snapshot" "$latest_link"
ok "快照已提交并更新 latest"

step "完成"
info "  快照: $snapshot"
info "  本次新增占用: $(/usr/bin/du -sh "$snapshot" | /usr/bin/cut -f1)（含硬链接复用）"
if (( want_total_size )); then
  info "  备份根目录总占用: $(/usr/bin/du -sh "$snapshots_root" | /usr/bin/cut -f1)"
else
  info "  （想看整体占用加 --size，外置盘上会比较慢）"
fi

printf '\n✅ 备份完成: %s\n' "${snapshot:t}"
