#!/usr/bin/env bash
set -euo pipefail

# 同步仓库配置到目标 Codex home，并固定 superpowers 版本。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
EIGENPHI_BACKEND_ROOT=""
SKIP_SUPERPOWERS_SYNC="false"
SYNC_AGENTS_ONLY="false"
FORCE_DOWNGRADE="false"
OPERATOR_CHECKPOINT=""

usage() {
  cat <<USAGE
Usage: sync_codex_home.sh --repo-root <path> [--eigenphi-backend-root <path>] [--codex-home <path>] [--skip-superpowers-sync] [--sync-agents-only] [--force-downgrade --operator-checkpoint <path>]

Options:
  --eigenphi-backend-root   Optional legacy argument; EigenPhi MCP is disabled by default.
  --force-downgrade         Allow an ancestor source only with a same-operation operator checkpoint.
  --operator-checkpoint     JSON receipt with command, exit_code, key_output, and timestamp.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
      shift 2
      ;;
    --codex-home)
      CODEX_HOME="${2:-}"
      shift 2
      ;;
    --eigenphi-backend-root)
      EIGENPHI_BACKEND_ROOT="${2:-}"
      shift 2
      ;;
    --skip-superpowers-sync)
      SKIP_SUPERPOWERS_SYNC="true"
      shift
      ;;
    --sync-agents-only)
      SYNC_AGENTS_ONLY="true"
      shift
      ;;
    --force-downgrade)
      FORCE_DOWNGRADE="true"
      shift
      ;;
    --operator-checkpoint)
      OPERATOR_CHECKPOINT="${2:-}"
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

MANIFEST_PATH="${CODEX_HOME}/harness/sync-manifest.json"
SOURCE_COMMIT=""
REPO_IDENTITY=""
EXPECTED_OLD=""
TRANSITION_VERDICT="bootstrap"

fail_transition() {
  echo "source transition rejected: $1" >&2
  exit 1
}

if ! SOURCE_COMMIT="$(git -C "${REPO_ROOT}" rev-parse --verify 'HEAD^{commit}' 2>/dev/null)"; then
  fail_transition "unknown (source HEAD is not a commit)"
fi
if [[ ! "${SOURCE_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  fail_transition "unknown (source commit is malformed)"
fi
if ! REPO_IDENTITY="$(git -C "${REPO_ROOT}" config --get remote.origin.url 2>/dev/null)" || [[ -z "${REPO_IDENTITY}" ]]; then
  fail_transition "unknown (remote origin identity is unavailable)"
fi

if [[ -e "${MANIFEST_PATH}" && ! -f "${MANIFEST_PATH}" ]]; then
  fail_transition "manifest_corrupt (manifest is not a regular file)"
fi

if [[ -f "${MANIFEST_PATH}" ]]; then
  if ! EXPECTED_OLD="$(python3 - "${MANIFEST_PATH}" "${REPO_IDENTITY}" <<'PY'
from datetime import datetime
import json
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
expected_identity = sys.argv[2]
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"manifest parse failed: {exc}")

required = {
    "schema_version",
    "repo_identity_version",
    "repo_identity",
    "source_commit",
    "managed_surface_digest_version",
    "managed_surface_digest",
    "synced_at",
}
if set(payload) != required:
    raise SystemExit("manifest keys do not match schema v2")
if payload["schema_version"] != 2 or payload["repo_identity_version"] != 1:
    raise SystemExit("manifest schema or repo identity version is invalid")
if payload["repo_identity"] != expected_identity:
    raise SystemExit("manifest repo identity does not match source")
if not isinstance(payload["source_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", payload["source_commit"]):
    raise SystemExit("manifest source_commit is invalid")
if payload["managed_surface_digest_version"] != 1:
    raise SystemExit("manifest managed surface digest version is invalid")
if not isinstance(payload["managed_surface_digest"], str) or not re.fullmatch(
    r"sha256:[0-9a-f]{64}", payload["managed_surface_digest"]
):
    raise SystemExit("manifest managed surface digest is invalid")
if not isinstance(payload["synced_at"], str):
    raise SystemExit("manifest synced_at is invalid")
try:
    datetime.fromisoformat(payload["synced_at"].replace("Z", "+00:00"))
except ValueError as exc:
    raise SystemExit(f"manifest synced_at is invalid: {exc}")
print(payload["source_commit"])
PY
  )"; then
    fail_transition "manifest_corrupt"
  fi

  if ! git -C "${REPO_ROOT}" cat-file -e "${EXPECTED_OLD}^{commit}" 2>/dev/null; then
    fail_transition "unknown (manifest source commit is unavailable)"
  fi
  REMOTE_LINE="$(git -C "${REPO_ROOT}" ls-remote --exit-code origin refs/heads/main 2>/dev/null || true)"
  REMOTE_TIP="${REMOTE_LINE%%[[:space:]]*}"
  if [[ ! "${REMOTE_TIP}" =~ ^[0-9a-f]{40}$ ]]; then
    fail_transition "unknown (fresh remote tip is unavailable)"
  fi

  if [[ "${EXPECTED_OLD}" == "${SOURCE_COMMIT}" ]]; then
    if [[ "${SOURCE_COMMIT}" == "${REMOTE_TIP}" ]]; then
      TRANSITION_VERDICT="equal"
    else
      fail_transition "stale_equal"
    fi
  elif git -C "${REPO_ROOT}" merge-base --is-ancestor "${EXPECTED_OLD}" "${SOURCE_COMMIT}" 2>/dev/null; then
    if [[ "${SOURCE_COMMIT}" != "${REMOTE_TIP}" ]]; then
      fail_transition "unknown (forward source is not the fresh remote tip)"
    fi
    TRANSITION_VERDICT="forward"
  elif git -C "${REPO_ROOT}" merge-base --is-ancestor "${SOURCE_COMMIT}" "${EXPECTED_OLD}" 2>/dev/null; then
    if ! git -C "${REPO_ROOT}" cat-file -e "${REMOTE_TIP}^{commit}" 2>/dev/null \
      || ! git -C "${REPO_ROOT}" merge-base --is-ancestor "${EXPECTED_OLD}" "${REMOTE_TIP}" 2>/dev/null; then
      fail_transition "unknown (downgrade commits are not reachable from the fresh remote tip)"
    fi
    TRANSITION_VERDICT="downgrade"
  else
    fail_transition "diverged"
  fi
fi

if [[ "${TRANSITION_VERDICT}" == "equal" ]]; then
  echo "source transition: equal"
  exit 0
fi

if [[ "${TRANSITION_VERDICT}" == "downgrade" ]]; then
  if [[ "${FORCE_DOWNGRADE}" != "true" || -z "${OPERATOR_CHECKPOINT}" ]]; then
    fail_transition "downgrade (requires --force-downgrade and --operator-checkpoint)"
  fi
  if ! python3 - "${OPERATOR_CHECKPOINT}" "${SOURCE_COMMIT}" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
source_commit = sys.argv[2]
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"operator checkpoint parse failed: {exc}")
if set(payload) != {"command", "exit_code", "key_output", "timestamp"}:
    raise SystemExit("operator checkpoint must contain exactly the four receipt fields")
if not isinstance(payload["command"], str) or "--force-downgrade" not in payload["command"]:
    raise SystemExit("operator checkpoint command must bind --force-downgrade")
if source_commit not in payload["command"]:
    raise SystemExit("operator checkpoint command must bind the requested source commit")
if payload["exit_code"] != 0 or not isinstance(payload["key_output"], str) or not payload["key_output"].strip():
    raise SystemExit("operator checkpoint result is invalid")
try:
    recorded = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
except (AttributeError, ValueError) as exc:
    raise SystemExit(f"operator checkpoint timestamp is invalid: {exc}")
if recorded.tzinfo is None or abs((datetime.now(timezone.utc) - recorded).total_seconds()) > 300:
    raise SystemExit("operator checkpoint is not from the same operation window")
PY
  then
    fail_transition "downgrade (operator checkpoint invalid)"
  fi
fi

write_sync_manifest() {
  python3 - "${MANIFEST_PATH}" "${REPO_ROOT}" "${REPO_IDENTITY}" "${SOURCE_COMMIT}" "${EXPECTED_OLD}" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

manifest_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
repo_identity = sys.argv[3]
source_commit = sys.argv[4]
expected_old = sys.argv[5]

if manifest_path.exists():
    current = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not expected_old or current.get("source_commit") != expected_old:
        raise SystemExit("manifest expected-old CAS failed")
elif expected_old:
    raise SystemExit("manifest expected-old CAS failed")

digest = hashlib.sha256()
source_root = repo_root / "codex"
for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
    relative = path.relative_to(repo_root).as_posix().encode("utf-8")
    content = path.read_bytes()
    digest.update(relative + b"\0" + str(len(content)).encode("ascii") + b"\0" + content)

payload = {
    "schema_version": 2,
    "repo_identity_version": 1,
    "repo_identity": repo_identity,
    "source_commit": source_commit,
    "managed_surface_digest_version": 1,
    "managed_surface_digest": f"sha256:{digest.hexdigest()}",
    "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
fd, temp_name = tempfile.mkstemp(prefix=f".{manifest_path.name}.", dir=manifest_path.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
    os.replace(temp_name, manifest_path)
    try:
        parent_fd = os.open(manifest_path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except OSError:
        pass
finally:
    try:
        os.unlink(temp_name)
    except FileNotFoundError:
        pass
PY
  echo "source transition: ${TRANSITION_VERDICT}"
}

mkdir -p "${CODEX_HOME}"

sync_codex_remote_docs() {
  local source target backup
  for filename in remote-access.md remote-hosts.md; do
    source="${REPO_ROOT}/codex/${filename}"
    target="${CODEX_HOME}/${filename}"
    if [[ ! -f "${source}" ]]; then
      echo "Missing Codex remote doc source: ${source}" >&2
      exit 1
    fi
    if [[ -f "${target}" ]]; then
      backup="${target}.backup.$(date +%Y%m%d%H%M%S)"
      cp "${target}" "${backup}"
      echo "Backed up existing ${filename} to ${backup}"
    fi
    cp "${source}" "${target}"
    echo "Codex ${filename} synchronized: ${target}"
  done
}

if [[ "${SYNC_AGENTS_ONLY}" == "true" ]]; then
  AGENTS_SOURCE="${REPO_ROOT}/codex/AGENTS.md"
  AGENTS_TARGET="${CODEX_HOME}/AGENTS.md"
  if [[ ! -f "${AGENTS_SOURCE}" ]]; then
    echo "Missing AGENTS source: ${AGENTS_SOURCE}" >&2
    exit 1
  fi
  if [[ -f "${AGENTS_TARGET}" ]]; then
    backup="${AGENTS_TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    cp "${AGENTS_TARGET}" "${backup}"
    echo "Backed up existing AGENTS to ${backup}"
  fi
  cp "${AGENTS_SOURCE}" "${AGENTS_TARGET}"
  echo "Codex AGENTS synchronized: ${AGENTS_TARGET}"
  sync_codex_remote_docs
  if [[ -f "${REPO_ROOT}/codex/hooks.json" ]]; then
    cp "${REPO_ROOT}/codex/hooks.json" "${CODEX_HOME}/hooks.json"
    echo "Codex hooks config synchronized: ${CODEX_HOME}/hooks.json"
  fi
  if [[ -d "${REPO_ROOT}/codex/hooks" ]]; then
    mkdir -p "${CODEX_HOME}/hooks"
    rsync -a --delete "${REPO_ROOT}/codex/hooks/" "${CODEX_HOME}/hooks/"
    echo "Codex hook scripts synchronized: ${CODEX_HOME}/hooks/"
  fi
  if [[ -d "${REPO_ROOT}/codex/runtime" ]]; then
    mkdir -p "${CODEX_HOME}/runtime"
    rsync -a --delete "${REPO_ROOT}/codex/runtime/" "${CODEX_HOME}/runtime/"
    echo "Codex runtime policy synchronized: ${CODEX_HOME}/runtime/"
  fi
  if [[ -d "${REPO_ROOT}/codex/zsh" ]]; then
    mkdir -p "${CODEX_HOME}/zsh"
    rsync -a --delete "${REPO_ROOT}/codex/zsh/" "${CODEX_HOME}/zsh/"
    echo "Codex zsh helpers synchronized: ${CODEX_HOME}/zsh/"
  fi
  CONFIG_TARGET="${CODEX_HOME}/config.toml"
  if [[ -f "${CONFIG_TARGET}" ]]; then
    python3 - "${CONFIG_TARGET}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

updated = re.sub(r"^codex_hooks\s*=.*\n?", "", text, flags=re.MULTILINE)
if re.search(r"^hooks\s*=", updated, flags=re.MULTILINE):
    updated = re.sub(r"^hooks\s*=.*$", "hooks = true", updated, count=1, flags=re.MULTILINE)
elif "[features]" in text:
    updated = updated.replace("[features]", "[features]\nhooks = true", 1)
else:
    updated = updated.rstrip() + "\n\n[features]\nhooks = true\n"

if updated != text:
    path.write_text(updated, encoding="utf-8")
PY
    echo "Codex hooks feature enabled in existing config: ${CONFIG_TARGET}"
  else
    echo "[WARN] Missing ${CONFIG_TARGET}; hooks will activate after the next full config sync." >&2
  fi
  write_sync_manifest
  exit 0
fi

CONFIG_TARGET="${CODEX_HOME}/config.toml"
if [[ -f "${CONFIG_TARGET}" ]]; then
  backup="${CONFIG_TARGET}.backup.$(date +%Y%m%d%H%M%S)"
  cp "${CONFIG_TARGET}" "${backup}"
  echo "Backed up existing config to ${backup}"
fi

TEMPLATE_PATH="${REPO_ROOT}/codex/config.template.toml"
if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  echo "Missing config template: ${TEMPLATE_PATH}" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to resolve NPM_GLOBAL_BIN for codex config rendering." >&2
  exit 1
fi

npm_global_prefix="$(npm prefix -g)"
if [[ -z "${npm_global_prefix}" ]]; then
  echo "Failed to resolve npm global prefix." >&2
  exit 1
fi

npm_global_bin="${npm_global_prefix}/bin"
escaped_npm_global_bin="$(printf '%s' "${npm_global_bin}" | sed 's/[\/&]/\\&/g')"
rendered_tmp="$(mktemp)"
sed \
  -e "s|\${NPM_GLOBAL_BIN}|${escaped_npm_global_bin}|g" \
  "${TEMPLATE_PATH}" > "${rendered_tmp}"

if rg -n '\$\{[A-Z0-9_]+\}' "${rendered_tmp}" >/dev/null 2>&1; then
  echo "Template rendering failed: unresolved placeholder remains in ${rendered_tmp}" >&2
  rm -f "${rendered_tmp}"
  exit 1
fi

if [[ -f "${CONFIG_TARGET}" ]]; then
  python3 - "${rendered_tmp}" "${CONFIG_TARGET}" <<'PY'
from pathlib import Path
import re
import sys

rendered_path = Path(sys.argv[1])
existing_path = Path(sys.argv[2])
rendered = rendered_path.read_text(encoding="utf-8")
existing = existing_path.read_text(encoding="utf-8")


def table_blocks(text):
    headers = list(re.finditer(r"(?m)^\[([^\]\n]+)\]\s*$", text))
    blocks = []
    for index, match in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        blocks.append((match.group(1), text[match.start():end].strip()))
    return blocks


def preserve_table(name):
    return (
        name.startswith("plugins.")
        or name.startswith("marketplaces.")
        or name.startswith("projects.")
        or name == "hooks.state"
        or name.startswith("hooks.state.")
        or name == "desktop"
        or name.startswith("desktop.")
        or name == "memories"
        or name == "mcp_servers.node_repl"
        or name == "mcp_servers.node_repl.env"
    )


def table_key_lines(block):
    keys = {}
    for line in block.splitlines()[1:]:
        match = re.match(r"\s*([A-Za-z0-9_-]+)\s*=", line)
        if match:
            keys[match.group(1)] = line
    return keys


def merge_table_keys(text, table_name, source_block):
    target_match = re.search(rf"(?m)^\[{re.escape(table_name)}\]\s*$", text)
    if not target_match:
        return text
    next_match = re.search(r"(?m)^\[[^\]\n]+\]\s*$", text[target_match.end():])
    end = target_match.end() + next_match.start() if next_match else len(text)
    target_block = text[target_match.start():end]
    target_keys = table_key_lines(target_block)
    additions = []
    for key, line in table_key_lines(source_block).items():
        if key in target_keys:
            continue
        if table_name == "features" and key == "codex_hooks":
            continue
        additions.append(line)
    if not additions:
        return text
    insertion = "\n" + "\n".join(additions)
    return text[:end].rstrip() + insertion + "\n\n" + text[end:].lstrip("\n")


existing_blocks = table_blocks(existing)
rendered_names = {name for name, _ in table_blocks(rendered)}

notify_match = re.search(r"(?m)^notify\s*=.*$", existing)
if notify_match and not re.search(r"(?m)^notify\s*=", rendered):
    first_table = re.search(r"(?m)^\[[^\]\n]+\]\s*$", rendered)
    insert_at = first_table.start() if first_table else len(rendered)
    rendered = (
        rendered[:insert_at].rstrip()
        + "\n\n"
        + notify_match.group(0)
        + "\n\n"
        + rendered[insert_at:].lstrip("\n")
    )

for name, block in existing_blocks:
    if name == "features":
        rendered = merge_table_keys(rendered, "features", block)
    elif preserve_table(name):
        if name in rendered_names:
            rendered = merge_table_keys(rendered, name, block)
        else:
            rendered = rendered.rstrip() + "\n\n" + block + "\n"
            rendered_names.add(name)

rendered_path.write_text(rendered, encoding="utf-8")
PY
fi

cp "${rendered_tmp}" "${CONFIG_TARGET}"
rm -f "${rendered_tmp}"

mkdir -p "${CODEX_HOME}/skills"
# Repo skills are managed overlays; preserve runtime-only/local skills that are
# intentionally outside this repository's source-of-truth.
rsync -a "${REPO_ROOT}/codex/skills/" "${CODEX_HOME}/skills/"

if [[ -d "${REPO_ROOT}/codex/workflow" ]]; then
  mkdir -p "${CODEX_HOME}/workflow"
  # workflow/memory 属于运行态热数据，不从仓库模板回灌。
  rsync -a --delete --exclude 'memory/' "${REPO_ROOT}/codex/workflow/" "${CODEX_HOME}/workflow/"
fi

if [[ -f "${REPO_ROOT}/codex/AGENTS.md" ]]; then
  if [[ -f "${CODEX_HOME}/AGENTS.md" ]]; then
    backup="${CODEX_HOME}/AGENTS.md.backup.$(date +%Y%m%d%H%M%S)"
    cp "${CODEX_HOME}/AGENTS.md" "${backup}"
    echo "Backed up existing AGENTS to ${backup}"
  fi
  cp "${REPO_ROOT}/codex/AGENTS.md" "${CODEX_HOME}/AGENTS.md"
fi

sync_codex_remote_docs

if [[ -f "${REPO_ROOT}/codex/hooks.json" ]]; then
  if [[ -f "${CODEX_HOME}/hooks.json" ]]; then
    backup="${CODEX_HOME}/hooks.json.backup.$(date +%Y%m%d%H%M%S)"
    cp "${CODEX_HOME}/hooks.json" "${backup}"
    echo "Backed up existing hooks config to ${backup}"
  fi
  cp "${REPO_ROOT}/codex/hooks.json" "${CODEX_HOME}/hooks.json"
fi

if [[ -d "${REPO_ROOT}/codex/hooks" ]]; then
  mkdir -p "${CODEX_HOME}/hooks"
  rsync -a --delete "${REPO_ROOT}/codex/hooks/" "${CODEX_HOME}/hooks/"
fi

if [[ -d "${REPO_ROOT}/codex/runtime" ]]; then
  mkdir -p "${CODEX_HOME}/runtime"
  rsync -a --delete "${REPO_ROOT}/codex/runtime/" "${CODEX_HOME}/runtime/"
fi

if [[ -d "${REPO_ROOT}/codex/zsh" ]]; then
  mkdir -p "${CODEX_HOME}/zsh"
  rsync -a --delete "${REPO_ROOT}/codex/zsh/" "${CODEX_HOME}/zsh/"
fi

if [[ "${SKIP_SUPERPOWERS_SYNC}" == "true" ]]; then
  echo "Skipping superpowers sync by request."
  write_sync_manifest
  exit 0
fi

LOCK_PATH="${REPO_ROOT}/locks/superpowers.lock"
if [[ ! -f "${LOCK_PATH}" ]]; then
  echo "Missing lock file: ${LOCK_PATH}" >&2
  exit 1
fi

repo_url="$(awk -F= '/^repo=/{print $2}' "${LOCK_PATH}" | head -n1)"
commit_sha="$(awk -F= '/^commit=/{print $2}' "${LOCK_PATH}" | head -n1)"
if [[ -z "${repo_url}" || -z "${commit_sha}" ]]; then
  echo "Invalid superpowers lock file." >&2
  exit 1
fi

SUPERPOWERS_DIR="${CODEX_HOME}/superpowers"
if [[ -d "${SUPERPOWERS_DIR}/.git" ]]; then
  if [[ -n "$(git -C "${SUPERPOWERS_DIR}" status --porcelain --untracked-files=no)" ]]; then
    echo "Local changes detected in ${SUPERPOWERS_DIR}; aborting to avoid data loss." >&2
    exit 1
  fi
  git -C "${SUPERPOWERS_DIR}" fetch --all --tags --prune
else
  git clone "${repo_url}" "${SUPERPOWERS_DIR}"
fi

git -C "${SUPERPOWERS_DIR}" checkout "${commit_sha}"

MARKETPLACE_MANIFEST="${SUPERPOWERS_DIR}/.agents/plugins/marketplace.json"
PLUGIN_MANIFEST="${SUPERPOWERS_DIR}/.codex-plugin/plugin.json"
python3 - "${MARKETPLACE_MANIFEST}" "${PLUGIN_MANIFEST}" <<'PY'
import json
import sys
from pathlib import Path

marketplace_path = Path(sys.argv[1])
plugin_path = Path(sys.argv[2])
if not marketplace_path.is_file():
    raise SystemExit(f"Missing Superpowers marketplace manifest: {marketplace_path}")
if not plugin_path.is_file():
    raise SystemExit(f"Missing Superpowers plugin manifest: {plugin_path}")

marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
if marketplace.get("name") != "superpowers-dev":
    raise SystemExit("Superpowers marketplace name must be superpowers-dev")
if plugin.get("name") != "superpowers" or plugin.get("version") != "6.1.1":
    raise SystemExit("Superpowers plugin manifest must be superpowers version 6.1.1")
if plugin.get("skills") != "./skills/":
    raise SystemExit("Superpowers plugin manifest must expose ./skills/")
PY

CODEX_RESOLVER="${CODEX_HOME}/runtime/resolve_codex_cli.sh"
if [[ ! -x "${CODEX_RESOLVER}" ]] || ! CODEX_BIN="$("${CODEX_RESOLVER}")"; then
  echo "A functional Codex CLI is required to register and install the Superpowers plugin." >&2
  exit 1
fi

superpowers_marketplace_registered() {
  CODEX_HOME="${CODEX_HOME}" "${CODEX_BIN}" plugin marketplace list --json |
    python3 -c 'import json, os, sys; expected = os.path.realpath(sys.argv[1]); data = json.load(sys.stdin); sys.exit(0 if any(m.get("name") == "superpowers-dev" and os.path.realpath(m.get("root", "")) == expected for m in data.get("marketplaces", [])) else 1)' "${SUPERPOWERS_DIR}"
}

superpowers_plugin_installed() {
  CODEX_HOME="${CODEX_HOME}" "${CODEX_BIN}" plugin list --json |
    python3 -c 'import json, sys; data = json.load(sys.stdin); sys.exit(0 if any(p.get("pluginId") == "superpowers@superpowers-dev" and p.get("installed") is True and p.get("enabled") is True and p.get("version") == "6.1.1" for p in data.get("installed", [])) else 1)'
}

if superpowers_marketplace_registered; then
  echo "Superpowers marketplace already registered: superpowers-dev"
else
  CODEX_HOME="${CODEX_HOME}" "${CODEX_BIN}" plugin marketplace add "${SUPERPOWERS_DIR}" --json >/dev/null
  echo "Superpowers marketplace registered: superpowers-dev"
fi

if superpowers_plugin_installed; then
  echo "Superpowers plugin already installed: superpowers@superpowers-dev"
else
  CODEX_HOME="${CODEX_HOME}" "${CODEX_BIN}" plugin add superpowers@superpowers-dev --json >/dev/null
  echo "Superpowers plugin installed: superpowers@superpowers-dev"
fi

echo "Codex home synchronized: ${CODEX_HOME}"
write_sync_manifest
