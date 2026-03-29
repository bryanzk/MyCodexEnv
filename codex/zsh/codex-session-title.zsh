# Codex session title hook for zsh
#
# Behaviour:
#   - Only runs inside git repositories
#   - Uses .codex-title-template when present
#   - Optionally bootstraps the template file when the repo ships a matching init script
#   - Updates the terminal title and exports CODEX_PROJECT / CODEX_SESSION_TITLE
#   - Defaults to <项目缩写>-<YYYYMMDD>-summary so new Codex sessions start with a compliant prefix

autoload -Uz add-zsh-hook

codex__session_title_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null
}

codex__session_title_project_code() {
    local repo_name="$1"
    python3 - "$repo_name" <<'PY'
from __future__ import annotations

import re
import sys

repo_name = sys.argv[1]
normalized = re.sub(r"[^A-Za-z0-9]+", " ", repo_name)
parts = []
for chunk in normalized.split():
    parts.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", chunk))

if len(parts) >= 2:
    code = "".join(part[0] for part in parts[:6]).upper()
elif parts:
    token = parts[0].upper()
    code = token[: min(max(len(token), 2), 6)]
else:
    compact = re.sub(r"[^A-Za-z0-9]", "", repo_name).upper()
    code = compact[:6] or "PROJ"

print(code)
PY
}

codex__session_title_render() {
    local template="$1"
    local repo_root="$2"
    local repo_name script_name project_code date_str title

    repo_name="${repo_root:t}"
    script_name="zsh"
    project_code="$(codex__session_title_project_code "$repo_name")"
    date_str="$(date +%Y%m%d)"
    title="$template"
    title="${title//\{repo\}/$repo_name}"
    title="${title//\{root\}/$repo_root}"
    title="${title//\{script\}/$script_name}"
    title="${title//\{abbr\}/$project_code}"
    title="${title//\{date\}/$date_str}"

    printf '%s' "$title"
}

codex_update_session_title() {
    local repo_root template title init_script

    repo_root="$(codex__session_title_repo_root)" || return 0

    if [[ -z "$repo_root" ]]; then
        return 0
    fi

    template="{abbr}-{date}-summary"
    init_script="${repo_root}/scripts/codex-init-title-template.sh"

    if [[ -f "${repo_root}/.codex-title-template" ]]; then
        template="$(<"${repo_root}/.codex-title-template")"
    elif [[ -x "$init_script" ]]; then
        # 仓库自带初始化脚本时，自动补齐一次模板文件。
        "$init_script" --force >/dev/null 2>&1 || true
        if [[ -f "${repo_root}/.codex-title-template" ]]; then
            template="$(<"${repo_root}/.codex-title-template")"
        fi
    fi

    title="$(codex__session_title_render "$template" "$repo_root")"

    export CODEX_PROJECT="${repo_root:t}"
    export CODEX_SESSION_TITLE="$title"

    # 兼容大多数支持 OSC 0 的终端。
    print -Pn -- "\e]0;${title}\a"
}

add-zsh-hook chpwd codex_update_session_title
add-zsh-hook precmd codex_update_session_title
codex_update_session_title
