#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from harness_evidence import append_event, infer_evidence_kind
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from harness_evidence import append_event, infer_evidence_kind


ARCHITECTURE_KEYS = (
    "new_services",
    "new_trust_roots",
    "new_identity_systems",
    "new_state_machines",
    "new_states",
    "new_operational_roles",
    "new_external_dependencies",
    "repeated_finding_category_count",
)
EVIDENCE_LEVELS = {
    "observed", "reproduced", "provider_or_standard_documented",
    "reasoned_current_scope_counterexample", "speculative",
}
DISPOSITIONS = {
    "MITIGATE_IN_V1",
    "MANUAL_CONTROL",
    "ACCEPTED_RISK",
    "DEFERRED",
    "UNSUPPORTED",
    "NEEDS_EVIDENCE",
    "SCOPE_DECISION_REQUIRED",
    "SCOPE_REBASE_REQUIRED",
}
TERMINAL_DISPOSITIONS = {"MITIGATE_IN_V1", "MANUAL_CONTROL", "ACCEPTED_RISK", "DEFERRED", "UNSUPPORTED"}
SCOPE_REQUIRED = {
    "schema_version",
    "scope_id",
    "scope_version",
    "session_binding",
    "repo_anchor",
    "mode",
    "product_stage",
    "supported_scenarios",
    "non_goals",
    "manual_controls",
    "risk_policy",
    "complexity_budget",
    "allowed_claims",
    "confirmation_source",
    "confirmation_message_sha256",
    "created_at",
}
FINDING_REQUIRED = {
    "finding_id",
    "category",
    "claim",
    "in_scope",
    "evidence_level",
    "affected_asset",
    "required_preconditions",
    "likelihood",
    "impact",
    "irreversibility",
    "manual_control_available",
    "manual_control_adequate",
    "complexity_delta",
    "disposition",
    "rationale",
    "owner",
    "future_trigger",
    "status",
}
RECEIPT_REQUIRED = {
    "schema_version",
    "session_binding",
    "repo_anchor_hash",
    "scope_hash",
    "plan_hash",
    "finding_set_hash",
    "architecture_delta_hash",
    "review_round",
    "decision",
    "operation_key",
    "timestamp",
    "expires_at",
}


class GovernorError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_value(value: Any) -> str:
    return sha256_text(canonical_json(value))


def session_binding(session_id: str) -> str:
    if not session_id:
        raise GovernorError("session_id is required")
    return sha256_text(f"plan-governor:{session_id}")


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GovernorError(f"invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def iso_time(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def require_exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing:
        raise GovernorError(f"{label} missing required fields: {', '.join(missing)}")
    if extra:
        raise GovernorError(f"{label} has undeclared fields: {', '.join(extra)}")


def validate_hash(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise GovernorError(f"{label} must be a lowercase SHA-256")


def validate_architecture(value: Any, label: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise GovernorError(f"{label} must be an object")
    require_exact_keys(value, set(ARCHITECTURE_KEYS), label)
    for key in ARCHITECTURE_KEYS:
        if isinstance(value[key], bool) or not isinstance(value[key], int) or value[key] < 0:
            raise GovernorError(f"{label}.{key} must be a non-negative integer")
    return value


def validate_scope(value: Any, expected_binding: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GovernorError("scope envelope must be an object")
    require_exact_keys(value, SCOPE_REQUIRED, "scope envelope")
    if value["schema_version"] != 1:
        raise GovernorError("scope envelope schema_version must be 1")
    if value["session_binding"] != expected_binding:
        raise GovernorError("scope envelope session_binding does not match the trusted session")
    validate_hash(value["session_binding"], "scope envelope session_binding")
    validate_hash(value["confirmation_message_sha256"], "confirmation_message_sha256")
    if not isinstance(value["scope_version"], int) or isinstance(value["scope_version"], bool) or value["scope_version"] < 1:
        raise GovernorError("scope_version must be a positive integer")
    if value["confirmation_source"] != "user_message":
        raise GovernorError("confirmation_source must be user_message")
    if value["mode"] not in {"plan", "review", "implementation", "report-only", "handoff"}:
        raise GovernorError("scope envelope mode is invalid")
    for key in ("scope_id", "repo_anchor", "product_stage"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise GovernorError(f"scope envelope {key} must be non-empty")
    for key in ("supported_scenarios", "non_goals", "manual_controls", "allowed_claims"):
        if not isinstance(value[key], list) or not all(isinstance(item, str) and item.strip() for item in value[key]):
            raise GovernorError(f"scope envelope {key} must be a string array")
    if not value["supported_scenarios"]:
        raise GovernorError("scope envelope supported_scenarios must not be empty")
    if not isinstance(value["risk_policy"], dict):
        raise GovernorError("scope envelope risk_policy must be an object")
    validate_architecture(value["complexity_budget"], "complexity_budget")
    parse_time(value["created_at"])
    return value


def validate_finding(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GovernorError("finding must be an object")
    require_exact_keys(value, FINDING_REQUIRED, "finding")
    if value["evidence_level"] not in EVIDENCE_LEVELS:
        raise GovernorError("finding evidence_level is invalid")
    if value["disposition"] not in DISPOSITIONS:
        raise GovernorError("finding disposition is invalid")
    if value["likelihood"] not in {"low", "medium", "high", "unknown"}:
        raise GovernorError("finding likelihood is invalid")
    if value["impact"] not in {"low", "medium", "high", "catastrophic"}:
        raise GovernorError("finding impact is invalid")
    if value["status"] not in {"terminal", "non_terminal"}:
        raise GovernorError("finding status is invalid")
    for key in ("in_scope", "irreversibility", "manual_control_available", "manual_control_adequate"):
        if not isinstance(value[key], bool):
            raise GovernorError(f"finding {key} must be boolean")
    for key in ("finding_id", "category", "claim", "affected_asset"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise GovernorError(f"finding {key} must be non-empty")
    if not isinstance(value["required_preconditions"], list) or not all(
        isinstance(item, str) and item.strip() for item in value["required_preconditions"]
    ):
        raise GovernorError("finding required_preconditions must be a string array")
    for key in ("rationale", "owner", "future_trigger"):
        if not isinstance(value[key], str):
            raise GovernorError(f"finding {key} must be a string")
    validate_architecture(value["complexity_delta"], "complexity_delta")
    return value


def budget_breached(delta: dict[str, int], budget: dict[str, int]) -> bool:
    return any(delta[key] > budget[key] for key in ARCHITECTURE_KEYS)


def evaluate_finding(finding: dict[str, Any], budget: dict[str, int]) -> dict[str, Any]:
    finding = validate_finding(finding)
    validate_architecture(budget, "complexity_budget")
    reasons: list[str] = []
    declared = finding["disposition"]
    if not finding["in_scope"]:
        disposition = declared if declared in {"DEFERRED", "UNSUPPORTED"} else "DEFERRED"
        reasons.append("outside_frozen_scope")
    elif finding["manual_control_adequate"] and not finding["manual_control_available"]:
        disposition = "NEEDS_EVIDENCE"
        reasons.append("manual_control_contradiction")
    elif finding["evidence_level"] == "speculative" or not finding["required_preconditions"]:
        disposition = "NEEDS_EVIDENCE"
        reasons.append("evidence_or_preconditions_missing")
    elif (
        finding["manual_control_available"]
        and finding["manual_control_adequate"]
        and not (finding["impact"] == "catastrophic" and finding["irreversibility"])
    ):
        disposition = "MANUAL_CONTROL"
        reasons.append("adequate_manual_control")
    elif finding["likelihood"] == "high" and finding["impact"] in {"high", "catastrophic"}:
        disposition = "MITIGATE_IN_V1"
        reasons.append("credible_high_likelihood_high_impact")
    elif finding["impact"] == "catastrophic" and finding["irreversibility"]:
        disposition = "MITIGATE_IN_V1"
        reasons.append("credible_catastrophic_irreversible")
    else:
        disposition = declared if declared in {"ACCEPTED_RISK", "DEFERRED"} else "ACCEPTED_RISK"
        reasons.append("accepted_or_deferred")

    if budget_breached(finding["complexity_delta"], budget):
        disposition = "SCOPE_REBASE_REQUIRED"
        reasons.append("complexity_budget_breach")

    terminal = disposition in TERMINAL_DISPOSITIONS
    if terminal and not all(finding[key].strip() for key in ("owner", "rationale", "future_trigger")):
        disposition = "SCOPE_DECISION_REQUIRED"
        terminal = False
        reasons.append("terminal_metadata_incomplete")
    return {
        "finding_id_hash": sha256_text(finding["finding_id"]),
        "category_hash": sha256_text(finding["category"]),
        "disposition": disposition,
        "status": "terminal" if terminal else "non_terminal",
        "reason_codes": reasons,
    }


def aggregate_delta(findings: list[dict[str, Any]]) -> dict[str, int]:
    return {key: sum(item["complexity_delta"][key] for item in findings) for key in ARCHITECTURE_KEYS}


def codex_home(value: str | None) -> Path:
    return Path(value or os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser()


def state_path(home: Path, binding: str) -> Path:
    return home / "harness" / "plan-governor" / binding / "state.json"


def atomic_json(path: Path, value: Any, *, private_parent: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if private_parent:
        os.chmod(path.parent, 0o700)
    fd, temp_name = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GovernorError(f"missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GovernorError(f"malformed {label}: {path}: {exc.msg}") from exc
    except OSError as exc:
        raise GovernorError(f"cannot read {label}: {path}: {exc}") from exc


def load_state(home: Path, binding: str) -> dict[str, Any]:
    value = read_json(state_path(home, binding), "governor state")
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("session_binding") != binding:
        raise GovernorError("malformed governor state")
    return value


def state_status(home: Path, binding: str, now: datetime) -> dict[str, Any]:
    path = state_path(home, binding)
    try:
        state = load_state(home, binding)
        if parse_time(state["expires_at"]) <= now:
            return {"status": "SCOPE_DECISION_REQUIRED", "reason": "expired_state", "state_path": str(path)}
        return {
            "status": state["status"],
            "scope_version": state["scope_version"],
            "review_round": state.get("review_round", 0),
            "budget_breach_without_rebase": state.get("budget_breach_without_rebase", False),
            "state_path": str(path),
        }
    except GovernorError as exc:
        reason = "missing_state" if not path.exists() else "malformed_state"
        return {"status": "SCOPE_DECISION_REQUIRED", "reason": reason, "message": str(exc), "state_path": str(path)}


def append_guardrail(home: Path, action: str, status: str, metadata: dict[str, Any], now: datetime) -> None:
    evidence_dir = home / "harness" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(evidence_dir, 0o700)
    event = {
        "schema_version": 1,
        "timestamp": iso_time(now),
        "event_type": "guardrail_decision",
        "cwd": os.getcwd(),
        "phase": "development",
        "evidence_kind": "decision",
        "approval_state": "not_required",
        "failure_class": "none",
        "message": f"plan_governor:{action}:{status}",
        "metadata": metadata,
    }
    event["evidence_kind"] = infer_evidence_kind(event)
    target = append_event(home, event)
    os.chmod(target, 0o600)


def receipt_operation_key(receipt: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in receipt.items() if key != "operation_key"}
    return sha256_text("plan-governor-receipt:" + canonical_json(unsigned))


def seal_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(receipt)
    sealed["operation_key"] = receipt_operation_key(sealed)
    return sealed


def build_receipt(
    state: dict[str, Any],
    finding_set_hash: str,
    architecture_delta_hash: str,
    decision: str,
    now: datetime,
) -> dict[str, Any]:
    receipt = {
        "schema_version": 1,
        "session_binding": state["session_binding"],
        "repo_anchor_hash": state["repo_anchor_hash"],
        "scope_hash": state["scope_hash"],
        "plan_hash": state["plan_hash"],
        "finding_set_hash": finding_set_hash,
        "architecture_delta_hash": architecture_delta_hash,
        "review_round": state["review_round"],
        "decision": decision,
        "timestamp": iso_time(now),
        "expires_at": iso_time(now + timedelta(minutes=10)),
    }
    return seal_receipt(receipt)


def receipt_shape_valid(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_REQUIRED:
        return False
    if receipt.get("schema_version") != 1 or receipt.get("decision") not in {
        "ADMITTED",
        "REBASE_REQUIRED",
        "SCOPE_DECISION_REQUIRED",
    }:
        return False
    if not isinstance(receipt.get("review_round"), int) or isinstance(receipt.get("review_round"), bool):
        return False
    try:
        for key in (
            "session_binding",
            "repo_anchor_hash",
            "scope_hash",
            "plan_hash",
            "finding_set_hash",
            "architecture_delta_hash",
            "operation_key",
        ):
            validate_hash(receipt.get(key), key)
        parse_time(receipt.get("timestamp"))
        parse_time(receipt.get("expires_at"))
    except GovernorError:
        return False
    return True


def classify_receipt(receipt: Any, state: dict[str, Any], now: datetime) -> str:
    if receipt is None:
        return "missing"
    if isinstance(receipt, str):
        try:
            receipt = json.loads(receipt)
        except json.JSONDecodeError:
            return "malformed"
    if not receipt_shape_valid(receipt):
        return "malformed"
    if receipt_operation_key(receipt) != receipt["operation_key"]:
        return "tampered"
    for key in ("session_binding", "repo_anchor_hash", "scope_hash", "plan_hash"):
        if receipt[key] != state.get(key):
            return "binding_mismatch"
    if parse_time(receipt["expires_at"]) <= now:
        return "expired"
    if receipt["review_round"] != state.get("review_round") or receipt["decision"] != "ADMITTED":
        return "stale"
    return "valid_current_and_admitted"


def shadow_decision(
    receipt_category: str,
    budget_breach_without_rebase: bool,
    existing_result: dict[str, Any],
) -> dict[str, Any]:
    _ = receipt_category, budget_breach_without_rebase
    return dict(existing_result)


def cmd_freeze(args: argparse.Namespace) -> dict[str, Any]:
    now = parse_time(args.now)
    binding = session_binding(args.session_id)
    envelope = validate_scope(read_json(Path(args.envelope), "scope envelope"), binding)
    home = codex_home(args.codex_home)
    path = state_path(home, binding)
    if path.exists():
        previous = load_state(home, binding)
        if envelope["scope_version"] <= previous["scope_version"]:
            raise GovernorError("scope_version must increase when replacing frozen scope")
    state = {
        "schema_version": 1,
        "status": "FROZEN",
        "session_binding": binding,
        "repo_anchor_hash": sha256_text(str(Path(envelope["repo_anchor"]).expanduser().resolve(strict=False))),
        "scope_hash": hash_value(envelope),
        "scope_id_hash": sha256_text(envelope["scope_id"]),
        "scope_version": envelope["scope_version"],
        "complexity_budget": envelope["complexity_budget"],
        "review_round": 0,
        "plan_hash": "",
        "last_receipt_hash": "",
        "repeated_presentations": {},
        "unresolved_category_counts": {},
        "budget_breach_without_rebase": False,
        "updated_at": iso_time(now),
        "expires_at": iso_time(now + timedelta(days=30)),
    }
    atomic_json(path, state, private_parent=True)
    append_guardrail(
        home,
        "freeze",
        "FROZEN",
        {"scope_hash": state["scope_hash"], "scope_version": state["scope_version"]},
        now,
    )
    return {"status": "FROZEN", "scope_hash": state["scope_hash"], "state_path": str(path)}


def cmd_evaluate_round(args: argparse.Namespace) -> dict[str, Any]:
    now = parse_time(args.now)
    binding = session_binding(args.session_id)
    home = codex_home(args.codex_home)
    state = load_state(home, binding)
    if parse_time(state["expires_at"]) <= now:
        raise GovernorError("expired governor state: scope decision required")
    findings_value = read_json(Path(args.findings), "findings")
    if not isinstance(findings_value, list) or not findings_value:
        raise GovernorError("findings must be a non-empty array")
    findings = [validate_finding(item) for item in findings_value]
    plan_hash = sha256_text(Path(args.plan).read_text(encoding="utf-8"))
    if args.review_round <= state.get("review_round", 0):
        raise GovernorError("review_round must increase")

    decisions = [evaluate_finding(item, state["complexity_budget"]) for item in findings]
    unresolved_counts = dict(state.get("unresolved_category_counts", {}))
    for decision in decisions:
        if decision["status"] == "non_terminal":
            category = decision["category_hash"]
            unresolved_counts[category] = unresolved_counts.get(category, 0) + 1
    repeated_unresolved = any(count >= 2 for count in unresolved_counts.values())
    budget_breach = any(item["disposition"] == "SCOPE_REBASE_REQUIRED" for item in decisions)
    all_terminal = all(item["status"] == "terminal" for item in decisions)
    if budget_breach or repeated_unresolved:
        round_decision = "REBASE_REQUIRED"
        next_status = "REBASE_REQUIRED"
    elif all_terminal:
        round_decision = "ADMITTED"
        next_status = "CLOSED"
    else:
        round_decision = "SCOPE_DECISION_REQUIRED"
        next_status = "SCOPE_DECISION_REQUIRED"

    delta = aggregate_delta(findings)
    state.update(
        {
            "status": next_status,
            "review_round": args.review_round,
            "plan_hash": plan_hash,
            "finding_set_hash": hash_value(findings),
            "architecture_delta_hash": hash_value(delta),
            "unresolved_category_counts": unresolved_counts,
            "budget_breach_without_rebase": budget_breach or repeated_unresolved,
            "updated_at": iso_time(now),
            "expires_at": iso_time(now + timedelta(days=30)),
        }
    )
    receipt = build_receipt(
        state,
        finding_set_hash=state["finding_set_hash"],
        architecture_delta_hash=state["architecture_delta_hash"],
        decision=round_decision,
        now=now,
    )
    state["last_receipt_hash"] = hash_value(receipt)
    atomic_json(state_path(home, binding), state, private_parent=True)
    if args.receipt_out:
        atomic_json(Path(args.receipt_out), receipt)
    append_guardrail(
        home,
        "evaluate_round",
        round_decision,
        {
            "scope_hash": state["scope_hash"],
            "plan_hash": plan_hash,
            "review_round": args.review_round,
            "finding_count": len(findings),
            "terminal_count": sum(item["status"] == "terminal" for item in decisions),
            "budget_breach_without_rebase": state["budget_breach_without_rebase"],
        },
        now,
    )
    return {
        "status": next_status,
        "decision": round_decision,
        "findings": decisions,
        "receipt": receipt,
        "shadow": {"mode": "shadow", "existing_result_preserved": True},
    }


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    return state_status(codex_home(args.codex_home), session_binding(args.session_id), parse_time(args.now))


def cmd_verify_receipt(args: argparse.Namespace) -> dict[str, Any]:
    now = parse_time(args.now)
    binding = session_binding(args.session_id)
    home = codex_home(args.codex_home)
    state = load_state(home, binding)
    receipt: Any = None
    if args.receipt:
        try:
            receipt = Path(args.receipt).read_text(encoding="utf-8")
        except OSError as exc:
            raise GovernorError(f"missing receipt: {args.receipt}") from exc
    expected = dict(state)
    expected["repo_anchor_hash"] = sha256_text(str(Path(args.repo_anchor).expanduser().resolve(strict=False)))
    expected["plan_hash"] = sha256_text(Path(args.plan).read_text(encoding="utf-8"))
    category = classify_receipt(receipt, expected, now)
    receipt_hash = hash_value(json.loads(receipt)) if category == "valid_current_and_admitted" else ""
    repeats = dict(state.get("repeated_presentations", {}))
    repeated = bool(receipt_hash and repeats.get(receipt_hash, 0))
    if receipt_hash:
        repeats[receipt_hash] = repeats.get(receipt_hash, 0) + 1
        state["repeated_presentations"] = repeats
        state["updated_at"] = iso_time(now)
        atomic_json(state_path(home, binding), state, private_parent=True)
    append_guardrail(
        home,
        "verify_receipt",
        category,
        {
            "receipt_category": category,
            "repeated_presentation": repeated,
            "budget_breach_without_rebase": state.get("budget_breach_without_rebase", False),
        },
        now,
    )
    return {
        "category": category,
        "repeated_presentation": repeated,
        "budget_breach_without_rebase": state.get("budget_breach_without_rebase", False),
        "shadow": {"mode": "shadow", "existing_result_preserved": True},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Runtime Plan Governor v1 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--codex-home")
    freeze.add_argument("--session-id", required=True)
    freeze.add_argument("--envelope", required=True)
    freeze.add_argument("--now")
    freeze.set_defaults(func=cmd_freeze)

    evaluate = subparsers.add_parser("evaluate-round")
    evaluate.add_argument("--codex-home")
    evaluate.add_argument("--session-id", required=True)
    evaluate.add_argument("--findings", required=True)
    evaluate.add_argument("--plan", required=True)
    evaluate.add_argument("--review-round", required=True, type=int)
    evaluate.add_argument("--receipt-out")
    evaluate.add_argument("--now")
    evaluate.set_defaults(func=cmd_evaluate_round)

    status = subparsers.add_parser("status")
    status.add_argument("--codex-home")
    status.add_argument("--session-id", required=True)
    status.add_argument("--now")
    status.set_defaults(func=cmd_status)

    verify = subparsers.add_parser("verify-receipt")
    verify.add_argument("--codex-home")
    verify.add_argument("--session-id", required=True)
    verify.add_argument("--receipt")
    verify.add_argument("--plan", required=True)
    verify.add_argument("--repo-anchor", required=True)
    verify.add_argument("--now")
    verify.set_defaults(func=cmd_verify_receipt)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = args.func(args)
    except (GovernorError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
