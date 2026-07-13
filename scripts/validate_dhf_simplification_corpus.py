#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


MINIMUM_CATEGORY_COUNTS = {"light": 4, "standard": 5, "governed": 6}
ALLOWED_CWD_CLASSES = {"generic_repo", "shipq_repo"}
ALLOWED_COHORT_STATUSES = {"efficiency_included", "routing_control_excluded"}
ALLOWED_RECEIPT_STATUSES = {"required", "verification_not_applicable"}
REQUIRED_SCENARIO_FIELDS = {
    "id",
    "category",
    "scenario_type",
    "sanitized_prompt",
    "activation_status",
    "cohort_status",
    "cwd_class",
    "expected_profile",
    "escalation_signal",
    "mandatory_helpers",
    "forbidden_helpers",
    "required_output_fields",
    "permission_safety_outcome",
    "result_acceptance_checks",
    "baseline_mandatory_helpers",
    "baseline_measurement",
    "verification_receipt_status",
}
REQUIRED_BASELINE_FIELDS = {
    "route",
    "injected_context_utf8_bytes_proxy",
    "mandatory_helper_count",
    "verification_receipt_status",
    "known_mismatches",
}


def extract_acceptance_criteria(contract_path: Path) -> list[str]:
    text = contract_path.read_text(encoding="utf-8")
    marker = "## Acceptance Criteria\n"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    criteria: list[str] = []
    current: list[str] = []
    for raw_line in section.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- [ ] "):
            if current:
                criteria.append(" ".join(current))
            current = [stripped[6:].strip()]
        elif current and stripped:
            current.append(stripped)
    if current:
        criteria.append(" ".join(current))
    return criteria


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_scenario(scenario: object, index: int) -> list[str]:
    prefix = f"scenario[{index}]"
    if not isinstance(scenario, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_SCENARIO_FIELDS - set(scenario))
    if missing:
        errors.append(f"{prefix} missing required fields: {', '.join(missing)}")
        return errors

    for field in ("id", "scenario_type", "sanitized_prompt", "activation_status"):
        if not _non_empty_string(scenario[field]):
            errors.append(f"{prefix}.{field} must be a non-empty string")
    category = scenario["category"]
    if category not in {*MINIMUM_CATEGORY_COUNTS, "routing_control"}:
        errors.append(f"{prefix}.category is invalid: {category}")
    if scenario["cwd_class"] not in ALLOWED_CWD_CLASSES:
        errors.append(f"{prefix}.cwd_class is invalid: {scenario['cwd_class']}")
    if scenario["cohort_status"] not in ALLOWED_COHORT_STATUSES:
        errors.append(f"{prefix}.cohort_status is invalid: {scenario['cohort_status']}")
    if category in MINIMUM_CATEGORY_COUNTS and scenario["expected_profile"] != category:
        errors.append(f"{prefix}.expected_profile must match category {category}")
    if category == "routing_control" and scenario["expected_profile"] != "not_applicable":
        errors.append(f"{prefix}.expected_profile must be not_applicable")
    if scenario["activation_status"] != "explicitly_activated_generic":
        if scenario["cohort_status"] != "routing_control_excluded":
            errors.append(f"{prefix}: routing controls must be excluded from the efficiency cohort")
    elif scenario["cohort_status"] != "efficiency_included":
        errors.append(f"{prefix}: activated generic scenarios must be included in the efficiency cohort")

    if category == "governed" and not _non_empty_string(scenario["escalation_signal"]):
        errors.append(f"{prefix}.escalation_signal must name the governed trigger")
    if category in {"light", "standard"} and scenario["escalation_signal"] is not None:
        errors.append(f"{prefix}.escalation_signal must be explicit null when absent")

    for field in (
        "mandatory_helpers",
        "forbidden_helpers",
        "required_output_fields",
        "baseline_mandatory_helpers",
    ):
        value = scenario[field]
        if not isinstance(value, list) or any(not _non_empty_string(item) for item in value):
            errors.append(f"{prefix}.{field} must be a string list")
    if set(scenario["mandatory_helpers"]) & set(scenario["forbidden_helpers"]):
        errors.append(f"{prefix} cannot require and forbid the same helper")
    if not scenario["required_output_fields"]:
        errors.append(f"{prefix}.required_output_fields must not be empty")

    outcome = scenario["permission_safety_outcome"]
    if not isinstance(outcome, dict) or not _non_empty_string(outcome.get("decision")):
        errors.append(f"{prefix}.permission_safety_outcome must declare a decision")
    elif not isinstance(outcome.get("forbidden_actions"), list):
        errors.append(f"{prefix}.permission_safety_outcome.forbidden_actions must be a list")

    checks = scenario["result_acceptance_checks"]
    if not isinstance(checks, list) or not checks:
        errors.append(f"{prefix}.result_acceptance_checks must be a non-empty list")
    else:
        for check in checks:
            if not isinstance(check, dict) or not _non_empty_string(check.get("id")) or not _non_empty_string(check.get("assertion")):
                errors.append(f"{prefix}.result_acceptance_checks entries require id and assertion")
                break

    baseline = scenario["baseline_measurement"]
    if not isinstance(baseline, dict):
        errors.append(f"{prefix}.baseline_measurement must be an object")
    else:
        missing_baseline = sorted(REQUIRED_BASELINE_FIELDS - set(baseline))
        if missing_baseline:
            errors.append(f"{prefix}.baseline_measurement missing: {', '.join(missing_baseline)}")
        elif (
            not isinstance(baseline["injected_context_utf8_bytes_proxy"], int)
            or baseline["injected_context_utf8_bytes_proxy"] < 0
            or not isinstance(baseline["mandatory_helper_count"], int)
            or baseline["mandatory_helper_count"] < 0
            or not isinstance(baseline["known_mismatches"], list)
        ):
            errors.append(f"{prefix}.baseline_measurement has invalid measurement values")
    if scenario["verification_receipt_status"] not in ALLOWED_RECEIPT_STATUSES:
        errors.append(f"{prefix}.verification_receipt_status is invalid")
    return errors


def validate_corpus(corpus: object, contract_path: Path) -> list[str]:
    if not isinstance(corpus, dict):
        return ["corpus must be an object"]
    errors: list[str] = []
    if corpus.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    boundary = corpus.get("measurement_boundary")
    if not isinstance(boundary, dict):
        errors.append("measurement_boundary must be an object")
    else:
        if boundary.get("context_unit") != "utf8_bytes_proxy":
            errors.append("measurement boundary must label context as utf8_bytes_proxy")
        if not _non_empty_string(boundary.get("context_boundary")):
            errors.append("measurement boundary must document the injected-context boundary")
        if not _non_empty_string(boundary.get("mandatory_helper_boundary")):
            errors.append("measurement boundary must document the mandatory-helper boundary")
        if boundary.get("token_claimed") is not False:
            errors.append("measurement boundary must explicitly state token_claimed=false")

    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list):
        return errors + ["scenarios must be a list"]
    for index, scenario in enumerate(scenarios):
        errors.extend(_validate_scenario(scenario, index))
    ids = [scenario.get("id") for scenario in scenarios if isinstance(scenario, dict)]
    if len(ids) != len(set(ids)):
        errors.append("scenario IDs must be unique")
    counts = Counter(
        scenario.get("category")
        for scenario in scenarios
        if isinstance(scenario, dict) and scenario.get("category") in MINIMUM_CATEGORY_COUNTS
    )
    for category, minimum in MINIMUM_CATEGORY_COUNTS.items():
        if counts[category] < minimum:
            errors.append(f"at least {minimum} {category} scenarios are required")

    contract_criteria = extract_acceptance_criteria(contract_path)
    expected_trace_ids = {f"AC-{index:02d}" for index in range(1, len(contract_criteria) + 1)}
    trace_map = corpus.get("acceptance_trace_map")
    if not isinstance(trace_map, dict):
        errors.append("acceptance_trace_map must be an object")
        trace_map = {}
    actual_trace_ids = set(trace_map)
    missing_trace_ids = sorted(expected_trace_ids - actual_trace_ids)
    extra_trace_ids = sorted(actual_trace_ids - expected_trace_ids)
    if missing_trace_ids:
        errors.append(f"missing acceptance trace IDs: {', '.join(missing_trace_ids)}")
    if extra_trace_ids:
        errors.append(f"unknown acceptance trace IDs: {', '.join(extra_trace_ids)}")
    known_ids = set(ids)
    for index, criterion in enumerate(contract_criteria, 1):
        trace_id = f"AC-{index:02d}"
        trace = trace_map.get(trace_id)
        if not isinstance(trace, dict):
            continue
        if trace.get("criterion") != criterion:
            errors.append(f"{trace_id} criterion text does not match the contract")
        scenario_ids = trace.get("scenario_ids")
        test_ids = trace.get("test_ids")
        if not isinstance(scenario_ids, list) or not isinstance(test_ids, list) or not (scenario_ids or test_ids):
            errors.append(f"{trace_id} must map to one or more scenario/test IDs")
            continue
        for scenario_id in scenario_ids:
            if scenario_id not in known_ids:
                errors.append(f"{trace_id} references unknown scenario ID: {scenario_id}")
        if not _non_empty_string(trace.get("evidence_status")):
            errors.append(f"{trace_id} must declare evidence_status")
    return errors


def _load_dispatcher(root: Path):
    path = root / "codex" / "hooks" / "dhf_preprompt.py"
    spec = importlib.util.spec_from_file_location("dhf_simplification_baseline_dispatcher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import dispatcher: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measure_baseline(corpus: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    module = _load_dispatcher(root)
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        generic_root = temp_root / "GenericRepo"
        shipq_root = temp_root / "ShipQ"
        generic_root.mkdir()
        shipq_root.mkdir()
        adapter = temp_root / "shipq_adapter.py"
        adapter.write_text(
            "def build_response(_payload):\n"
            "    return {'continue': True, 'hookSpecificOutput': "
            "{'hookEventName': 'UserPromptSubmit', 'additionalContext': "
            "'Sanitized ShipQ adapter baseline context.'}}\n",
            encoding="utf-8",
        )
        module.SHIPQ_ROOT = shipq_root
        module.SHIPQ_ADAPTER = adapter
        module.ALLOW_UNTRUSTED_ADAPTER = True
        module.DHF_SKILL = root / "codex" / "skills" / "delivery-harness-framework" / "SKILL.md"
        cwd_by_class = {"generic_repo": generic_root, "shipq_repo": shipq_root}
        measurements: list[dict[str, Any]] = []
        for scenario in corpus["scenarios"]:
            payload = {
                "cwd": str(cwd_by_class[scenario["cwd_class"]]),
                "prompt": scenario["sanitized_prompt"],
            }
            response, route = module.route_response(payload)
            context = response.get("hookSpecificOutput", {}).get("additionalContext", "")
            measurements.append(
                {
                    "id": scenario["id"],
                    "route": route,
                    "injected_context_utf8_bytes_proxy": len(context.encode("utf-8")),
                    "mandatory_helper_count": len(set(scenario["baseline_mandatory_helpers"])),
                    "verification_receipt_status": scenario["baseline_measurement"]["verification_receipt_status"],
                }
            )
        return measurements


def validate_baseline_measurements(corpus: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    actual_by_id = {item["id"]: item for item in measure_baseline(corpus, root)}
    for scenario in corpus["scenarios"]:
        expected = scenario["baseline_measurement"]
        actual = actual_by_id[scenario["id"]]
        if expected["route"] != actual["route"]:
            errors.append(f"{scenario['id']} route mismatch: {expected['route']} != {actual['route']}")
        if expected["injected_context_utf8_bytes_proxy"] != actual["injected_context_utf8_bytes_proxy"]:
            errors.append(
                f"{scenario['id']} injected-context proxy mismatch: "
                f"{expected['injected_context_utf8_bytes_proxy']} != {actual['injected_context_utf8_bytes_proxy']}"
            )
        if expected["mandatory_helper_count"] != actual["mandatory_helper_count"]:
            errors.append(
                f"{scenario['id']} mandatory-helper count mismatch: "
                f"{expected['mandatory_helper_count']} != {actual['mandatory_helper_count']}"
            )
    return errors


def summary(corpus: dict[str, Any]) -> dict[str, Any]:
    counts = Counter(
        scenario["category"]
        for scenario in corpus["scenarios"]
        if scenario["category"] in MINIMUM_CATEGORY_COUNTS
    )
    return {
        "valid": True,
        "scenario_count": len(corpus["scenarios"]),
        "category_counts": {category: counts[category] for category in MINIMUM_CATEGORY_COUNTS},
        "routing_control_count": sum(
            scenario["category"] == "routing_control" for scenario in corpus["scenarios"]
        ),
        "acceptance_criterion_count": len(corpus["acceptance_trace_map"]),
        "baseline_mismatch_count": sum(
            bool(scenario["baseline_measurement"]["known_mismatches"])
            for scenario in corpus["scenarios"]
        ),
        "measurement_boundary": copy.deepcopy(corpus["measurement_boundary"]),
    }


def cmd_validate(args: argparse.Namespace) -> int:
    corpus_path = Path(args.corpus).resolve()
    contract_path = Path(args.contract).resolve()
    root = corpus_path.parents[2]
    try:
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read corpus: {exc}", file=sys.stderr)
        return 1
    errors = validate_corpus(corpus, contract_path)
    if not errors and args.check_baseline:
        errors.extend(validate_baseline_measurements(corpus, root))
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1
    payload = summary(corpus)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"valid: scenarios={payload['scenario_count']} "
            f"acceptance_criteria={payload['acceptance_criterion_count']} "
            f"baseline_mismatches={payload['baseline_mismatch_count']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and measure the bounded DHF simplification golden corpus."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("corpus")
    validate.add_argument("--contract", required=True)
    validate.add_argument("--check-baseline", action="store_true")
    validate.add_argument("--json", action="store_true")
    validate.set_defaults(func=cmd_validate)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
