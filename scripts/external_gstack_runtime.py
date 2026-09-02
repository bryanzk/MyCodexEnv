#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


STATUS_SCHEMA = "mce.external_gstack.status.v1"
AUTO_GENERATED_BANNER = "<!-- AUTO-GENERATED from"
SIDECAR_PAIRS = (
    (".agents/skills/gstack/SKILL.md", "SKILL.md"),
    ("bin", "bin"),
    ("lib", "lib"),
    ("browse/dist", "browse/dist"),
    ("browse/bin", "browse/bin"),
    (".agents/skills/gstack-upgrade/SKILL.md", "gstack-upgrade/SKILL.md"),
    (".agents/skills/gstack-office-hours/SKILL.md", "office-hours/SKILL.md"),
    ("review/checklist.md", "review/checklist.md"),
    ("review/design-checklist.md", "review/design-checklist.md"),
    ("review/greptile-triage.md", "review/greptile-triage.md"),
    ("review/TODOS-format.md", "review/TODOS-format.md"),
    ("ETHOS.md", "ETHOS.md"),
    ("supabase/config.sh", "supabase/config.sh"),
)
SIDECAR_DIRS = (".", "browse", "gstack-upgrade", "office-hours", "review", "supabase")
SIDECAR_DIRECTORY_TARGETS = {"bin", "lib", "browse/dist", "browse/bin"}
SAFE_NAME = re.compile(r"^gstack(?:-[a-z0-9][a-z0-9-]*)?$")
SAFE_OPERATION_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,100}$")
KNOWN_JOURNAL_STATES = {
    "planned", "staged", "cutting_over", "sidecar_old_moved", "sidecar_installed",
    "verified", "complete", "rolling_back", "rolled_back", "blocked",
}
MAX_QUIESCENCE_AGE_SECONDS = 15 * 60


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    detail: str

    def as_json(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "detail": self.detail,
        }


class LockContended(RuntimeError):
    pass


def locked_runtime(codex_home: Path):
    class RuntimeLock:
        def __enter__(self):
            codex_home.mkdir(parents=True, exist_ok=True)
            self.handle = (codex_home / ".phase0-sync.lock").open("a+")
            try:
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                self.handle.close()
                raise LockContended("lock_contended") from exc
            return self.handle

        def __exit__(self, exc_type, exc, traceback):
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()

    return RuntimeLock()


def emit_error(reason_code: str, detail: str, *, exit_code: int = 2) -> int:
    print(
        json.dumps({"status": "blocked", "reason_code": reason_code, "detail": detail}, sort_keys=True),
        file=sys.stderr,
    )
    return exit_code


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def set_journal_state(journal_path: Path, journal: dict[str, Any], state: str) -> None:
    journal["state"] = state
    durable_write_json(journal_path, journal)


def require_manifest(manifest: dict[str, Any], *, require_fresh_receipt: bool = True) -> None:
    required = {
        "schema_version", "operation_id", "repo_root", "codex_home", "gstack_root", "operation_root",
        "staging_root", "backup_root", "external_head", "external_version", "inventory", "flat_generated",
        "replace_real", "existing_links", "sidecar_pairs", "sidecar_dirs", "approval_context",
        "quiescence_receipt",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"manifest missing fields: {missing}")
    if manifest["schema_version"] != "mce.external_gstack.v1":
        raise ValueError("unsupported manifest schema")
    context = manifest["approval_context"]
    context_keys = {
        "authority_sha256", "external_root_sha256", "runtime_skills_sha256",
        "non_target_sha256", "replace_real_prestates", "sidecar_prestate_sha256", "warning_tuples",
    }
    if not isinstance(context, dict) or set(context) != context_keys:
        raise ValueError("approval context fields mismatch")
    digest_keys = context_keys - {"replace_real_prestates", "warning_tuples"}
    if any(not isinstance(context[key], str) or not re.fullmatch(r"[0-9a-f]{64}", context[key])
           for key in digest_keys):
        raise ValueError("approval context digest invalid")
    prestates = context["replace_real_prestates"]
    if not isinstance(prestates, dict) or any(
        not SAFE_NAME.fullmatch(name) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
        for name, value in prestates.items()
    ):
        raise ValueError("approval target prestates invalid")
    if not isinstance(context["warning_tuples"], list):
        raise ValueError("approval warning tuples invalid")
    receipt = manifest["quiescence_receipt"]
    if not isinstance(receipt, dict) or receipt.get("status") != "approved":
        raise ValueError("approved quiescence receipt required")
    if receipt.get("operation_id") != manifest["operation_id"] or receipt.get("approved_by") != "owner":
        raise ValueError("quiescence receipt identity mismatch")
    try:
        approved_at = datetime.fromisoformat(str(receipt["timestamp"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise ValueError("quiescence receipt timestamp invalid") from exc
    if approved_at.tzinfo is None:
        raise ValueError("quiescence receipt timestamp must be timezone-aware")
    if require_fresh_receipt:
        age = (datetime.now(timezone.utc) - approved_at.astimezone(timezone.utc)).total_seconds()
        if age < -60 or age > MAX_QUIESCENCE_AGE_SECONDS:
            raise ValueError("quiescence receipt is stale")


def validate_operation_paths(manifest: dict[str, Any]) -> tuple[Path, Path, Path, Path, Path]:
    codex_home = lexical_absolute(Path(manifest["codex_home"]))
    operation_root = lexical_absolute(Path(manifest["operation_root"]))
    staging_root = lexical_absolute(Path(manifest["staging_root"]))
    backup_root = lexical_absolute(Path(manifest["backup_root"]))
    runtime_backups = codex_home / "runtime-backups"
    operation_id = manifest["operation_id"]
    if not isinstance(operation_id, str) or not SAFE_OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operation id is unsafe")
    if operation_root.parent != runtime_backups:
        raise ValueError("operation root must be directly under runtime-backups")
    if operation_root.name != f"{operation_id}-external-gstack":
        raise ValueError("operation root basename must match operation id")
    if staging_root != operation_root / "staging" or backup_root != operation_root / "backup":
        raise ValueError("staging and backup roots must use canonical operation paths")
    skills = codex_home / "skills"
    if operation_root.exists() or staging_root.exists() or backup_root.exists():
        raise FileExistsError("operation, staging, and backup paths must start absent")
    if skills.stat().st_dev != runtime_backups.parent.stat().st_dev:
        raise ValueError("runtime backup base must share the skills filesystem")
    return codex_home, skills, operation_root, staging_root, backup_root


def validate_recovery_paths(operation_root: Path, journal: dict[str, Any]) -> tuple[Path, Path, Path]:
    manifest_data = journal["manifest"]
    require_manifest(manifest_data, require_fresh_receipt=False)
    codex_home = lexical_absolute(Path(manifest_data["codex_home"]))
    if lexical_absolute(Path(journal["codex_home"])) != codex_home:
        raise ValueError("journal and manifest codex_home mismatch")
    if operation_root.parent != codex_home / "runtime-backups":
        raise ValueError("recovery operation root must be directly under runtime-backups")
    if lexical_absolute(Path(manifest_data["operation_root"])) != operation_root:
        raise ValueError("journal operation root mismatch")
    staging_root = lexical_absolute(Path(manifest_data["staging_root"]))
    backup_root = lexical_absolute(Path(manifest_data["backup_root"]))
    if staging_root != operation_root / "staging" or backup_root != operation_root / "backup":
        raise ValueError("recovery staging and backup paths are noncanonical")
    if not codex_home.is_dir() or codex_home.is_symlink() or not operation_root.is_dir() or operation_root.is_symlink():
        raise ValueError("recovery roots must be real directories")
    if journal.get("state") not in KNOWN_JOURNAL_STATES:
        raise ValueError("unknown journal state")
    expected_digest = hashlib.sha256(
        json.dumps(manifest_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if journal.get("manifest_sha256") != expected_digest:
        raise ValueError("journal manifest digest mismatch")
    return codex_home, codex_home / "skills", backup_root


def prepare_sidecar(root: Path, staging_sidecar: Path, pairs: list[list[str]]) -> None:
    staging_sidecar.mkdir(parents=True, mode=0o700)
    for _, target_relative in pairs:
        target = staging_sidecar / target_relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"staged sidecar target exists: {target}")
    for source_relative, target_relative in pairs:
        source = root / source_relative
        if source.is_symlink() or not source.exists() or root.resolve() not in source.resolve().parents:
            raise ValueError(f"sidecar source invalid: {source}")
        if (target_relative in SIDECAR_DIRECTORY_TARGETS) != source.is_dir():
            raise ValueError(f"sidecar source type mismatch: {source}")
        if target_relative not in SIDECAR_DIRECTORY_TARGETS and not source.is_file():
            raise ValueError(f"sidecar source type mismatch: {source}")
        os.symlink(source, staging_sidecar / target_relative)


def verify_transaction_sidecar(root: Path, sidecar: Path, pairs: list[list[str]], dirs: list[str]) -> None:
    if not sidecar.is_dir() or sidecar.is_symlink():
        raise RuntimeError("sidecar verification failed")
    expected = {relative for _, relative in pairs} | {relative for relative in dirs if relative != "."}
    actual = {item.relative_to(sidecar).as_posix() for item in sidecar.rglob("*")}
    if actual != expected:
        raise RuntimeError("sidecar contains unexpected paths")
    for source_relative, target_relative in pairs:
        source = root / source_relative
        target = sidecar / target_relative
        if not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False):
            raise RuntimeError(f"sidecar target verification failed: {target_relative}")


def verify_live_transaction(root: Path, skills: Path, manifest_data: dict[str, Any]) -> None:
    for name in manifest_data["flat_generated"]:
        target = skills / name
        source = root / ".agents" / "skills" / name
        if not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False):
            raise RuntimeError(f"flat target verification failed: {name}")
    verify_transaction_sidecar(
        root, skills / "gstack", manifest_data["sidecar_pairs"], manifest_data["sidecar_dirs"]
    )


def remove_new_sidecar(sidecar: Path, pairs: list[list[str]]) -> None:
    for _, relative in reversed(pairs):
        target = sidecar / relative
        if target.is_symlink():
            target.unlink()
    for relative in sorted({str(Path(target).parent) for _, target in pairs if str(Path(target).parent) != "."},
                           key=lambda value: len(Path(value).parts), reverse=True):
        directory = sidecar / relative
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    if sidecar.is_dir() and not any(sidecar.iterdir()):
        sidecar.rmdir()


def run(command: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(str(path.expanduser()))))


def parse_frontmatter_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*[\"']?([^\"'\n]+)", text)
    if not match:
        raise ValueError(f"missing frontmatter name: {path}")
    return match.group(1).strip()


def vendored_generated_names(repo_root: Path) -> set[str]:
    vendor = repo_root / "codex" / "skills" / "gstack"
    if not vendor.is_dir():
        return set()
    names: set[str] = set()
    for child in sorted(vendor.iterdir()):
        skill = child / "SKILL.md"
        if not child.is_dir() or not skill.is_file():
            continue
        name = parse_frontmatter_name(skill)
        generated = name if name.startswith("gstack") else f"gstack-{name}"
        if not SAFE_NAME.fullmatch(generated):
            raise ValueError(f"unsafe vendored gstack name: {generated}")
        names.add(generated)
    return names


def repo_owned_nonexternal_names(repo_root: Path) -> set[str]:
    repo_skills = repo_root / "codex" / "skills"
    generated = vendored_generated_names(repo_root)
    if not repo_skills.is_dir():
        return set()
    names: set[str] = set()
    for child in sorted(repo_skills.iterdir()):
        if not child.name.startswith("gstack-"):
            continue
        if not child.is_dir() or child.is_symlink():
            raise ValueError(f"invalid repo gstack skill path: {child}")
        skill = child / "SKILL.md"
        if not skill.is_file() or skill.is_symlink():
            raise ValueError(f"invalid repo gstack skill manifest: {skill}")
        text = skill.read_text(encoding="utf-8")
        if child.name in generated or AUTO_GENERATED_BANNER in text:
            continue
        name = parse_frontmatter_name(skill)
        if name != child.name:
            raise ValueError(f"repo gstack skill name mismatch: {child.name} != {name}")
        names.add(child.name)
    return names


def default_root(codex_home: Path) -> Path:
    return lexical_absolute(codex_home.parent / ".gstack" / "repos" / "gstack")


def select_root(cli_root: str | None, environment: Mapping[str, str], codex_home: Path) -> tuple[str, Path, bool]:
    if cli_root:
        return "cli", lexical_absolute(Path(cli_root)), True
    env_root = environment.get("GSTACK_ROOT", "").strip()
    if env_root:
        return "env", lexical_absolute(Path(env_root)), True
    return "default", default_root(codex_home), False


def symlink_raw_target(path: Path) -> str:
    return os.readlink(path)


def reserved_runtime_footprints(repo_root: Path, codex_home: Path) -> list[tuple[Path, str]]:
    skills = codex_home / "skills"
    if not skills.is_dir():
        return []
    nonexternal = repo_owned_nonexternal_names(repo_root)
    matches: list[tuple[Path, str]] = []
    for child in sorted(skills.iterdir()):
        if not child.is_symlink():
            continue
        if child.name == "gstack" or (child.name.startswith("gstack-") and child.name not in nonexternal):
            matches.append((child, symlink_raw_target(child)))
    sidecar = skills / "gstack"
    if sidecar.is_dir() and not sidecar.is_symlink():
        for _, relative in SIDECAR_PAIRS:
            target = sidecar / relative
            if target.is_symlink():
                matches.append((target, symlink_raw_target(target)))
    return matches


def external_inventory(root: Path) -> list[str]:
    skills = root / ".agents" / "skills"
    if not skills.is_dir():
        raise ValueError(f"external generated skills directory missing: {skills}")
    names: list[str] = []
    for child in sorted(skills.iterdir()):
        if not child.is_dir() or not (child / "SKILL.md").is_file():
            continue
        name = child.name
        if not SAFE_NAME.fullmatch(name) or name in names:
            raise ValueError(f"unsafe or duplicate external gstack name: {name}")
        names.append(name)
    if "gstack" not in names:
        raise ValueError("external inventory missing root gstack skill")
    return names


def validate_external_root(root: Path) -> tuple[list[str], str, list[Finding]]:
    findings: list[Finding] = []
    if not root.is_dir():
        return [], "", [Finding("error", "external_gstack_root_invalid", str(root), "root is missing or not a directory")]
    code, out, err = run(["git", "-C", str(root), "rev-parse", "--show-toplevel"])
    if code != 0 or lexical_absolute(Path(out)).resolve(strict=False) != root.resolve(strict=False):
        findings.append(Finding("error", "external_gstack_root_invalid", str(root), err or "path is not the exact git root"))
    version_path = root / "VERSION"
    setup_path = root / "setup"
    if not version_path.is_file() or version_path.is_symlink():
        findings.append(Finding("error", "external_gstack_root_invalid", str(version_path), "VERSION must be a regular file"))
    if not setup_path.is_file() or setup_path.is_symlink() or not os.access(setup_path, os.X_OK):
        findings.append(Finding("error", "external_gstack_root_invalid", str(setup_path), "setup must be an executable regular file"))
    try:
        inventory = external_inventory(root)
    except (OSError, UnicodeError, ValueError) as exc:
        findings.append(Finding("error", "external_gstack_inventory_invalid", str(root), str(exc)))
        inventory = []
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else ""
    return inventory, version, findings


def manifest(path: Path) -> dict[str, tuple[str, str]]:
    if not path.is_dir():
        return {}
    result: dict[str, tuple[str, str]] = {}
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            result[relative] = ("symlink", os.readlink(item))
        elif item.is_file():
            result[relative] = ("file", hashlib.sha256(item.read_bytes()).hexdigest())
        elif item.is_dir():
            result[relative] = ("dir", "")
    return result


def path_digest(path: Path, excluded_top_level: set[str] | None = None) -> str:
    entries: list[tuple[str, str, int, str]] = []
    excluded_top_level = excluded_top_level or set()

    def visit(item: Path, relative: str) -> None:
        metadata = item.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if item.is_symlink():
            entries.append((relative, "symlink", mode, os.readlink(item)))
            return
        if item.is_file():
            entries.append((relative, "file", mode, hashlib.sha256(item.read_bytes()).hexdigest()))
            return
        if item.is_dir():
            entries.append((relative, "dir", mode, ""))
            for child in sorted(item.iterdir(), key=lambda value: value.name):
                if relative == "" and child.name in excluded_top_level:
                    continue
                visit(child, f"{relative}/{child.name}" if relative else child.name)
            return
        raise ValueError(f"unsupported filesystem type: {item}")

    visit(path, "")
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def non_target_digest(skills: Path, flat_generated: list[str]) -> str:
    external_names = set(flat_generated) | {"gstack"}
    payload = {
        child.name: path_digest(child)
        for child in sorted(skills.iterdir(), key=lambda value: value.name)
        if child.name not in external_names and child.name != ".system"
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def current_warning_tuples(repo_root: Path, codex_home: Path, gstack_root: Path) -> list[list[str]]:
    checker = Path(__file__).with_name("check_skill_compatibility.py")
    code, out, err = run([
        sys.executable, str(checker), "--repo-root", str(repo_root), "--codex-home", str(codex_home),
        "--gstack-root", str(gstack_root), "--json",
    ])
    if code not in {0, 1} or not out:
        raise RuntimeError(err or "skill compatibility checker did not return JSON")
    payload = json.loads(out)
    return sorted([
        [item["severity"], item["code"], item["path"]]
        for item in payload.get("findings", [])
        if item.get("severity") == "warning"
    ])


def capture_approval_context(
    repo_root: Path,
    codex_home: Path,
    gstack_root: Path,
    flat_generated: list[str],
) -> dict[str, Any]:
    skills = codex_home / "skills"
    replace_real_prestates = {
        name: path_digest(skills / name)
        for name in flat_generated
        if (skills / name).is_dir() and not (skills / name).is_symlink()
    }
    return {
        "authority_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "external_root_sha256": path_digest(gstack_root, {".git"}),
        "runtime_skills_sha256": path_digest(skills, {".system"}),
        "non_target_sha256": non_target_digest(skills, flat_generated),
        "replace_real_prestates": replace_real_prestates,
        "sidecar_prestate_sha256": path_digest(skills / "gstack"),
        "warning_tuples": current_warning_tuples(repo_root, codex_home, gstack_root),
    }


def find_incomplete_operation(codex_home: Path, current: Path) -> Path | None:
    runtime_backups = codex_home / "runtime-backups"
    if not runtime_backups.is_dir():
        return None
    for journal_path in sorted(runtime_backups.glob("*-external-gstack/operation.json")):
        if journal_path.parent == current:
            continue
        try:
            state = json.loads(journal_path.read_text(encoding="utf-8")).get("state")
        except (OSError, UnicodeError, json.JSONDecodeError):
            return journal_path.parent
        if state not in {"complete", "rolled_back"}:
            return journal_path.parent
    return None


def active_topology(root: Path, codex_home: Path, inventory: list[str]) -> tuple[int, list[str], list[str], str, list[Finding]]:
    runtime_skills = codex_home / "skills"
    missing: list[str] = []
    drifted: list[str] = []
    findings: list[Finding] = []
    visible = 0
    flat = sorted(set(inventory) - {"gstack"})
    for name in flat:
        source = root / ".agents" / "skills" / name
        target = runtime_skills / name
        if not target.exists() and not target.is_symlink():
            missing.append(name)
            continue
        if target.is_symlink():
            if target.resolve(strict=False) == source.resolve(strict=False):
                visible += 1
            else:
                drifted.append(name)
            continue
        skill = target / "SKILL.md"
        if target.is_dir() and skill.is_file() and AUTO_GENERATED_BANNER in skill.read_text(encoding="utf-8", errors="replace") \
                and manifest(target) == manifest(source):
            visible += 1
        else:
            drifted.append(name)

    sidecar = runtime_skills / "gstack"
    sidecar_state = "ok"
    expected_rel = {relative for _, relative in SIDECAR_PAIRS}
    expected_dirs = {relative for relative in SIDECAR_DIRS if relative != "."}
    if not sidecar.is_dir() or sidecar.is_symlink():
        sidecar_state = "missing"
        missing.append("gstack")
    else:
        for source_relative, target_relative in SIDECAR_PAIRS:
            source = root / source_relative
            target = sidecar / target_relative
            if not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False):
                sidecar_state = "drifted"
        actual = set()
        for item in sidecar.rglob("*"):
            actual.add(item.relative_to(sidecar).as_posix())
        allowed = expected_rel | expected_dirs
        if actual != allowed:
            sidecar_state = "drifted"
        if sidecar_state == "ok":
            visible += 1
        else:
            drifted.append("gstack")
    if missing or drifted:
        findings.append(Finding("error", "external_gstack_runtime_drift", str(runtime_skills),
                                f"missing={missing} drifted={drifted}"))
    return visible, missing, drifted, sidecar_state, findings


def base_payload(root: Path, mode: str, status: str) -> dict[str, Any]:
    return {
        "schema_version": STATUS_SCHEMA,
        "root_selection": {"mode": mode},
        "external_gstack": {
            "root": str(root),
            "version": "",
            "expected_skill_count": 0,
            "visible_skill_count": 0,
            "missing": [],
            "drifted": [],
            "sidecar": "not_checked",
            "status": status,
        },
        "inventory": [],
        "exact_excludes": [],
        "topology": {},
        "findings": [],
    }


def inspect_status(
    repo_root: Path,
    codex_home: Path,
    cli_root: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    environment = environment or os.environ
    mode, root, explicit = select_root(cli_root, environment, codex_home)
    if not root.exists():
        payload = base_payload(root, mode, "invalid" if explicit else "legacy")
        if explicit:
            payload["findings"].append(
                Finding("error", "external_gstack_root_invalid", str(root), "explicit root is missing").as_json()
            )
            return payload
        try:
            footprints = reserved_runtime_footprints(repo_root, codex_home)
        except (OSError, UnicodeError, ValueError) as exc:
            payload["external_gstack"]["status"] = "invalid"
            payload["findings"].append(
                Finding("error", "external_gstack_repo_ownership_invalid", str(repo_root), str(exc)).as_json()
            )
            return payload
        if footprints:
            payload["external_gstack"]["status"] = "invalid"
            for path, raw in footprints:
                payload["findings"].append(
                    Finding("error", "external_gstack_default_missing_with_runtime_footprint", str(path),
                            f"reserved runtime symlink remains: {raw}").as_json()
                )
        return payload

    inventory, version, findings = validate_external_root(root)
    payload = base_payload(root, mode, "invalid" if findings else "active")
    payload["external_gstack"]["version"] = version
    payload["inventory"] = inventory
    payload["findings"] = [item.as_json() for item in findings]
    if findings:
        return payload
    visible, missing, drifted, sidecar, topology_findings = active_topology(root, codex_home, inventory)
    payload["external_gstack"].update(
        {
            "expected_skill_count": len(inventory),
            "visible_skill_count": visible,
            "missing": missing,
            "drifted": drifted,
            "sidecar": sidecar,
        }
    )
    flat = sorted(set(inventory) - {"gstack"})
    payload["exact_excludes"] = [f"/{name}/" for name in flat] + ["/gstack/"]
    payload["topology"] = {"flat_generated": flat, "sidecar_root": "gstack"}
    payload["findings"].extend(item.as_json() for item in topology_findings)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and manage external gstack runtime ownership.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--repo-root", required=True)
    status.add_argument("--codex-home", required=True)
    status.add_argument("--gstack-root")
    status.add_argument("--json", action="store_true")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--manifest", required=True)
    recover = subparsers.add_parser("recover")
    recover.add_argument("--operation-root", required=True)
    recover.add_argument("--rollback", action="store_true", required=True)
    return parser.parse_args()


def apply_command(manifest_path: Path) -> int:
    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        require_manifest(manifest_data)
        codex_home = lexical_absolute(Path(manifest_data["codex_home"]))
        validate_operation_paths(manifest_data)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return emit_error("manifest_invalid", str(exc))
    try:
        with locked_runtime(codex_home):
            try:
                codex_home, skills, operation_root, staging_root, backup_root = validate_operation_paths(manifest_data)
                repo_root = lexical_absolute(Path(manifest_data["repo_root"]))
                gstack_root = lexical_absolute(Path(manifest_data["gstack_root"]))
                inventory, version, root_findings = validate_external_root(gstack_root)
                if root_findings:
                    raise ValueError(root_findings[0].detail)
                code, head, err = run(["git", "-C", str(gstack_root), "rev-parse", "HEAD"])
                if code != 0 or head != manifest_data["external_head"] or version != manifest_data["external_version"]:
                    raise ValueError(err or "external identity drift")
                code, branch, err = run(["git", "-C", str(gstack_root), "branch", "--show-current"])
                if code != 0 or branch != "main":
                    raise ValueError(err or "external root must be on main")
                code, dirty, err = run(["git", "-C", str(gstack_root), "status", "--porcelain", "--untracked-files=all"])
                if code != 0 or dirty:
                    raise ValueError(err or "external root must be clean")
                expected_inventory = sorted(inventory)
                flat_generated = sorted(set(expected_inventory) - {"gstack"})
                if manifest_data["inventory"] != expected_inventory or manifest_data["flat_generated"] != flat_generated:
                    raise ValueError("manifest inventory does not match external root")
                if sorted(manifest_data["replace_real"] + manifest_data["existing_links"]) != flat_generated:
                    raise ValueError("manifest flat ownership partition mismatch")
                if tuple(tuple(item) for item in manifest_data["sidecar_pairs"]) != SIDECAR_PAIRS:
                    raise ValueError("manifest sidecar pairs mismatch")
                if tuple(manifest_data["sidecar_dirs"]) != SIDECAR_DIRS:
                    raise ValueError("manifest sidecar directories mismatch")
                current_context = capture_approval_context(repo_root, codex_home, gstack_root, flat_generated)
                if current_context != manifest_data["approval_context"]:
                    raise ValueError("approved source or runtime prestate drift")
                if sorted(current_context["replace_real_prestates"]) != sorted(manifest_data["replace_real"]):
                    raise ValueError("approved real-target prestates do not match replacement partition")
                incomplete = find_incomplete_operation(codex_home, operation_root)
                if incomplete is not None:
                    raise ValueError(f"incomplete external gstack operation requires recovery: {incomplete}")
                for name in manifest_data["existing_links"]:
                    target = skills / name
                    source = gstack_root / ".agents" / "skills" / name
                    if not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False):
                        raise ValueError(f"existing link drift: {name}")
                for name in manifest_data["replace_real"]:
                    target = skills / name
                    skill = target / "SKILL.md"
                    if not target.is_dir() or target.is_symlink() or not skill.is_file() \
                            or AUTO_GENERATED_BANNER not in skill.read_text(encoding="utf-8", errors="replace"):
                        raise ValueError(f"replacement target is not an owned generated directory: {name}")
                old_sidecar = skills / "gstack"
                if not old_sidecar.is_dir() or old_sidecar.is_symlink():
                    raise ValueError("old sidecar must be a real directory")

                runtime_backups = codex_home / "runtime-backups"
                runtime_backups.mkdir(parents=True, exist_ok=True, mode=0o700)
                operation_root.mkdir(mode=0o700)
                staging_root.mkdir(mode=0o700)
                backup_root.mkdir(mode=0o700)
                (staging_root / "flat").mkdir(mode=0o700)
                (backup_root / "flat").mkdir(mode=0o700)
                journal_path = operation_root / "operation.json"
                journal = {
                    "schema_version": manifest_data["schema_version"],
                    "state": "planned",
                    "codex_home": str(codex_home),
                    "manifest": manifest_data,
                    "manifest_sha256": hashlib.sha256(
                        json.dumps(
                            manifest_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                        ).encode("utf-8")
                    ).hexdigest(),
                    "targets": {name: "prestate" for name in manifest_data["replace_real"]},
                }
                durable_write_json(journal_path, journal)

                for name in manifest_data["replace_real"]:
                    os.symlink(gstack_root / ".agents" / "skills" / name, staging_root / "flat" / name)
                prepare_sidecar(gstack_root, staging_root / "gstack", manifest_data["sidecar_pairs"])
                set_journal_state(journal_path, journal, "staged")
                if capture_approval_context(repo_root, codex_home, gstack_root, flat_generated) != current_context:
                    raise ValueError("approved prestate drifted before cutover")
                set_journal_state(journal_path, journal, "cutting_over")

                for name in manifest_data["replace_real"]:
                    target = skills / name
                    target_backup = backup_root / "flat" / name
                    os.rename(target, target_backup)
                    fsync_dir(target.parent)
                    fsync_dir(target_backup.parent)
                    journal["targets"][name] = "old_moved"
                    durable_write_json(journal_path, journal)
                    if os.environ.get("MCE_EXTERNAL_GSTACK_TEST_FAULT") == f"after_old_moved:{name}":
                        os._exit(97)
                    os.rename(staging_root / "flat" / name, target)
                    fsync_dir(target.parent)
                    fsync_dir(staging_root / "flat")
                    journal["targets"][name] = "new_installed"
                    durable_write_json(journal_path, journal)
                    source = gstack_root / ".agents" / "skills" / name
                    if not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False):
                        raise RuntimeError(f"replacement verification failed: {name}")
                    journal["targets"][name] = "verified"
                    durable_write_json(journal_path, journal)

                sidecar_backup = backup_root / "gstack"
                os.rename(old_sidecar, sidecar_backup)
                fsync_dir(old_sidecar.parent)
                fsync_dir(sidecar_backup.parent)
                set_journal_state(journal_path, journal, "sidecar_old_moved")
                os.rename(staging_root / "gstack", old_sidecar)
                fsync_dir(old_sidecar.parent)
                fsync_dir(staging_root)
                set_journal_state(journal_path, journal, "sidecar_installed")
                verify_live_transaction(gstack_root, skills, manifest_data)
                post_context = capture_approval_context(repo_root, codex_home, gstack_root, flat_generated)
                for key in ("authority_sha256", "external_root_sha256", "non_target_sha256", "warning_tuples"):
                    if post_context[key] != current_context[key]:
                        raise RuntimeError(
                            f"post-cutover context drift: {key} expected={current_context[key]!r} "
                            f"actual={post_context[key]!r}"
                        )
                set_journal_state(journal_path, journal, "verified")
                if (staging_root / "flat").is_dir() and not any((staging_root / "flat").iterdir()):
                    (staging_root / "flat").rmdir()
                if staging_root.is_dir() and not any(staging_root.iterdir()):
                    staging_root.rmdir()
                set_journal_state(journal_path, journal, "complete")
                print(json.dumps({"status": "complete", "operation_root": str(operation_root)}, sort_keys=True))
                return 0
            except Exception as exc:
                return emit_error("apply_failed", str(exc))
    except LockContended:
        return emit_error("lock_contended", "another runtime mutation holds the shared lock", exit_code=75)


def recover_command(operation_root: Path) -> int:
    try:
        journal_path = operation_root / "operation.json"
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        codex_home, _, _ = validate_recovery_paths(operation_root, journal)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return emit_error("journal_invalid", str(exc))
    try:
        with locked_runtime(codex_home):
            try:
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
                manifest_data = journal["manifest"]
                _, skills, backup_root = validate_recovery_paths(operation_root, journal)
                repo_root = lexical_absolute(Path(manifest_data["repo_root"]))
                gstack_root = lexical_absolute(Path(manifest_data["gstack_root"]))
                flat_generated = manifest_data["flat_generated"]
                approval_context = manifest_data["approval_context"]
                if non_target_digest(skills, flat_generated) != approval_context["non_target_sha256"]:
                    raise ValueError("non-target runtime drift blocks recovery")
                if path_digest(gstack_root, {".git"}) != approval_context["external_root_sha256"]:
                    raise ValueError("external source drift blocks recovery")
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != approval_context["authority_sha256"]:
                    raise ValueError("runtime authority drift blocks recovery")
                if current_warning_tuples(repo_root, codex_home, gstack_root) != approval_context["warning_tuples"]:
                    raise ValueError("warning baseline drift blocks recovery")
                if journal.get("state") == "rolled_back":
                    if capture_approval_context(repo_root, codex_home, gstack_root, flat_generated) != approval_context:
                        raise ValueError("rolled_back journal does not match approved prestate")
                    print(json.dumps({"status": "rolled_back", "operation_root": str(operation_root)}, sort_keys=True))
                    return 0
                sidecar = skills / "gstack"
                sidecar_backup = backup_root / "gstack"
                sidecar_backup_required = journal["state"] in {
                    "sidecar_old_moved", "sidecar_installed", "verified", "complete", "rolling_back"
                }
                if sidecar_backup.exists():
                    if not sidecar_backup.is_dir() or sidecar_backup.is_symlink():
                        raise ValueError("sidecar backup is not a real directory")
                    if path_digest(sidecar_backup) != approval_context["sidecar_prestate_sha256"]:
                        raise ValueError("sidecar backup does not match approved prestate")
                    if sidecar.exists() or sidecar.is_symlink():
                        verify_transaction_sidecar(
                            gstack_root, sidecar, manifest_data["sidecar_pairs"], manifest_data["sidecar_dirs"]
                        )
                elif not sidecar.exists() or path_digest(sidecar) != approval_context["sidecar_prestate_sha256"] or (
                    sidecar_backup_required and journal["state"] != "rolling_back"
                ):
                    raise ValueError("missing sidecar prestate backup")
                for name in manifest_data["replace_real"]:
                    target = skills / name
                    source = gstack_root / ".agents" / "skills" / name
                    target_backup = backup_root / "flat" / name
                    target_state = journal.get("targets", {}).get(name)
                    if target_state not in {"prestate", "old_moved", "new_installed", "verified"}:
                        raise ValueError(f"unknown journal target state: {name}")
                    if target_backup.exists():
                        if not target_backup.is_dir() or target_backup.is_symlink():
                            raise ValueError(f"flat backup is not a real directory: {name}")
                        if path_digest(target_backup) != approval_context["replace_real_prestates"][name]:
                            raise ValueError(f"flat backup does not match approved prestate: {name}")
                        if (target.exists() or target.is_symlink()) and (
                            not target.is_symlink() or target.resolve(strict=False) != source.resolve(strict=False)
                        ):
                            raise ValueError(f"unexpected live flat target blocks recovery: {name}")
                    elif (
                        target_state != "prestate" and journal["state"] != "rolling_back"
                    ) or (
                        not target.is_dir() or target.is_symlink()
                        or path_digest(target) != approval_context["replace_real_prestates"][name]
                    ):
                        raise ValueError(f"missing flat prestate backup: {name}")
                set_journal_state(journal_path, journal, "rolling_back")
                if sidecar_backup.exists():
                    if sidecar.exists() or sidecar.is_symlink():
                        remove_new_sidecar(sidecar, manifest_data["sidecar_pairs"])
                    if not sidecar.exists() and not sidecar.is_symlink():
                        os.rename(sidecar_backup, sidecar)
                        fsync_dir(sidecar.parent)
                        fsync_dir(sidecar_backup.parent)
                        if os.environ.get("MCE_EXTERNAL_GSTACK_TEST_FAULT") == "after_sidecar_restored":
                            os._exit(98)
                for name in reversed(manifest_data["replace_real"]):
                    target = skills / name
                    source = lexical_absolute(Path(manifest_data["gstack_root"])) / ".agents" / "skills" / name
                    target_backup = backup_root / "flat" / name
                    if target.is_symlink() and target.resolve(strict=False) == source.resolve(strict=False):
                        target.unlink()
                        fsync_dir(target.parent)
                    if target_backup.exists() and not target.exists() and not target.is_symlink():
                        os.rename(target_backup, target)
                        fsync_dir(target.parent)
                        fsync_dir(target_backup.parent)
                        if os.environ.get("MCE_EXTERNAL_GSTACK_TEST_FAULT") == f"after_flat_restored:{name}":
                            os._exit(98)
                if capture_approval_context(repo_root, codex_home, gstack_root, flat_generated) != approval_context:
                    raise RuntimeError("rollback prestate verification failed")
                set_journal_state(journal_path, journal, "rolled_back")
                print(json.dumps({"status": "rolled_back", "operation_root": str(operation_root)}, sort_keys=True))
                return 0
            except Exception as exc:
                return emit_error("recovery_blocked", str(exc))
    except LockContended:
        return emit_error("lock_contended", "another runtime mutation holds the shared lock", exit_code=75)


def main() -> int:
    args = parse_args()
    if args.command == "status":
        payload = inspect_status(
            lexical_absolute(Path(args.repo_root)),
            lexical_absolute(Path(args.codex_home)),
            args.gstack_root,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if any(item.get("severity") == "error" for item in payload["findings"]) else 0
    if args.command == "apply":
        return apply_command(lexical_absolute(Path(args.manifest)))
    if args.command == "recover":
        return recover_command(lexical_absolute(Path(args.operation_root)))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
