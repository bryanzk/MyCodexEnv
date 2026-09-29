#!/usr/bin/env bash
set -euo pipefail

# 同步仓库内 Claude workflow 与共享 skills 到目标 Claude home，并注入集成指令块。
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
SHARED_SKILLS_MANIFEST="${REPO_ROOT}/claude/shared-skills.txt"
SETTINGS_SOURCE="${REPO_ROOT}/claude/settings.managed.json"
if [[ ! -d "${WORKFLOW_SOURCE}" ]]; then
  echo "Missing workflow source directory: ${WORKFLOW_SOURCE}" >&2
  exit 1
fi
if [[ ! -f "${BLOCK_SOURCE}" ]]; then
  echo "Missing integration block: ${BLOCK_SOURCE}" >&2
  exit 1
fi
if [[ ! -f "${SHARED_SKILLS_MANIFEST}" ]]; then
  echo "Missing shared skills manifest: ${SHARED_SKILLS_MANIFEST}" >&2
  exit 1
fi
if [[ ! -f "${SETTINGS_SOURCE}" ]]; then
  echo "Missing managed Claude settings: ${SETTINGS_SOURCE}" >&2
  exit 1
fi

# 托管的全局 permissions 只追加缺失条目；settings.json 中其他键和用户已有条目保持不变。
# check 只做校验；apply 在内容变化时先备份再原子写入（软链接写入其真实目标）。
merge_managed_settings() {
  python3 - "$1" "${SETTINGS_SOURCE}" "${CLAUDE_HOME}/settings.json" <<'PY'
import json
import os
import shutil
import sys
import tempfile
import time

mode, source_path, target_path = sys.argv[1:4]
LISTS = ("allow", "ask", "deny")


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


try:
    with open(source_path, encoding="utf-8") as handle:
        managed = json.load(handle)
except (OSError, ValueError) as exc:
    fail(f"Invalid managed Claude settings {source_path}: {exc}")
if not isinstance(managed, dict) or set(managed) != {"permissions"} or not isinstance(managed["permissions"], dict):
    fail(f"Managed Claude settings must contain only a permissions object: {source_path}")
for key, entries in managed["permissions"].items():
    if key not in LISTS:
        fail(f"Unsupported managed permissions key {key!r} in {source_path}")
    if not isinstance(entries, list) or not all(isinstance(e, str) and e.strip() for e in entries):
        fail(f"Managed permissions.{key} must be a list of non-empty strings: {source_path}")

real_target = os.path.realpath(target_path)
if os.path.exists(real_target):
    try:
        with open(real_target, encoding="utf-8") as handle:
            settings = json.load(handle)
    except (OSError, ValueError) as exc:
        fail(f"Existing Claude settings is not valid JSON, refusing to modify {target_path}: {exc}")
    existed = True
else:
    settings = {}
    existed = False
if not isinstance(settings, dict):
    fail(f"Existing Claude settings must be a JSON object: {target_path}")
permissions = settings.setdefault("permissions", {})
if not isinstance(permissions, dict):
    fail(f"Existing Claude settings permissions must be an object: {target_path}")

added = 0
for key in LISTS:
    entries = managed["permissions"].get(key, [])
    if not entries:
        continue
    current = permissions.setdefault(key, [])
    if not isinstance(current, list):
        fail(f"Existing Claude settings permissions.{key} must be a list: {target_path}")
    for entry in entries:
        if entry not in current:
            current.append(entry)
            added += 1

if mode == "check":
    sys.exit(0)
if added == 0:
    print(f"Claude settings permissions already current: {target_path}")
    sys.exit(0)

directory = os.path.dirname(real_target)
os.makedirs(directory, exist_ok=True)
if existed:
    backup = f"{real_target}.backup.{time.strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(real_target, backup)
    print(f"Backed up existing Claude settings to {backup}")
fd, tmp = tempfile.mkstemp(dir=directory, prefix=".settings.json.")
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
if existed:
    shutil.copymode(real_target, tmp)
os.replace(tmp, real_target)
print(f"Added {added} managed permission entries to {target_path}")
PY
}
merge_managed_settings check

# 先校验全部共享 skill 源，避免半途失败留下部分同步的 Claude home。
shared_skills=()
while IFS= read -r line || [[ -n "${line}" ]]; do
  skill="${line%%#*}"
  skill="${skill//[[:space:]]/}"
  [[ -z "${skill}" ]] && continue
  if [[ ! "${skill}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Invalid shared skill name: ${skill}" >&2
    exit 1
  fi
  if [[ ! -f "${REPO_ROOT}/codex/skills/${skill}/SKILL.md" ]]; then
    echo "Missing shared skill source: ${REPO_ROOT}/codex/skills/${skill}/SKILL.md" >&2
    exit 1
  fi
  shared_skills+=("${skill}")
done < "${SHARED_SKILLS_MANIFEST}"

mkdir -p "${CLAUDE_HOME}"
mkdir -p "${CLAUDE_HOME}/workflow"
# workflow/memory 属于运行态热数据，不从仓库模板回灌。
rsync -a --delete --exclude 'memory/' "${WORKFLOW_SOURCE}/" "${CLAUDE_HOME}/workflow/"

# 共享 skills 只逐个镜像清单内目录，保留 Claude home 中其他本地/插件 skills。
mkdir -p "${CLAUDE_HOME}/skills"
for skill in ${shared_skills[@]+"${shared_skills[@]}"}; do
  target="${CLAUDE_HOME}/skills/${skill}"
  if [[ -L "${target}" ]]; then
    # 只移除链接本身，不改动链接指向的外部安装目录。
    rm "${target}"
    echo "Replaced symlinked Claude skill with managed copy: ${target}"
  fi
  mkdir -p "${target}"
  rsync -a --delete "${REPO_ROOT}/codex/skills/${skill}/" "${target}/"
done

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

merge_managed_settings apply

echo "Claude home synchronized: ${CLAUDE_HOME}"
