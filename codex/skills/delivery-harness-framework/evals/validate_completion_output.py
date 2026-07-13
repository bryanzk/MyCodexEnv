#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CLAIM_CLASSES = {
    "implemented_or_fixed",
    "documented_or_configured",
    "diagnosed_or_blocked",
    "verification_not_applicable",
}
RESULT_INVARIANTS = {
    "result",
    "scope_and_constraints",
    "verification_receipt",
    "remaining_risk_or_next_action",
}
COMMAND_RECEIPT_FIELDS = {"command", "exit_code", "key_output", "timestamp"}


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _meaningful(value: object) -> bool:
    if _non_empty_text(value):
        return True
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def _validate_command_receipt(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(COMMAND_RECEIPT_FIELDS - set(receipt))
    if missing:
        errors.append(f"missing receipt fields: {', '.join(missing)}")
        return errors
    for field in ("command", "key_output", "timestamp"):
        if not _non_empty_text(receipt[field]):
            errors.append(f"verification_receipt.{field} must be non-empty text")
    if not isinstance(receipt["exit_code"], int) or isinstance(receipt["exit_code"], bool):
        errors.append("verification_receipt.exit_code must be an integer")
    return errors


def validate_output_sample(sample: object) -> list[str]:
    if not isinstance(sample, dict):
        return ["output sample must be an object"]
    errors: list[str] = []
    claim = sample.get("completion_claim_class")
    if claim not in CLAIM_CLASSES:
        errors.append(f"invalid completion_claim_class: {claim}")
    missing_invariants = sorted(RESULT_INVARIANTS - set(sample))
    if missing_invariants:
        errors.append(f"missing result invariant fields: {', '.join(missing_invariants)}")
        return errors
    if not _meaningful(sample["result"]):
        errors.append("result must be meaningful")
    if not _meaningful(sample["scope_and_constraints"]):
        errors.append("scope_and_constraints must be meaningful")
    next_action = sample["remaining_risk_or_next_action"]
    if next_action is not None and not _meaningful(next_action):
        errors.append("remaining_risk_or_next_action must be meaningful or null")

    receipt = sample["verification_receipt"]
    if not isinstance(receipt, dict):
        errors.append("verification_receipt must be an object")
        return errors
    if claim in {"implemented_or_fixed", "documented_or_configured"}:
        errors.extend(_validate_command_receipt(receipt))
    elif claim == "diagnosed_or_blocked":
        if not _non_empty_text(receipt.get("concrete_evidence")):
            errors.append("diagnosed_or_blocked requires concrete_evidence")
        if not _non_empty_text(receipt.get("exact_blocker")):
            errors.append("diagnosed_or_blocked requires exact_blocker")
        present_command_fields = COMMAND_RECEIPT_FIELDS & set(receipt)
        if present_command_fields:
            errors.extend(_validate_command_receipt(receipt))
    elif claim == "verification_not_applicable":
        if receipt.get("status") != "verification_not_applicable":
            errors.append("pure explanation receipt status must be verification_not_applicable")
        if not _non_empty_text(receipt.get("reason")):
            errors.append("verification_not_applicable requires a reason")
        forbidden = sorted(COMMAND_RECEIPT_FIELDS & (set(receipt) | set(sample)))
        if forbidden:
            errors.append(
                "verification_not_applicable must not include command receipt fields: "
                + ", ".join(forbidden)
            )
    return errors


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_evals(payload: object) -> tuple[list[str], int]:
    if not isinstance(payload, dict) or not isinstance(payload.get("evals"), list):
        return ["evals document must contain an evals list"], 0
    errors: list[str] = []
    count = 0
    for case in payload["evals"]:
        if not isinstance(case, dict) or "completion_claim_class" not in case:
            continue
        count += 1
        case_id = case.get("id", f"case-{count}")
        sample = case.get("structured_output_sample")
        if isinstance(sample, dict) and sample.get("completion_claim_class") != case["completion_claim_class"]:
            errors.append(f"{case_id}: sample claim class does not match eval case")
        errors.extend(f"{case_id}: {error}" for error in validate_output_sample(sample))
    if count != len(CLAIM_CLASSES):
        errors.append(f"expected {len(CLAIM_CLASSES)} completion claim samples, found {count}")
    return errors, count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate structured DHF completion output samples.")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--sample", type=Path)
    inputs.add_argument("--evals", type=Path)
    args = parser.parse_args()
    try:
        payload = _load_json(args.sample or args.evals)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read JSON: {exc}", file=sys.stderr)
        return 1
    if args.sample:
        errors = validate_output_sample(payload)
        count = 1
    else:
        errors, count = _validate_evals(payload)
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1
    print(json.dumps({"valid": True, "sample_count": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
