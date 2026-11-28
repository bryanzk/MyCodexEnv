#!/usr/bin/env python3
"""Read and maintain the DHF host conformance table (docs/dhf-conformance.json).

The table has one cell per DHF function and host. A cell may claim
`enforced_verified` only when its probes have passing receipts, and a receipt
counts for the host version it was taken on. Subcommands:

  check            validate the table (used by tests and CI)
  doctor           show every function on one host, with evidence age
  probes           print the probes for one host
  require-receipt  fail unless the given host version has host probe receipts
  probe-installed  run the installed Guard, healthy and faulted, in a temporary home
  record           append a probe receipt

Only `record` and `probe-installed --record` write, and only to the table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TABLE = Path("docs/dhf-conformance.json")
FUNCTIONS = ["position", "restrict", "observe", "thread", "empower", "contain", "transact"]
PROBE_KINDS = {"host", "installed_artifact", "transaction"}
CORE_END_MARKER = "# --- END DHF GUARD CORE ---\n"
INSTALLED_PROBE = "restrict.installed-guard-fault"


def load(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / TABLE).read_text(encoding="utf-8"))


def dump(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def latest_receipt(data: dict[str, Any], host: str, probe_id: str, host_version: str | None = None) -> dict[str, Any] | None:
    """The newest receipt for one probe, pass or fail, optionally on one host version.

    Only the newest result counts: a later failure withdraws an earlier pass
    until the probe passes again.
    """
    found = [
        receipt
        for receipt in data.get("receipts", [])
        if receipt.get("host") == host
        and receipt.get("probe") == probe_id
        and (host_version is None or receipt.get("host_version") == host_version)
    ]
    floor = datetime.min.replace(tzinfo=timezone.utc)
    return max(found, key=lambda receipt: parse_time(receipt.get("timestamp")) or floor) if found else None


def validate(data: dict[str, Any], *, raw_text: str | None = None) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("functions") != FUNCTIONS:
        errors.append(f"functions must be exactly {FUNCTIONS}")
    statuses = data.get("statuses")
    hosts = data.get("hosts")
    if not isinstance(statuses, dict) or not isinstance(hosts, dict) or not hosts:
        return errors + ["statuses and hosts must be non-empty objects"]
    if not isinstance(data.get("freshness_days"), int) or data["freshness_days"] <= 0:
        errors.append("freshness_days must be a positive integer")
    probes: dict[str, dict[str, Any]] = {}
    for probe in data.get("probes", []):
        probe_id = probe.get("id")
        if not isinstance(probe_id, str) or probe_id in probes:
            errors.append(f"probe id missing or duplicated: {probe_id!r}")
            continue
        probes[probe_id] = probe
        if probe.get("function") not in FUNCTIONS or probe.get("host") not in hosts or probe.get("kind") not in PROBE_KINDS:
            errors.append(f"probe {probe_id}: function, host, or kind is not recognized")
        for field in ("prompt", "expected", "criterion", "side_effects"):
            if not isinstance(probe.get(field), str) or not probe[field].strip():
                errors.append(f"probe {probe_id}: {field} is required")
    for index, receipt in enumerate(data.get("receipts", [])):
        probe = probes.get(receipt.get("probe"))
        label = f"receipt {index} ({receipt.get('probe')})"
        if probe is None:
            errors.append(f"{label}: unknown probe")
        elif receipt.get("host") != probe.get("host"):
            errors.append(f"{label}: host does not match the probe's host")
        if receipt.get("result") not in {"pass", "fail"}:
            errors.append(f"{label}: result must be pass or fail")
        if parse_time(receipt.get("timestamp")) is None:
            errors.append(f"{label}: timestamp must be ISO 8601 with a UTC offset")
        for field in ("host_version", "machine", "key_output"):
            if not isinstance(receipt.get(field), str) or not receipt[field].strip():
                errors.append(f"{label}: {field} is required")
    cells = data.get("cells", {})
    if sorted(cells) != sorted(hosts):
        errors.append("cells must have exactly one entry per host")
    for host, row in cells.items():
        if sorted(row) != sorted(FUNCTIONS):
            errors.append(f"cells.{host} must have exactly the seven functions")
            continue
        for function, cell in row.items():
            where = f"cells.{host}.{function}"
            if cell.get("status") not in statuses:
                errors.append(f"{where}: unknown status {cell.get('status')!r}")
            listed = cell.get("probes", [])
            for probe_id in listed:
                probe = probes.get(probe_id)
                if probe is None or probe.get("function") != function or probe.get("host") != host:
                    errors.append(f"{where}: probe {probe_id} is unknown or belongs to another cell")
            if cell.get("status") == "enforced_verified":
                if not listed:
                    errors.append(f"{where}: enforced_verified needs at least one probe")
                for probe_id in listed:
                    newest = latest_receipt(data, host, probe_id)
                    if newest is None:
                        errors.append(f"{where}: enforced_verified but probe {probe_id} has no passing receipt")
                    elif newest.get("result") != "pass":
                        errors.append(f"{where}: enforced_verified but the latest receipt of probe {probe_id} failed")
    if raw_text is not None and raw_text != dump(data):
        errors.append("file is not in canonical form; rewrite it with json.dumps(indent=2, ensure_ascii=False)")
    return errors


def cell_view(data: dict[str, Any], host: str, function: str, host_version: str | None, now: datetime) -> dict[str, Any]:
    """One function on one host. Evidence is current only when every listed probe's evidence is current.

    A receipt goes stale with age for every probe, and with a host version
    change for host probes only: an installed-artifact or transaction probe
    does not run inside the host.
    """
    cell = data["cells"][host][function]
    kinds = {probe["id"]: probe.get("kind") for probe in data.get("probes", [])}
    view = {
        "function": function,
        "status": cell["status"],
        "mechanism": cell.get("mechanism", ""),
        "note": cell.get("note", ""),
        "probes": cell.get("probes", []),
        "evidence_version": None,
        "evidence_at": None,
        "evidence_machine": None,
        "evidence": "none",
    }
    latest = {probe_id: latest_receipt(data, host, probe_id) for probe_id in view["probes"]}
    found = [receipt for receipt in latest.values() if receipt is not None]
    if not found:
        return view
    problems = []
    for probe_id, receipt in latest.items():
        if receipt is None:
            problems.append(f"{probe_id} has no receipt")
        elif receipt.get("result") != "pass":
            problems.append(f"{probe_id} failed at {receipt['timestamp']}")
        elif kinds.get(probe_id) == "host" and host_version is not None and receipt["host_version"] != host_version:
            problems.append(f"{probe_id} probed on {receipt['host_version']}, host is {host_version}")
        elif now - (parse_time(receipt["timestamp"]) or now) > timedelta(days=data["freshness_days"]):
            problems.append(f"{probe_id} older than {data['freshness_days']} days")
    # Report the weakest link: the oldest of the per-probe latest receipts.
    oldest = min(found, key=lambda receipt: parse_time(receipt["timestamp"]) or now)
    view.update(evidence_version=oldest["host_version"], evidence_at=oldest["timestamp"], evidence_machine=oldest["machine"])
    if any(" failed at " in problem for problem in problems):
        view["evidence"] = "failed: " + "; ".join(problems)
    elif problems:
        view["evidence"] = "stale: " + "; ".join(problems)
    elif host_version is None:
        view["evidence"] = "unconfirmed: current host version unknown"
    else:
        view["evidence"] = "current"
    return view


def missing_host_receipts(data: dict[str, Any], host: str, host_version: str) -> list[str]:
    """Host probes of enforced_verified cells whose latest receipt on this host version is not a pass."""
    kinds = {probe["id"]: probe.get("kind") for probe in data.get("probes", [])}
    missing = []
    for function in FUNCTIONS:
        cell = data["cells"][host][function]
        if cell.get("status") != "enforced_verified":
            continue
        absent = [
            probe_id
            for probe_id in cell.get("probes", [])
            if kinds.get(probe_id) == "host"
            and (latest_receipt(data, host, probe_id, host_version) or {}).get("result") != "pass"
        ]
        if absent:
            missing.append(f"{function} (run: {', '.join(absent)})")
    return missing


def guard_owner_disabled(host: str, codex_home: Path | None) -> bool | None:
    """Whether the owner turned the Guard hook off in this host's config.toml.

    Hook on/off belongs to the owner (SHI-631); DHF reports it and never turns a
    hook back on. Returns None when the config cannot be read.
    """
    if host != "codex-cli":
        return None
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    from hook_registration import disabled_managed_commands

    home = codex_home or Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    try:
        text = (home / "config.toml").read_text(encoding="utf-8")
    except OSError:
        return None
    return any("/harness_guard.py" in command for command in disabled_managed_commands(text))


def unrecognized_calls(host: str, codex_home: Path | None) -> dict[str, Any] | None:
    """Write-class calls the Guard could not classify on this host, read from its receipt.

    They are recorded, not blocked, so the count has to be looked at. Returns
    None when the host has no Guard receipt to read.
    """
    if host != "codex-cli":
        return None
    home = codex_home or Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    receipt_path = home / "harness" / "guard-receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"receipt": str(receipt_path), "count": None, "last": None}
    count = receipt.get("unrecognized_mutations") if isinstance(receipt, dict) else None
    last = receipt.get("last_unrecognized") if isinstance(receipt, dict) else None
    return {
        "receipt": str(receipt_path),
        "count": count if isinstance(count, int) and not isinstance(count, bool) else None,
        "last": {key: last.get(key) for key in ("at", "tool_name")} if isinstance(last, dict) else None,
    }


def detect_host_version(host: str, root: Path = ROOT) -> str | None:
    if host != "codex-cli":
        return None
    try:
        resolver = subprocess.run([str(root / "codex" / "runtime" / "resolve_codex_cli.sh")], capture_output=True, text=True, check=False, timeout=20)
        binary = resolver.stdout.strip() if resolver.returncode == 0 and resolver.stdout.strip() else "codex"
        version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=False, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    parts = version.stdout.split()
    return parts[1] if version.returncode == 0 and len(parts) >= 2 else None


def run_guard(interpreter: str, guard: Path, payload: dict[str, Any], env: dict[str, str]) -> str:
    done = subprocess.run([interpreter, str(guard)], input=json.dumps(payload), capture_output=True, text=True, check=False, env=env, timeout=30)
    try:
        result = json.loads(done.stdout)
    except ValueError:
        return f"error(exit={done.returncode})"
    if done.returncode != 0 or not isinstance(result, dict):
        return f"error(exit={done.returncode})"
    if result.get("decision") != "block":
        return "allow"
    reason = str(result.get("reason", ""))
    return "guard_fault" if reason.endswith("guard_fault") else "block"


def probe_installed(codex_home: Path, interpreter: str) -> dict[str, Any]:
    installed = codex_home / "hooks" / "harness_guard.py"
    source = installed.read_text(encoding="utf-8")
    outcome: dict[str, Any] = {
        "guard_sha256": hashlib.sha256(installed.read_bytes()).hexdigest(),
        "matches_source": installed.read_bytes() == (ROOT / "codex" / "hooks" / "harness_guard.py").read_bytes(),
        "interpreter": interpreter,
    }
    if source.count(CORE_END_MARKER) != 1:
        outcome["summary"] = "unsupported: the installed Guard predates the guard_fault rule"
        outcome["passed"] = False
        return outcome
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        home = tmp_path / ".codex"
        (home / "hooks").mkdir(parents=True)
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        healthy = tmp_path / "healthy-harness_guard.py"
        healthy.write_text(source, encoding="utf-8")
        faulted = tmp_path / "faulted-harness_guard.py"
        faulted.write_text(source.replace(CORE_END_MARKER, CORE_END_MARKER + "raise RuntimeError('dhf conformance probe fault')\n"), encoding="utf-8")
        # The Guard honors CODEX_HARNESS_EVIDENCE_DIR for block records; pin it
        # inside the temporary directory so the probe cannot write to a real one.
        env = dict(os.environ, CODEX_HOME=str(home), CODEX_HARNESS_EVIDENCE_DIR=str(tmp_path / "evidence"))
        env.pop("CODEX_SESSION_ID", None)
        patch = "\n".join(["*** Begin Patch", f"*** Add File: {home / 'hooks' / 'probe.txt'}", "+probe", "*** End Patch"])
        outcome["healthy"] = run_guard(interpreter, healthy, {"tool_name": "apply_patch", "cwd": str(workspace), "tool_input": {"patch": patch}}, env)
        outcome["fault_write"] = run_guard(interpreter, faulted, {"tool_name": "write", "cwd": str(workspace), "tool_input": {"path": str(workspace / "a.txt"), "content": "x"}}, env)
        outcome["fault_read"] = run_guard(interpreter, faulted, {"tool_name": "read", "cwd": str(workspace), "tool_input": {"path": str(workspace / "a.txt")}}, env)
    outcome["summary"] = f"healthy={outcome['healthy']} fault_write={outcome['fault_write']} fault_read={outcome['fault_read']}"
    outcome["passed"] = (outcome["healthy"], outcome["fault_write"], outcome["fault_read"]) == ("block", "guard_fault", "allow")
    return outcome


def append_receipt(root: Path, receipt: dict[str, Any]) -> list[str]:
    """Append one receipt. A failing receipt for an enforced_verified cell demotes that cell.

    The failure is evidence and must be kept; the cell can no longer claim
    enforcement, so its status becomes registered_unverified until the owner
    restores it after a passing rerun.
    """
    data = load(root)
    data.setdefault("receipts", []).append(receipt)
    if receipt.get("result") == "fail":
        for row in data.get("cells", {}).get(receipt.get("host"), {}).values():
            if row.get("status") == "enforced_verified" and receipt.get("probe") in row.get("probes", []):
                row["status"] = "registered_unverified"
                row["note"] = (row.get("note", "") + f" Demoted on {receipt.get('timestamp')}: probe {receipt.get('probe')} failed.").strip()
    errors = validate(data)
    if not errors:
        (root / TABLE).write_text(dump(data), encoding="utf-8")
    return errors


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DHF host conformance table: check, doctor, probes, receipts.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    for name in ("doctor", "probes", "require-receipt"):
        sub = commands.add_parser(name)
        sub.add_argument("--host", default="codex-cli")
        if name != "probes":
            sub.add_argument("--host-version")
        if name == "doctor":
            sub.add_argument("--json", action="store_true")
            sub.add_argument("--codex-home", type=Path, help="Codex home whose Guard receipt to read (default: $CODEX_HOME or ~/.codex)")
    installed = commands.add_parser("probe-installed")
    installed.add_argument("--codex-home", type=Path, required=True)
    installed.add_argument("--interpreter", default="/usr/bin/python3")
    installed.add_argument("--record", action="store_true")
    installed.add_argument("--host-version")
    installed.add_argument("--machine", default=socket.gethostname())
    record = commands.add_parser("record")
    record.add_argument("--probe", required=True)
    record.add_argument("--result", choices=["pass", "fail"], required=True)
    record.add_argument("--key-output", required=True)
    record.add_argument("--host-version")
    record.add_argument("--machine", default=socket.gethostname())
    record.add_argument("--timestamp")
    record.add_argument("--guard-sha256")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()

    try:
        raw_text = (root / TABLE).read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, ValueError) as error:
        print(f"ERROR: cannot read {TABLE}: {error}", file=sys.stderr)
        return 2
    errors = validate(data, raw_text=raw_text)
    if args.command == "check" or errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if not errors:
            print("conformance table consistent")
        return 1 if errors else 0

    if args.command == "probes":
        for probe in data["probes"]:
            if probe["host"] == args.host:
                print(f"## {probe['id']} ({probe['function']}, {probe['kind']})\n")
                print(f"Prompt or command:\n{probe['prompt']}\n")
                print(f"Expected: {probe['expected']}\nCriterion: {probe['criterion']}\nSide effects: {probe['side_effects']}\n")
        return 0

    if args.command == "record" or args.command == "probe-installed":
        probes = {probe["id"]: probe for probe in data["probes"]}
        probe_id = INSTALLED_PROBE if args.command == "probe-installed" else args.probe
        if probe_id not in probes:
            print(f"ERROR: unknown probe {probe_id}", file=sys.stderr)
            return 2
        host = probes[probe_id]["host"]
        if args.command == "probe-installed":
            try:
                outcome = probe_installed(args.codex_home.expanduser(), args.interpreter)
            except (OSError, subprocess.SubprocessError) as error:
                print(f"ERROR: installed Guard probe could not run: {error}", file=sys.stderr)
                return 2
            print(outcome["summary"])
            print(f"guard_sha256={outcome['guard_sha256']} matches_source={outcome['matches_source']} interpreter={outcome['interpreter']}")
            if not args.record:
                return 0 if outcome["passed"] else 1
            result, key_output, guard_sha = ("pass" if outcome["passed"] else "fail"), outcome["summary"], outcome["guard_sha256"][:8]
            timestamp = now_iso()
        else:
            result, key_output, guard_sha, timestamp = args.result, args.key_output, args.guard_sha256, args.timestamp or now_iso()
        host_version = args.host_version or detect_host_version(host, root)
        if host_version is None:
            print(f"ERROR: cannot detect the {host} version; pass --host-version", file=sys.stderr)
            return 2
        receipt = {"probe": probe_id, "host": host, "host_version": host_version, "machine": args.machine, "result": result, "key_output": key_output, "timestamp": timestamp}
        if guard_sha:
            receipt["guard_sha256"] = guard_sha
        errors = append_receipt(root, receipt)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if errors:
            return 1
        print(f"recorded {probe_id}: {result} on {host} {host_version} at {timestamp}")
        return 0 if result == "pass" else 1

    if args.host not in data["hosts"]:
        print(f"ERROR: unknown host {args.host}; known: {', '.join(sorted(data['hosts']))}", file=sys.stderr)
        return 2
    host_version = args.host_version or detect_host_version(args.host, root)

    if args.command == "require-receipt":
        if host_version is None:
            print(f"ERROR: cannot detect the {args.host} version; pass --host-version", file=sys.stderr)
            return 2
        missing = missing_host_receipts(data, args.host, host_version)
        for item in missing:
            print(f"missing host probe receipt for {args.host} {host_version}: {item}", file=sys.stderr)
        if not missing:
            print(f"host probe receipts present for {args.host} {host_version}")
        return 1 if missing else 0

    views = [cell_view(data, args.host, function, host_version, datetime.now(timezone.utc)) for function in FUNCTIONS]
    unrecognized = unrecognized_calls(args.host, args.codex_home.expanduser() if args.codex_home else None)
    guard_disabled = guard_owner_disabled(args.host, args.codex_home.expanduser() if args.codex_home else None)
    for view in views:
        if view["function"] == "restrict":
            view["unrecognized_calls"] = unrecognized
            view["guard_disabled_by_owner"] = guard_disabled
    if args.json:
        print(json.dumps({"host": args.host, "host_version": host_version, "functions": views}, ensure_ascii=False, indent=2))
        return 0
    print(f"# DHF conformance: {data['hosts'][args.host]['label']}\n")
    print(f"- host_version: `{host_version or 'unknown'}`")
    print(f"- table: `{TABLE}`; spec: `{data['spec']}`\n")
    for view in views:
        print(f"## {view['function']}: {view['status']}")
        print(f"- meaning: {data['statuses'][view['status']]}")
        if view["mechanism"]:
            print(f"- mechanism: {view['mechanism']}")
        if view["evidence_at"]:
            print(f"- oldest of the latest probe receipts: {view['evidence_at']} on {view['evidence_version']} ({view['evidence_machine']})")
        print(f"- evidence: {view['evidence']}")
        if view["probes"]:
            print(f"- probes: {', '.join(view['probes'])}")
        if view.get("guard_disabled_by_owner"):
            print("- WARNING: the owner turned the Guard hook off in config.toml; structured writes are not "
                  "mechanically blocked on this host. Turn it back on in Codex with /hooks.")
        calls = view.get("unrecognized_calls")
        if calls is not None and calls["count"] is None:
            print(f"- unrecognized calls: unknown (no readable Guard receipt at {calls['receipt']})")
        elif calls is not None and calls["count"] > 0:
            last = calls["last"] or {}
            print(f"- unrecognized calls: {calls['count']} (last: {last.get('tool_name')} at {last.get('at')}). "
                  "These write-class calls were recorded, not blocked: find out which tool it was and teach the adapter.")
        elif calls is not None:
            print("- unrecognized calls: 0")
        if view["note"]:
            print(f"- note: {view['note']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
