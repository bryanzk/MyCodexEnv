#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# 同步仓库配置到目标 Codex home，并固定 superpowers 版本。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
SKIP_SUPERPOWERS_SYNC="false"
SYNC_AGENTS_ONLY="false"
SYNC_AGENTS_FILE_ONLY="false"
FORCE_DOWNGRADE="false"
BOOTSTRAP_LOADED_READBACK="false"
OPERATOR_CHECKPOINT=""
PROMOTE_HARNESS_GUARD="false"
SELECTED_SKILLS=""
SHARED_CLAUDE_SKILLS_HOME=""

usage() {
  cat <<USAGE
Usage: sync_codex_home.sh --repo-root <path> [--codex-home <path>] [--skip-superpowers-sync] [--sync-agents-only | --sync-agents-file-only] [--promote-harness-guard] [--force-downgrade --operator-checkpoint <path>] [--bootstrap-loaded-readback --operator-checkpoint <path>]

Options:
  --sync-agents-file-only   Sync only AGENTS.md, after the existing source and runtime checks.
  --sync-skills-only NAMES   Sync only comma-separated named skills, after the original source attestation.
  --shared-claude-skills-home PATH
                            In skills-only mode, also copy selected Claude shared skills (no settings).
  --force-downgrade         Allow an ancestor source only with a same-operation operator checkpoint.
  --bootstrap-loaded-readback
                            Allow the one-time loaded-readback bootstrap with an operator checkpoint.
  --operator-checkpoint     JSON receipt with command, exit_code, key_output, and timestamp.
  --promote-harness-guard   Promote only the committed seven-target harness manifest.
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
    --skip-superpowers-sync)
      SKIP_SUPERPOWERS_SYNC="true"
      shift
      ;;
    --sync-skills-only)
      SELECTED_SKILLS="${2:-}"
      [[ -n "${SELECTED_SKILLS}" ]] || { echo "--sync-skills-only requires names" >&2; exit 2; }
      shift 2
      ;;
    --shared-claude-skills-home)
      SHARED_CLAUDE_SKILLS_HOME="${2:-}"
      [[ -n "${SHARED_CLAUDE_SKILLS_HOME}" ]] || { echo "--shared-claude-skills-home requires a path" >&2; exit 2; }
      shift 2
      ;;
    --sync-agents-file-only)
      SYNC_AGENTS_FILE_ONLY="true"
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
    --bootstrap-loaded-readback)
      BOOTSTRAP_LOADED_READBACK="true"
      shift
      ;;
    --operator-checkpoint)
      OPERATOR_CHECKPOINT="${2:-}"
      shift 2
      ;;
    --promote-harness-guard)
      PROMOTE_HARNESS_GUARD="true"
      shift
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

preflight_source_attestation() {
  python3 - \
    "${REPO_ROOT}" \
    "${CODEX_HOME}" \
    "${PHASE0_SOURCE_ROLE:-caller_worktree}" \
    "${PHASE0_PRODUCER_MANIFEST:-}" \
    "${SCRIPT_DIR}/harness_refresh_identity.py" <<'PY'
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

repo_root = Path(sys.argv[1]).resolve()
codex_home = Path(sys.argv[2])
source_role = sys.argv[3]
producer_path = Path(sys.argv[4]) if sys.argv[4] else None
digest_helper_path = Path(sys.argv[5])
approved_path = (repo_root / "runtime-approvals" / "approved-source-digests.txt").resolve()
approved_present = approved_path.exists() or approved_path.is_symlink()
approved_source = "repo_manifest" if approved_present else "absent"
try:
    approved_bytes = approved_path.read_bytes() if approved_present else None
except OSError:
    approved_bytes = None
approved_manifest_digest = (
    f"sha256:{hashlib.sha256(approved_bytes).hexdigest()}" if approved_bytes is not None else None
)


def blocked(reason_code, **details):
    payload = {
        "status": "blocked",
        "reason_code": reason_code,
        "authorized_clone_root": None,
        "approved_source": approved_source,
        "approved_manifest_path": str(approved_path),
        "approved_manifest_digest": approved_manifest_digest,
    }
    payload.update(details)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    raise SystemExit(78)


required = [
    repo_root / "codex" / "AGENTS.md",
    repo_root / "codex" / "remote-access.md",
    repo_root / "codex" / "remote-hosts.md",
    repo_root / "codex" / "hooks" / "task_state.py",
]
missing = [path.relative_to(repo_root).as_posix() for path in required if not path.is_file()]
if missing:
    blocked("source_required_file_missing", missing_paths=missing)

execution_clone = Path(
    os.environ.get(
        "PHASE0_AUTHORIZED_CLONE_ROOT",
        str(Path.home() / ".codex" / "automations" / "gstack-dhf-daily-refresh" / "repo"),
    )
).resolve()
if source_role not in {"git_head", "caller_worktree", "automation_execution_clone"}:
    blocked("source_role_path_mismatch")
if source_role == "automation_execution_clone" and repo_root != execution_clone:
    blocked("source_role_path_mismatch")

if approved_present:
    approved_relative = approved_path.relative_to(repo_root).as_posix()
    tracked = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", approved_relative],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    manifest_status = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all", "--", approved_relative],
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        tracked.returncode != 0
        or manifest_status.returncode != 0
        or manifest_status.stdout.strip()
        or approved_path.is_symlink()
        or not approved_path.is_file()
    ):
        blocked("approved_manifest_dirty")

status = subprocess.run(
    ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all", "--", "codex"],
    capture_output=True,
    text=True,
    check=False,
)
if status.returncode != 0:
    blocked("source_role_path_mismatch")
dirty_paths = [line[3:] for line in status.stdout.splitlines() if len(line) > 3]
if dirty_paths:
    blocked("source_dirty", dirty_paths=dirty_paths)

try:
    spec = importlib.util.spec_from_file_location("harness_refresh_identity_sync", digest_helper_path)
    if spec is None or spec.loader is None:
        raise OSError("source digest helper unavailable")
    digest_helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(digest_helper)
    source_digest = digest_helper.source_digest(repo_root)
except (OSError, RuntimeError):
    blocked("source_enumeration_failed")
try:
    approved = {
        match.group(1)
        for line in approved_bytes.decode("utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        if (match := re.fullmatch(r"sha256:([0-9a-f]{64})  .+", line.strip()))
    } if approved_bytes is not None else set()
except UnicodeDecodeError:
    approved = set()
if source_digest not in approved:
    blocked(
        "source_digest_unapproved",
        source_digest=f"sha256:{source_digest}",
        hint="run: python3 scripts/harness_refresh_identity.py status",
    )

manifest_path = codex_home / "harness" / "sync-manifest.json"
if manifest_path.is_file():
    try:
        runtime_commit = json.loads(manifest_path.read_text(encoding="utf-8"))["source_commit"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        runtime_commit = None
    if isinstance(runtime_commit, str) and re.fullmatch(r"[0-9a-f]{40}", runtime_commit):
        source_commit = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "HEAD^{commit}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        newer = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", source_commit, runtime_commit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if runtime_commit != source_commit and newer.returncode == 0:
            blocked("runtime_newer_than_source")

if source_role == "automation_execution_clone" and producer_path is None:
    blocked("attestation_producer_dirty_or_unapproved")
if producer_path is not None:
    try:
        producer = json.loads(producer_path.read_text(encoding="utf-8"))
        producers = producer["producers"]
        valid_roles = {item["role"] for item in producers} == {
            "launcher",
            "automation_manifest",
            "executed_prepare",
        }
        valid_entries = all(
            item.get("git_clean") is True
            and item.get("dirty_paths") == []
            and re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", ""))
            for item in producers
        )
        producer_approved = producer.get("result") == "approved" and valid_roles and valid_entries
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        producer_approved = False
    if not producer_approved:
        blocked("attestation_producer_dirty_or_unapproved")
PY
}

if [[ "${SYNC_AGENTS_FILE_ONLY}" == "true" ]] &&
   [[ "${SYNC_AGENTS_ONLY}" == "true" || -n "${SELECTED_SKILLS}" || "${PROMOTE_HARNESS_GUARD}" == "true" ]]; then
  echo "--sync-agents-file-only cannot be combined with other promotion modes" >&2
  exit 2
fi

preflight_source_attestation

if [[ -n "${SELECTED_SKILLS}" ]]; then
  if [[ "${SYNC_AGENTS_ONLY}" == "true" || "${PROMOTE_HARNESS_GUARD}" == "true" || "${FORCE_DOWNGRADE}" == "true" || "${BOOTSTRAP_LOADED_READBACK}" == "true" ]]; then
    echo "--sync-skills-only cannot be combined with other promotion modes" >&2
    exit 2
  fi
  python3 - "${REPO_ROOT}" "${CODEX_HOME}" "${SELECTED_SKILLS}" "${SHARED_CLAUDE_SKILLS_HOME}" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

repo = Path(sys.argv[1]).resolve()
codex_home = Path(sys.argv[2]).resolve()
names = sys.argv[3].split(',')
claude_home = Path(sys.argv[4]).resolve() if sys.argv[4] else None
if len(names) != len(set(names)) or any(not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', name) for name in names):
    raise SystemExit('invalid or duplicate selected skill name')
shared = set()
if claude_home is not None:
    shared = {line.strip() for line in (repo / 'claude/shared-skills.txt').read_text().splitlines()
              if line.strip() and not line.lstrip().startswith('#')}
operations = []
# Validate the complete target set before creating anything.
for name in names:
    source = repo / 'codex/skills' / name
    if any(parent.is_symlink() for parent in source.parents if parent != repo and repo in parent.parents):
        raise SystemExit('symlink selected skill source ancestor: ' + name)
    if repo not in source.resolve().parents:
        raise SystemExit('selected skill source escapes repository: ' + name)
    if source.is_symlink() or not source.is_dir() or not (source / 'SKILL.md').is_file():
        raise SystemExit('invalid selected skill source: ' + name)
    homes = [codex_home] + ([claude_home] if claude_home is not None and name in shared else [])
    for home in homes:
        target = home / 'skills' / name
        if target == source or source in target.parents or target in source.parents:
            raise SystemExit('selected skill source/destination overlap: ' + name)
        if (home / 'skills').is_symlink() or target.is_symlink() or (target.exists() and not target.is_dir()):
            raise SystemExit('invalid selected skill destination: ' + str(target))
        for item in source.rglob('*'):
            if item.is_symlink() or not (item.is_file() or item.is_dir()):
                raise SystemExit('nonregular selected skill source: ' + str(item))
            if item.is_dir():
                continue
            dest = target / item.relative_to(source)
            if any(parent.is_symlink() for parent in [dest, *dest.parents] if parent != home and home in parent.parents):
                raise SystemExit('symlink selected skill destination: ' + str(dest))
            if dest.exists() and not dest.is_file():
                raise SystemExit('nonregular selected skill destination: ' + str(dest))
            for parent in dest.parents:
                if parent.exists() and not parent.is_dir():
                    raise SystemExit('nondirectory selected skill destination ancestor: ' + str(parent))
            mode = stat.S_IMODE(dest.stat().st_mode) if dest.exists() else stat.S_IMODE(item.stat().st_mode) & 0o777
            operations.append((item, dest, mode))
changed = []
for source, dest, mode in operations:
    data = source.read_bytes()
    if dest.is_file() and dest.read_bytes() == data:
        continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.skill-sync-', dir=dest.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, dest)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    changed.append(str(dest))
for source, dest, _ in operations:
    if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(dest.read_bytes()).digest():
        raise SystemExit('selected skill readback failed: ' + str(dest))
print(json.dumps({'status': 'ok', 'source_attestation': 'existing_preflight', 'selected_skills': names,
                  'files_checked': len(operations), 'changed_paths': changed}, sort_keys=True))
PY
  exit $?
fi

if [[ -n "${SHARED_CLAUDE_SKILLS_HOME}" ]]; then
  echo "--shared-claude-skills-home requires --sync-skills-only" >&2
  exit 2
fi

sync_harness_targets() {
  mkdir -p "${CODEX_HOME}/harness"
  exec 8>"${CODEX_HOME}/harness/.harness-guard-sync.lock"
  if ! python3 - <<'PY'
import fcntl
try:
    fcntl.flock(8, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(75)
PY
  then
    echo '{"status":"blocked","reason_code":"harness_guard_lock_contended"}' >&2
    return 75
  fi
  python3 - \
    "${REPO_ROOT}" \
    "${CODEX_HOME}" \
    "${HARNESS_TARGET_FAIL_AFTER:-}" \
    "${HARNESS_TARGET_CRASH_AT:-}" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

repo_root = Path(sys.argv[1]).resolve()
codex_home = Path(sys.argv[2]).resolve()
fail_after = int(sys.argv[3]) if sys.argv[3] else None
crash_at = sys.argv[4]
targets_path = repo_root / "codex" / "runtime" / "harness-guard-targets.json"
transactions = codex_home / "harness" / "harness-guard-transactions"
transactions.mkdir(parents=True, exist_ok=True)


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return digest_bytes(path.read_bytes())


def fsync_dir(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            os.fchmod(handle.fileno(), mode)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def record(directory, sequence, state, payload=None):
    path = directory / f"{sequence:03d}-{state}.json"
    data = {"state": state, **(payload or {})}
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    fsync_dir(directory)


def crash(boundary):
    if crash_at == boundary:
        os._exit(91)


def restore(entry):
    target = codex_home / entry["target"]
    current = digest(target) if target.is_file() else None
    if current == entry["pre_digest"]:
        return
    if current != entry["post_digest"]:
        raise RuntimeError(f"recovery_digest_unknown:{entry['target']}")
    backup = entry.get("backup")
    if backup is None:
        target.unlink(missing_ok=True)
        fsync_dir(target.parent)
        return
    atomic_write(target, (Path(entry["transaction_root"]) / backup).read_bytes(), entry["pre_mode"])


def recover_incomplete():
    for directory in sorted(path for path in transactions.iterdir() if path.is_dir()):
        prepared = list(directory.glob("*-PREPARED.json"))
        committed = list(directory.glob("*-COMMITTED.json"))
        if committed:
            continue
        if not prepared:
            shutil.rmtree(directory)
            fsync_dir(transactions)
            continue
        manifest_path = directory / "backup-manifest.json"
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = payload["entries"]
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"recovery_manifest_invalid:{directory.name}") from exc
        for entry in reversed(entries):
            entry["transaction_root"] = str(directory)
            restore(entry)
        sequence = len(list(directory.glob("*.json"))) + 1
        record(directory, sequence, "ABORTED", {"reason": "startup_recovery"})


recover_incomplete()

try:
    target_manifest_bytes = targets_path.read_bytes()
    target_manifest = json.loads(target_manifest_bytes)
    targets = target_manifest["targets"]
except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"harness target manifest invalid: {exc}")
if target_manifest.get("schema_version") != 1 or not isinstance(targets, list) or len(targets) != 7:
    raise SystemExit("harness target manifest must contain exactly seven targets")
if len({item.get("target") for item in targets if isinstance(item, dict)}) != 7:
    raise SystemExit("harness target manifest targets must be unique")
if any(item.get("source") == "codex/runtime/tool-policy.json" for item in targets):
    raise SystemExit("tool-policy.json must not be a harness target")

target_by_runtime = {item["target"]: item for item in targets}
deployed_entries = []
for source in sorted((repo_root / "codex" / "hooks").glob("*.py")):
    runtime_relative = f"hooks/{source.name}"
    runtime = codex_home / runtime_relative
    target_item = target_by_runtime.get(runtime_relative)
    if target_item is None:
        if not runtime.is_file() or digest(runtime) != digest(source):
            raise SystemExit(f"non-target canonical hook drift: {runtime_relative}")
        mode = stat.S_IMODE(runtime.stat().st_mode)
    else:
        mode = int(target_item["mode"])
    deployed_entries.append({
        "path": runtime_relative,
        "sha256": digest(source),
        "type": "file",
        "mode": mode,
    })
for item in targets:
    if item["target"].startswith("hooks/"):
        continue
    source = repo_root / item["source"]
    deployed_entries.append({
        "path": item["target"],
        "sha256": digest(source),
        "type": "file",
        "mode": int(item["mode"]),
    })
if len(deployed_entries) > 32:
    raise SystemExit("deployed manifest exceeds 32 files")
deployed_payload = {"schema_version": 1, "files": sorted(deployed_entries, key=lambda item: item["path"])}
deployed_bytes = (json.dumps(deployed_payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
deployed_path = codex_home / "harness" / "deployed-manifest.json"

transaction_id = uuid.uuid4().hex
transaction = transactions / transaction_id
transaction.mkdir()
fsync_dir(transactions)
entries = []
for item in targets:
    source = repo_root / item["source"]
    target = codex_home / item["target"]
    if not source.is_file() or source.is_symlink():
        raise SystemExit(f"invalid harness target source: {item['source']}")
    pre_digest = digest(target) if target.is_file() else None
    pre_mode = stat.S_IMODE(target.stat().st_mode) if target.is_file() else None
    backup = None
    if target.is_file():
        backup_path = transaction / "backups" / item["target"]
        atomic_write(backup_path, target.read_bytes(), pre_mode)
        backup = str(backup_path.relative_to(transaction))
    entries.append({
        "source": item["source"],
        "target": item["target"],
        "mode": int(item["mode"]),
        "pre_digest": pre_digest,
        "pre_mode": pre_mode,
        "post_digest": digest(source),
        "backup": backup,
    })
deployed_pre_digest = digest(deployed_path) if deployed_path.is_file() else None
deployed_pre_mode = stat.S_IMODE(deployed_path.stat().st_mode) if deployed_path.is_file() else None
deployed_backup = None
if deployed_path.is_file():
    backup_path = transaction / "backups" / "harness" / "deployed-manifest.json"
    atomic_write(backup_path, deployed_path.read_bytes(), deployed_pre_mode)
    deployed_backup = str(backup_path.relative_to(transaction))
entries.append({
    "source": None,
    "target": "harness/deployed-manifest.json",
    "mode": 0o600,
    "pre_digest": deployed_pre_digest,
    "pre_mode": deployed_pre_mode,
    "post_digest": digest_bytes(deployed_bytes),
    "backup": deployed_backup,
})

source_commit = subprocess.run(
    ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
backup_manifest = {
    "schema_version": 1,
    "transaction_id": transaction_id,
    "repo_root": str(repo_root),
    "source_commit": source_commit,
    "target_manifest_sha256": digest_bytes(target_manifest_bytes),
    "target_set": [item["target"] for item in targets],
    "entries": entries,
}
atomic_write(
    transaction / "backup-manifest.json",
    (json.dumps(backup_manifest, sort_keys=True) + "\n").encode("utf-8"),
    0o600,
)
crash("after_backup_manifest")
sequence = 1
record(transaction, sequence, "PREPARED", {key: backup_manifest[key] for key in (
    "schema_version", "transaction_id", "repo_root", "source_commit", "target_manifest_sha256", "target_set"
)})
crash("after_prepared")
tool_policy = codex_home / "runtime" / "tool-policy.json"
tool_policy_before = digest(tool_policy) if tool_policy.is_file() else None

try:
    for index, item in enumerate(targets, 1):
        sequence += 1
        record(transaction, sequence, "TARGET_INTENT", {"index": index, "target": item["target"]})
        crash(f"after_intent_{index}")
        atomic_write(codex_home / item["target"], (repo_root / item["source"]).read_bytes(), int(item["mode"]))
        crash(f"after_replace_{index}")
        sequence += 1
        record(transaction, sequence, "TARGET_APPLIED", {"index": index, "target": item["target"]})
        crash(f"after_applied_{index}")
        if fail_after == index:
            raise RuntimeError(f"failure_injection_after_{index}")
    atomic_write(deployed_path, deployed_bytes, 0o600)
    crash("after_manifest")
    tool_policy_after = digest(tool_policy) if tool_policy.is_file() else None
    if tool_policy_after != tool_policy_before:
        raise RuntimeError("tool_policy_changed")
    sequence += 1
    record(transaction, sequence, "COMMITTED", {"target_count": 7})
    crash("after_committed")
except Exception as exc:
    for entry in reversed(entries):
        entry["transaction_root"] = str(transaction)
        restore(entry)
    sequence += 1
    record(transaction, sequence, "ABORTED", {"reason": str(exc)})
    raise SystemExit(str(exc))

print(f"harness guard promotion committed: targets=7 transaction={transaction_id}")
PY
}

if [[ "${PROMOTE_HARNESS_GUARD}" == "true" ]]; then
  sync_harness_targets
  exit $?
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

base_required = {
    "schema_version",
    "repo_identity_version",
    "repo_identity",
    "source_commit",
    "managed_surface_digest_version",
    "managed_surface_digest",
    "synced_at",
}
schema_version = payload.get("schema_version")
required = base_required if schema_version == 2 else base_required | {"loaded_readback", "loaded_receipt_digest"}
if schema_version not in {2, 3} or set(payload) != required:
    raise SystemExit("manifest keys do not match schema v2 or v3")
if payload["repo_identity_version"] != 1:
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
if schema_version == 3:
    if payload["loaded_readback"] not in {"verified", "bootstrap_operator_attested"}:
        raise SystemExit("manifest loaded readback status is invalid")
    digest = payload["loaded_receipt_digest"]
    if payload["loaded_readback"] == "verified":
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise SystemExit("manifest loaded receipt digest is invalid")
    elif digest is not None:
        raise SystemExit("bootstrap manifest loaded receipt digest must be null")
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
  python3 - "${MANIFEST_PATH}" "${REPO_ROOT}" "${REPO_IDENTITY}" "${SOURCE_COMMIT}" "${EXPECTED_OLD}" "${LOADED_READBACK_STATUS}" "${LOADED_RECEIPT_DIGEST}" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

manifest_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
repo_identity = sys.argv[3]
source_commit = sys.argv[4]
expected_old = sys.argv[5]
loaded_readback = sys.argv[6]
loaded_receipt_digest = sys.argv[7] or None

if manifest_path.exists():
    current = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not expected_old or current.get("source_commit") != expected_old:
        raise SystemExit("manifest expected-old CAS failed")
elif expected_old:
    raise SystemExit("manifest expected-old CAS failed")

digest = hashlib.sha256()
try:
    tracked = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z", "--", "codex/"],
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        raise OSError("git ls-files failed")
    for relative in sorted(part for part in tracked.stdout.split(b"\0") if part):
        path = repo_root / os.fsdecode(relative)
        content = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
        digest.update(relative + b"\0" + str(len(content)).encode("ascii") + b"\0" + content)
except OSError:
    raise SystemExit("source_enumeration_failed")

payload = {
    "schema_version": 3,
    "repo_identity_version": 1,
    "repo_identity": repo_identity,
    "source_commit": source_commit,
    "managed_surface_digest_version": 1,
    "managed_surface_digest": f"sha256:{digest.hexdigest()}",
    "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "loaded_readback": loaded_readback,
    "loaded_receipt_digest": loaded_receipt_digest,
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

if ! LOADED_READBACK_RESULT="$(python3 - "${CODEX_HOME}" "${MANIFEST_PATH}" "${BOOTSTRAP_LOADED_READBACK}" "${OPERATOR_CHECKPOINT}" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

codex_home = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
bootstrap = sys.argv[3] == "true"
checkpoint_path = Path(sys.argv[4]) if sys.argv[4] else None
receipt_path = codex_home / "harness" / "loaded-receipt.json"


def blocked(reason_code):
    print(json.dumps({
        "authorized_clone_root": None,
        "reason_code": reason_code,
        "status": "blocked",
    }, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    raise SystemExit(78)


manifest = None
if manifest_path.is_file():
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        blocked("loaded_readback_unavailable")

if bootstrap:
    if receipt_path.exists() or (isinstance(manifest, dict) and "loaded_readback" in manifest):
        blocked("bootstrap_not_applicable")
    if checkpoint_path is None:
        blocked("bootstrap_checkpoint_invalid")
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if set(checkpoint) != {"command", "exit_code", "key_output", "timestamp"}:
            raise ValueError("checkpoint fields")
        if not isinstance(checkpoint["command"], str) or "--bootstrap-loaded-readback" not in checkpoint["command"]:
            raise ValueError("checkpoint command")
        if checkpoint["exit_code"] != 0 or not isinstance(checkpoint["key_output"], str) or not checkpoint["key_output"].strip():
            raise ValueError("checkpoint result")
        recorded = datetime.fromisoformat(checkpoint["timestamp"].replace("Z", "+00:00"))
        if recorded.tzinfo is None or abs((datetime.now(timezone.utc) - recorded).total_seconds()) > 300:
            raise ValueError("checkpoint timestamp")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
        blocked("bootstrap_checkpoint_invalid")
    print("bootstrap_operator_attested\t")
    raise SystemExit(0)

if manifest is None:
    blocked("loaded_readback_unavailable")
try:
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    required = {"schema_version", "hook_path", "self_digest", "session_id", "event_kind", "written_at"}
    if not required.issubset(receipt) or type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
        raise ValueError("receipt schema")
    if not isinstance(receipt["hook_path"], str) or not receipt["hook_path"]:
        raise ValueError("receipt hook path")
    if not isinstance(receipt["self_digest"], str) or not re.fullmatch(r"[0-9a-f]{64}", receipt["self_digest"]):
        raise ValueError("receipt self digest")
    if receipt["session_id"] is not None and not isinstance(receipt["session_id"], str):
        raise ValueError("receipt session")
    if not isinstance(receipt["event_kind"], str) or not receipt["event_kind"]:
        raise ValueError("receipt event kind")
    written_at = datetime.fromisoformat(receipt["written_at"].replace("Z", "+00:00"))
    if written_at.tzinfo is None:
        raise ValueError("receipt timestamp")
    synced_at = datetime.fromisoformat(manifest["synced_at"].replace("Z", "+00:00"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, AttributeError, TypeError, ValueError):
    blocked("loaded_readback_unavailable")

if written_at < synced_at:
    blocked("loaded_readback_stale")
try:
    runtime_digest = hashlib.sha256((codex_home / "hooks" / "harness_observer.py").read_bytes()).hexdigest()
except OSError:
    blocked("loaded_readback_unavailable")
if receipt["self_digest"] != runtime_digest:
    blocked("loaded_readback_mismatch")
print(f"verified\tsha256:{hashlib.sha256(receipt_bytes).hexdigest()}")
PY
)"; then
  exit 78
fi
IFS=$'\t' read -r LOADED_READBACK_STATUS LOADED_RECEIPT_DIGEST <<<"${LOADED_READBACK_RESULT}"

if [[ "${TRANSITION_VERDICT}" == "equal" ]]; then
  echo "source transition: equal"
  exit 0
fi

mkdir -p "${CODEX_HOME}"
exec 9>"${CODEX_HOME}/.phase0-sync.lock"
if ! python3 - <<'PY'
import fcntl
import json
import sys

try:
    fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print(json.dumps({
        "authorized_clone_root": None,
        "reason_code": "lock_contended",
        "status": "blocked",
    }, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    raise SystemExit(75)
PY
then
  exit 75
fi

# gstack was retired on 2026-11-27 (SHI-637). Sync no longer classifies an
# external gstack or manages links to it; runtime gstack copies are left in place.
RUNTIME_BACKUP_DIR="${CODEX_HOME}/runtime-backups/$(date -u +%Y%m%dT%H%M%SZ)/"
RETIRED_HOOK_TARGET="${CODEX_HOME}/hooks/model_router.py"
RETIRED_HOOK_BACKUP="${RUNTIME_BACKUP_DIR}/retired/hooks/model_router.py"

if [[ -e "${RETIRED_HOOK_TARGET}" || -L "${RETIRED_HOOK_TARGET}" ]]; then
  if [[ ! -f "${RETIRED_HOOK_TARGET}" || -L "${RETIRED_HOOK_TARGET}" ]]; then
    echo "Retired hook target is not a regular file: ${RETIRED_HOOK_TARGET}" >&2
    exit 1
  fi
  if [[ -e "${RETIRED_HOOK_BACKUP}" || -L "${RETIRED_HOOK_BACKUP}" ]]; then
    echo "Retired hook backup already exists: ${RETIRED_HOOK_BACKUP}" >&2
    exit 1
  fi
fi

rsync_runtime_dir() {
  local source="$1"
  local target="$2"
  shift 2
  python3 - \
    "${source}" \
    "${target}" \
    "${RUNTIME_BACKUP_DIR}" \
    "${PHASE0_TRANSACTION_TEST_FAULT:-}" \
    "$@" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

source = Path(sys.argv[1])
target = Path(sys.argv[2])
backup_root = Path(sys.argv[3])
fault = sys.argv[4]
options = sys.argv[5:]
excludes = {
    options[index + 1].rstrip("/")
    for index, item in enumerate(options[:-1])
    if item == "--exclude"
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fsync_dir(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


backup_root.mkdir(parents=True, exist_ok=True)
transaction_root = Path(tempfile.mkdtemp(
    prefix=f"{hashlib.sha256(str(target).encode('utf-8')).hexdigest()[:16]}-",
    dir=backup_root,
))
journal_path = transaction_root / "transaction-journal.jsonl"
manifest_path = transaction_root / "backup-manifest.json"
entries = []
for source_path in sorted(source.rglob("*")):
    relative = source_path.relative_to(source)
    if any(relative == Path(exclude) or Path(exclude) in relative.parents for exclude in excludes):
        continue
    source_stat = source_path.lstat()
    if source_path.is_dir():
        continue
    if not stat.S_ISREG(source_stat.st_mode):
        raise SystemExit(f"non-regular source rejected: {relative}")
    target_path = target / relative
    if os.path.lexists(target_path):
        target_stat = target_path.lstat()
        if not stat.S_ISREG(target_stat.st_mode):
            raise SystemExit(f"non-regular target rejected: {relative}")
        metadata = {
            "uid": target_stat.st_uid,
            "gid": target_stat.st_gid,
            "mode": stat.S_IMODE(target_stat.st_mode),
        }
        backup_path = transaction_root / "files" / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_path, backup_path)
        pre_digest = digest(target_path)
    else:
        metadata = {
            "uid": source_stat.st_uid,
            "gid": source_stat.st_gid,
            "mode": stat.S_IMODE(source_stat.st_mode),
        }
        backup_path = None
        pre_digest = None
    entries.append({
        "relative": relative.as_posix(),
        "source": source_path,
        "target": target_path,
        "backup": backup_path,
        "pre_digest": pre_digest,
        "post_digest": digest(source_path),
        "metadata": metadata,
    })

manifest_path.write_text(
    json.dumps(
        [
            {
                "path": item["relative"],
                "pre_digest": item["pre_digest"],
                **item["metadata"],
            }
            for item in entries
        ],
        sort_keys=True,
    ) + "\n",
    encoding="utf-8",
)
replaced = []
reason = None
try:
    with journal_path.open("a", encoding="utf-8") as journal:
        for item in entries:
            target_path = item["target"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(prefix=f".{target_path.name}.", dir=target_path.parent)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(item["source"].read_bytes())
                    os.fchmod(handle.fileno(), item["metadata"]["mode"])
                    os.fchown(handle.fileno(), item["metadata"]["uid"], item["metadata"]["gid"])
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, target_path)
                fsync_dir(target_path.parent)
            finally:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass
            replaced.append(item)
            journal.write(json.dumps({
                "path": item["relative"],
                "pre_digest": item["pre_digest"],
                "post_digest": item["post_digest"],
            }, sort_keys=True) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
            if fault == "partial_copy":
                reason = fault
                raise RuntimeError(reason)
            if fault == "disk_digest_mismatch":
                target_path.write_bytes(b"injected mismatch\n")
            if digest(target_path) != item["post_digest"]:
                reason = "disk_digest_mismatch"
                raise RuntimeError(reason)
            if fault == "self_test_failure":
                reason = fault
                raise RuntimeError(reason)
except Exception as exc:
    reason = reason or "partial_copy"
    for item in reversed(replaced):
        target_path = item["target"]
        if item["backup"] is None:
            try:
                target_path.unlink()
            except FileNotFoundError:
                pass
        else:
            os.replace(item["backup"], target_path)
            os.chmod(target_path, item["metadata"]["mode"])
            os.chown(target_path, item["metadata"]["uid"], item["metadata"]["gid"])
        fsync_dir(target_path.parent)
        if item["pre_digest"] is not None and digest(target_path) != item["pre_digest"]:
            raise SystemExit(f"rollback digest mismatch: {item['relative']}") from exc
    print(json.dumps({
        "authorized_clone_root": None,
        "reason_code": reason,
        "status": "blocked",
    }, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    raise SystemExit(1)
PY
}

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

if [[ "${SYNC_AGENTS_ONLY}" == "true" || "${SYNC_AGENTS_FILE_ONLY}" == "true" ]]; then
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
  if [[ "${SYNC_AGENTS_ONLY}" == "true" ]]; then
    sync_codex_remote_docs
  fi
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
rendered_tmp="$(mktemp)"
python3 - "${TEMPLATE_PATH}" "${rendered_tmp}" "${npm_global_bin}" "${CODEX_HOME}" <<'PY'
import json
import os
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
for name, value in (("NPM_GLOBAL_BIN", sys.argv[3]), ("CODEX_HOME", os.path.abspath(sys.argv[4]))):
    text = text.replace("${" + name + "}", json.dumps(value, ensure_ascii=False)[1:-1])
Path(sys.argv[2]).write_text(text, encoding="utf-8")
PY

if rg -n '\$\{[A-Z0-9_]+\}' "${rendered_tmp}" >/dev/null 2>&1; then
  echo "Template rendering failed: unresolved placeholder remains in ${rendered_tmp}" >&2
  rm -f "${rendered_tmp}"
  exit 1
fi

if [[ -f "${CONFIG_TARGET}" ]]; then
  python3 - "${rendered_tmp}" "${CONFIG_TARGET}" "${SCRIPT_DIR}" <<'PY'
import json
import re
from pathlib import Path
import sys
import tomllib

rendered_path = Path(sys.argv[1])
existing_path = Path(sys.argv[2])
rendered = rendered_path.read_text(encoding="utf-8")
existing = existing_path.read_text(encoding="utf-8")
sys.path.insert(0, sys.argv[3])
from hook_registration import STATE_EVENT_NAMES, hook_commands


def remap_hook_state(existing_text, rendered_text):
    """Make each [hooks.state] entry follow its hook's command, not its position.

    The host keys hook state by event, group index, and hook index. When the
    template inserts or removes a hook, those positions move and an owner's
    on/off choice would land on another hook. Entries for a hook the template
    no longer registers are dropped for the same reason.
    """
    old_events = hook_commands(existing_text)
    new_events = hook_commands(rendered_text)

    def positions(events, event):
        return [(g, i, command) for g, group in enumerate(events.get(event, [])) for i, command in enumerate(group)]

    header = re.compile(r'^\[hooks\.state\."((?:[^"\\]|\\.)*)"\]\s*$')
    position_key = re.compile(r"^(.*config\.toml):([a-z_]+):(\d+):(\d+)$")
    moved, dropped, out, skipping = [], [], [], False
    for line in existing_text.splitlines(keepends=True):
        match = header.match(line.strip())
        if match is None:
            if line.lstrip().startswith("["):
                skipping = False
            if not skipping:
                out.append(line)
            continue
        skipping = False
        key = match.group(1)
        parts = position_key.match(key)
        event = STATE_EVENT_NAMES.get(parts.group(2)) if parts else None
        if event is None:
            out.append(line)
            continue
        group, index = int(parts.group(3)), int(parts.group(4))
        old = positions(old_events, event)
        found = [n for n, (g, i, _) in enumerate(old) if (g, i) == (group, index)]
        if not found:
            dropped.append(key)
            skipping = True
            continue
        command = old[found[0]][2]
        nth = sum(1 for g, i, c in old[:found[0]] if c == command)
        new = [(g, i) for g, i, c in positions(new_events, event) if c == command]
        if nth >= len(new):
            dropped.append(key)
            skipping = True
            continue
        target = f"{parts.group(1)}:{parts.group(2)}:{new[nth][0]}:{new[nth][1]}"
        if target != key:
            moved.append(f"{key} -> {target}")
            line = line.replace(json.dumps(key)[1:-1], json.dumps(target)[1:-1], 1)
        out.append(line)
    if moved:
        print("Moved hooks.state entries to follow their hooks: " + "; ".join(moved))
    if dropped:
        print("Dropped hooks.state entries for hooks the template no longer registers: " + "; ".join(dropped))
    return "".join(out)


existing = remap_hook_state(existing, rendered)


class TextMergeFailed(Exception):
    """The text-preserving merge could not read a spelling of the existing file."""


def refuse(reason):
    raise TextMergeFailed(reason)


try:
    existing_data = tomllib.loads(existing)
except tomllib.TOMLDecodeError as exc:
    raise SystemExit(
        f"config merge refused: the existing config.toml is not valid TOML ({exc}); "
        "repair it or move it aside, then sync again"
    )
template_data = tomllib.loads(rendered)


def statements(text):
    """Split TOML text into its statements: (start, end, is_header).

    A statement is a table header or one `key = value`. The scan skips
    comments, strings and bracketed values, so a line inside a multi-line
    string or array is never taken for a header or a key.
    """
    found = []
    index, size, start, depth, header = 0, len(text), None, 0, False
    while index < size:
        char = text[index]
        if start is None:
            if char in " \t\r\n":
                index += 1
                continue
            if char == "#":
                newline = text.find("\n", index)
                index = size if newline < 0 else newline + 1
                continue
            start, depth, header = index, 0, char == "["
        if text.startswith('"""', index) or text.startswith("'''", index):
            quote = text[index:index + 3]
            index += 3
            while index < size and not text.startswith(quote, index):
                if quote == '"""' and text[index] == "\\":
                    index += 1
                index += 1
            index += 3
            while index < size and text[index] == quote[0]:
                index += 1
            continue
        if char in "\"'":
            index += 1
            while index < size and text[index] not in (char, "\n"):
                if char == '"' and text[index] == "\\":
                    index += 1
                index += 1
            index += 1
            continue
        if char == "#":
            newline = text.find("\n", index)
            index = size if newline < 0 else newline
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == "\n" and depth <= 0:
            found.append((start, index, header))
            start = None
        index += 1
    if start is not None:
        found.append((start, size, header))
    return found


def header_path(header):
    """A header as its parsed key path, so `a."b-c"` and `a.b-c` compare equal."""
    try:
        node = tomllib.loads(header + "\n")
    except tomllib.TOMLDecodeError as exc:
        refuse(f"cannot read the table header {header.strip()!r}: {exc}")
    path = []
    while True:
        if isinstance(node, list) and len(node) == 1:
            node = node[0]
        elif isinstance(node, dict) and len(node) == 1:
            key, node = next(iter(node.items()))
            path.append(key)
        else:
            return tuple(path)


def statement_key(statement):
    try:
        parsed = tomllib.loads(statement + "\n")
    except tomllib.TOMLDecodeError as exc:
        refuse(f"cannot read the statement {statement.splitlines()[0]!r}: {exc}")
    return next(iter(parsed))


def split(text):
    """Return (top-level statements, table blocks) of a TOML text.

    A block is (path, is_array, text, start, end). Its text runs from its
    header to the next header.
    """
    parts = statements(text)
    headers = [(start, end) for start, end, is_header in parts if is_header]
    first = headers[0][0] if headers else len(text)
    top = [(statement_key(text[start:end]), text[start:end])
           for start, end, is_header in parts if not is_header and start < first]
    blocks = []
    for position, (start, end) in enumerate(headers):
        stop = headers[position + 1][0] if position + 1 < len(headers) else len(text)
        header = text[start:end]
        blocks.append((header_path(header), header.lstrip().startswith("[["), text[start:stop].strip(), start, stop))
    return top, blocks


def block_keys(block):
    return {statement_key(block[start:end]): block[start:end]
            for start, end, is_header in statements(block) if not is_header}


def preserve_table(path):
    """Tables the host or the owner writes at runtime and the sync has always kept."""
    return (
        (path[0] in ("plugins", "marketplaces", "projects") and len(path) > 1)
        or path[:2] == ("hooks", "state")
        or path[0] == "desktop"
        or path == ("memories",)
        or path in (("mcp_servers", "node_repl"), ("mcp_servers", "node_repl", "env"))
    )


def managed_table(path):
    """Tables this script renders from the template or merges by its own rule.

    Hook registration comes only from the template. `hooks.state` is the
    host's record of which hooks the owner trusted or disabled; it is kept.
    """
    return (
        path == ("features",)
        or path[:2] == ("skills", "config")
        or (path[0] == "hooks" and not preserve_table(path))
    )


def under(path, parents):
    return any(path[:size] in parents for size in range(1, len(path)))


def emit_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, float):
        return {"inf": "inf", "-inf": "-inf", "nan": "nan"}.get(str(value), repr(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(emit_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{json.dumps(key)} = {emit_value(item)}" for key, item in value.items()) + " }"
    return value.isoformat()


def as_table_blocks(path, table):
    """Write a parsed table as header blocks, so table rules apply to it."""
    blocks = []
    own = [f"{json.dumps(key)} = {emit_value(value)}" for key, value in table.items() if not isinstance(value, dict)]
    if own:
        header = "[" + ".".join(json.dumps(part) for part in path) + "]"
        blocks.append((path, False, header + "\n" + "\n".join(own)))
    for key, value in table.items():
        if isinstance(value, dict):
            blocks.extend(as_table_blocks(path + (key,), value))
    return blocks


def append_block(text, block):
    return text.rstrip() + "\n\n" + block + "\n"


def merge_table_keys(text, path, source_block):
    """Add to the template's table the keys only the existing table has."""
    target = next((block for block in split(text)[1] if block[0] == path and not block[1]), None)
    if target is None:
        return text
    target_keys = block_keys(target[2])
    additions = [
        line for key, line in block_keys(source_block).items()
        if key not in target_keys and not (path == ("features",) and key == "codex_hooks")
    ]
    if not additions:
        return text
    end = target[4]
    return text[:end].rstrip() + "\n" + "\n".join(additions) + "\n\n" + text[end:].lstrip("\n")


def text_merge(rendered):
    existing_top, existing_blocks = split(existing)
    rendered_top, rendered_blocks = split(rendered)
    rendered_paths = {path for path, is_array, *_ in rendered_blocks if not is_array}
    rendered_array_paths = {path for path, is_array, *_ in rendered_blocks if is_array}
    skill_paths = {
        tomllib.loads(block)["skills"]["config"][0]["path"]
        for path, is_array, block, *_ in rendered_blocks if is_array and path == ("skills", "config")
    }
    kept_array_paths = set()

    # Top-level keys the template does not set belong to the owner or to the host.
    rendered_top_keys = {key for key, _ in rendered_top}
    # A top-level statement can also write into a table, as `features.x = true` or
    # as an inline table. Where the template or this script owns that table, the
    # statement is read as a table so the same rules apply to it.
    table_roots = {path[0] for path, *_ in rendered_blocks} | {"features", "hooks", "skills"}
    as_tables = [statement for key, statement in existing_top if key in table_roots]
    runtime_top = [
        (key, statement) for key, statement in existing_top
        if key not in rendered_top_keys and key not in table_roots
    ]
    top_table_blocks = []
    if as_tables:
        for key, value in tomllib.loads("\n".join(as_tables) + "\n").items():
            if isinstance(value, dict):
                top_table_blocks.extend(as_table_blocks((key,), value))
    if runtime_top:
        insert_at = rendered_blocks[0][3] if rendered_blocks else len(rendered)
        rendered = (
            rendered[:insert_at].rstrip()
            + "\n"
            + "\n".join(statement for _, statement in runtime_top)
            + "\n\n"
            + rendered[insert_at:].lstrip("\n")
        )

    for path, is_array, block, *_ in top_table_blocks + existing_blocks:
        if is_array and path == ("skills", "config"):
            skill_path = tomllib.loads(block)["skills"]["config"][0]["path"]
            if skill_path not in skill_paths:
                rendered = append_block(rendered, block)
                skill_paths.add(skill_path)
        elif under(path, kept_array_paths):
            # Part of an array element that was kept. Each element has its own.
            rendered = append_block(rendered, block)
        elif is_array and preserve_table(path):
            rendered = append_block(rendered, block)
            kept_array_paths.add(path)
        elif path == ("features",):
            rendered = merge_table_keys(rendered, path, block)
        elif preserve_table(path):
            if path in rendered_paths:
                rendered = merge_table_keys(rendered, path, block)
            else:
                rendered = append_block(rendered, block)
                rendered_paths.add(path)
        elif managed_table(path) or under(path, rendered_array_paths):
            # Rendered from the template only, or part of an element of an array
            # the template owns; that element was not carried over.
            continue
        elif is_array:
            if path not in rendered_array_paths:
                rendered = append_block(rendered, block)
                kept_array_paths.add(path)
        elif path not in rendered_paths:
            # A table the template does not define was put there by the owner or
            # by the host. Dropping it silently loses their settings.
            rendered = append_block(rendered, block)
            rendered_paths.add(path)

    return rendered


def is_table_array(value):
    return isinstance(value, list) and bool(value) and all(isinstance(item, dict) for item in value)


def merge_data(path, template, current, kept):
    """What the merged config must contain, worked out on parsed data.

    The template keeps the keys and arrays it sets. Hook registration comes
    only from the template. Everything else the existing file holds is kept:
    top-level keys, tables the template does not define, sub-tables of the
    tables it does define, and extra keys in `features` and in the tables the
    host or the owner writes at runtime.
    """
    result = dict(template)
    # The template owns the direct keys of the tables it writes a header for.
    open_table = not path or path == ("features",) or preserve_table(path) or path not in template_tables
    for key, value in current.items():
        child = path + (key,)
        if child[0] == "hooks" and len(child) > 1 and not preserve_table(child):
            continue
        if child == ("features", "codex_hooks"):
            continue
        if child == ("skills", "config") and is_table_array(value) and is_table_array(template.get(key)):
            known = {entry.get("path") for entry in template[key]}
            result[key] = template[key] + [entry for entry in value if entry.get("path") not in known]
            continue
        if isinstance(value, dict):
            if key not in template:
                result[key] = value
                if not preserve_table(child):
                    kept.append("[" + ".".join(child) + "]")
            elif isinstance(template[key], dict):
                result[key] = merge_data(child, template[key], value, kept)
        elif key not in template and (open_table or is_table_array(value)):
            result[key] = value
            if not path and key != "notify":
                kept.append(key)
            elif is_table_array(value) and not preserve_table(child):
                kept.append("[[" + ".".join(child) + "]]")
    return result


def emit_table(path, table, lines):
    for key, value in table.items():
        if not isinstance(value, dict) and not is_table_array(value):
            lines.append(f"{json.dumps(key, ensure_ascii=False)} = {emit_value(value)}")
    for key, value in table.items():
        child = path + (key,)
        name = ".".join(json.dumps(part, ensure_ascii=False) for part in child)
        if isinstance(value, dict):
            if not value or any(not isinstance(item, dict) and not is_table_array(item) for item in value.values()):
                lines.extend(["", f"[{name}]"])
            emit_table(child, value, lines)
        elif is_table_array(value):
            for element in value:
                lines.extend(["", f"[[{name}]]"])
                emit_table(child, element, lines)


template_tables = {path for path, is_array, *_ in split(rendered)[1] if not is_array}
kept_runtime_only = []
expected = merge_data((), template_data, existing_data, kept_runtime_only)
try:
    merged_text = text_merge(rendered)
    if tomllib.loads(merged_text) != expected:
        raise TextMergeFailed("the text merge and the parsed merge disagree")
except (TextMergeFailed, tomllib.TOMLDecodeError, KeyError, IndexError, TypeError) as exc:
    # The existing file uses a spelling the text merge does not read. Write the
    # parsed result instead: the settings are exact, the comments are not kept.
    lines = []
    emit_table((), expected, lines)
    merged_text = "\n".join(lines).lstrip("\n") + "\n"
    if tomllib.loads(merged_text) != expected:
        raise SystemExit("config merge refused: the merged config.toml does not hold the expected settings")
    print(f"config.toml was rewritten from its parsed settings; comments in it were not kept ({exc})")

if kept_runtime_only:
    print("Kept runtime-only config entries the template does not define: " + ", ".join(kept_runtime_only))

rendered_path.write_text(merged_text, encoding="utf-8")
PY
fi

cp "${rendered_tmp}" "${CONFIG_TARGET}"
rm -f "${rendered_tmp}"

if [[ -d "${REPO_ROOT}/codex/agents" ]]; then
  mkdir -p "${CODEX_HOME}/agents"
  for source in "${REPO_ROOT}/codex/agents/"*.toml; do
    [[ -f "${source}" ]] || continue
    filename="$(basename "${source}")"
    target="${CODEX_HOME}/agents/${filename}"
    if [[ -f "${target}" ]]; then
      backup="${target}.backup.$(date +%Y%m%d%H%M%S)"
      cp "${target}" "${backup}"
      echo "Backed up existing custom agent to ${backup}"
    fi
    cp "${source}" "${target}"
  done
fi

mkdir -p "${CODEX_HOME}/skills"
# Repo skills are managed overlays; preserve runtime-only/local skills that are
# intentionally outside this repository's source-of-truth.
# skills/.system belongs to the host: each Codex version ships and rewrites its
# own set. The repository snapshot is a record, not a source to deploy.
rsync -a --exclude '/.system/' "${REPO_ROOT}/codex/skills/" "${CODEX_HOME}/skills/"

# codex/workflow (claude-code-workflow) was retired on 2026-11-27 (SHI-637).
# An existing ~/.codex/workflow is left in place; sync no longer writes it.

if [[ -f "${REPO_ROOT}/codex/AGENTS.md" ]]; then
  if [[ -f "${CODEX_HOME}/AGENTS.md" ]]; then
    backup="${CODEX_HOME}/AGENTS.md.backup.$(date +%Y%m%d%H%M%S)"
    cp "${CODEX_HOME}/AGENTS.md" "${backup}"
    echo "Backed up existing AGENTS to ${backup}"
  fi
  cp "${REPO_ROOT}/codex/AGENTS.md" "${CODEX_HOME}/AGENTS.md"
fi

sync_codex_remote_docs

# Hook registration is rendered into config.toml from codex/config.template.toml.
# ${CODEX_HOME}/hooks.json belongs to other tools and is never written here.

if [[ -d "${REPO_ROOT}/codex/hooks" ]]; then
  mkdir -p "${CODEX_HOME}/hooks"
  rsync_runtime_dir "${REPO_ROOT}/codex/hooks" "${CODEX_HOME}/hooks"
fi

if [[ -e "${RETIRED_HOOK_TARGET}" || -L "${RETIRED_HOOK_TARGET}" ]]; then
  if [[ ! -f "${RETIRED_HOOK_TARGET}" || -L "${RETIRED_HOOK_TARGET}" ]]; then
    echo "Retired hook target is not a regular file: ${RETIRED_HOOK_TARGET}" >&2
    exit 1
  fi
  if [[ -e "${RETIRED_HOOK_BACKUP}" || -L "${RETIRED_HOOK_BACKUP}" ]]; then
    echo "Retired hook backup already exists: ${RETIRED_HOOK_BACKUP}" >&2
    exit 1
  fi
  mkdir -p "$(dirname "${RETIRED_HOOK_BACKUP}")"
  mv "${RETIRED_HOOK_TARGET}" "${RETIRED_HOOK_BACKUP}"
  echo "Retired hook backed up to ${RETIRED_HOOK_BACKUP}"
fi

if [[ -d "${REPO_ROOT}/codex/runtime" ]]; then
  mkdir -p "${CODEX_HOME}/runtime"
  rsync_runtime_dir "${REPO_ROOT}/codex/runtime" "${CODEX_HOME}/runtime"
fi

if [[ -f "${REPO_ROOT}/codex/runtime/harness-guard-targets.json" ]]; then
  sync_harness_targets
fi

if [[ -d "${REPO_ROOT}/codex/zsh" ]]; then
  mkdir -p "${CODEX_HOME}/zsh"
  rsync_runtime_dir "${REPO_ROOT}/codex/zsh" "${CODEX_HOME}/zsh"
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
if plugin.get("name") != "superpowers" or plugin.get("version") != "6.2.0":
    raise SystemExit("Superpowers plugin manifest must be superpowers version 6.2.0")
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
    python3 -c 'import json, sys; data = json.load(sys.stdin); sys.exit(0 if any(p.get("pluginId") == "superpowers@superpowers-dev" and p.get("installed") is True and p.get("enabled") is True and p.get("version") == "6.2.0" for p in data.get("installed", [])) else 1)'
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
