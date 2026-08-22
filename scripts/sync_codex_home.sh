#!/usr/bin/env bash
set -euo pipefail

# 同步仓库配置到目标 Codex home，并固定 superpowers 版本。
REPO_ROOT=""
CODEX_HOME="${HOME}/.codex"
SKIP_SUPERPOWERS_SYNC="false"
SYNC_AGENTS_ONLY="false"
FORCE_DOWNGRADE="false"
BOOTSTRAP_LOADED_READBACK="false"
OPERATOR_CHECKPOINT=""
PROMOTE_HARNESS_GUARD="false"

usage() {
  cat <<USAGE
Usage: sync_codex_home.sh --repo-root <path> [--codex-home <path>] [--skip-superpowers-sync] [--sync-agents-only] [--promote-harness-guard] [--force-downgrade --operator-checkpoint <path>] [--bootstrap-loaded-readback --operator-checkpoint <path>]

Options:
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
    "${PHASE0_PRODUCER_MANIFEST:-}" <<'PY'
import hashlib
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

digest = hashlib.sha256()
try:
    tracked = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z", "--", "codex/"],
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        blocked("source_enumeration_failed")
    for relative in sorted(part for part in tracked.stdout.split(b"\0") if part):
        path = repo_root / os.fsdecode(relative)
        content = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
        digest.update(relative + b"\0" + str(len(content)).encode("ascii") + b"\0" + content)
except OSError:
    blocked("source_enumeration_failed")
source_digest = digest.hexdigest()
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
    blocked("source_digest_unapproved", source_digest=f"sha256:{source_digest}")

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

preflight_source_attestation

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
RUNTIME_BACKUP_DIR="${CODEX_HOME}/runtime-backups/$(date -u +%Y%m%dT%H%M%SZ)/"

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
rsync -a "${REPO_ROOT}/codex/skills/" "${CODEX_HOME}/skills/"

if [[ -d "${REPO_ROOT}/codex/workflow" ]]; then
  mkdir -p "${CODEX_HOME}/workflow"
  # workflow/memory 属于运行态热数据，不从仓库模板回灌。
  rsync_runtime_dir "${REPO_ROOT}/codex/workflow" "${CODEX_HOME}/workflow" --exclude 'memory/'
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
  rsync_runtime_dir "${REPO_ROOT}/codex/hooks" "${CODEX_HOME}/hooks"
fi

retired_hook="${CODEX_HOME}/hooks/model_router.py"
if [[ -e "${retired_hook}" || -L "${retired_hook}" ]]; then
  if [[ ! -f "${retired_hook}" || -L "${retired_hook}" ]]; then
    echo "Retired hook target is not a regular file: ${retired_hook}" >&2
    exit 1
  fi
  retired_backup="${RUNTIME_BACKUP_DIR}/retired/hooks/model_router.py"
  if [[ -e "${retired_backup}" || -L "${retired_backup}" ]]; then
    echo "Retired hook backup already exists: ${retired_backup}" >&2
    exit 1
  fi
  mkdir -p "$(dirname "${retired_backup}")"
  mv "${retired_hook}" "${retired_backup}"
  echo "Retired hook backed up to ${retired_backup}"
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
