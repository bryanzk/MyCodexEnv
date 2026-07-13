#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "accepted_result_behavior",
    "safety_permission_outcome",
    "verification_receipt_completeness",
    "dirty_worktree_preservation",
    "recoverability",
)
RECEIPT_FIELDS = {"command", "exit_code", "key_output", "timestamp"}
RECOVERABILITY_FIELDS = ("phase", "constraints", "ownership", "next_action", "verification_evidence")
HELPER_CLIS = (
    "harness_recover.py",
    "harness_env_probe.py",
    "harness_requirements.py",
    "harness_report.py",
    "harness_agent_team.py",
    "harness_checkpoint.py",
)
TARGET_REDUCTION = 0.40


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validator(root: Path):
    return _load_module(
        root / "scripts" / "validate_dhf_simplification_corpus.py",
        "dhf_simplification_pair_validator",
    )


def measure_candidate(corpus: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    return _validator(root).measure_candidate(corpus, root)


def measure_baseline(corpus: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    return _validator(root).measure_baseline(corpus, root)


def recoverability_errors(case: object) -> list[str]:
    if not isinstance(case, dict):
        return ["recoverability case must be an object"]
    case_id = str(case.get("id", "unknown"))
    checkpoint = case.get("checkpoint")
    recovered = case.get("recovered")
    if not isinstance(checkpoint, dict) or not isinstance(recovered, dict):
        return [f"{case_id} recoverability checkpoint and recovered values must be objects"]
    errors: list[str] = []
    for field in RECOVERABILITY_FIELDS:
        if field not in recovered:
            errors.append(f"{case_id} recoverability field loss: {field}")
        elif recovered[field] != checkpoint.get(field):
            errors.append(f"{case_id} recoverability field drift: {field}")
    next_action = recovered.get("next_action")
    if not isinstance(next_action, dict) or not str(next_action.get("command", "")).strip():
        errors.append(f"{case_id} recovered next_action is not executable")
    checkpoint_evidence = checkpoint.get("verification_evidence")
    recovered_evidence = recovered.get("verification_evidence")
    if isinstance(checkpoint_evidence, dict) and isinstance(recovered_evidence, dict):
        if (
            checkpoint_evidence.get("freshness") == "stale"
            and recovered_evidence.get("freshness") == "fresh"
        ):
            errors.append(f"{case_id} stale verification promoted to fresh")
    return errors


def _dimension_results(
    scenario: dict[str, Any], observation: dict[str, Any], recoverability_by_id: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, bool]], list[str]]:
    scenario_id = scenario["id"]
    errors: list[str] = []
    results: dict[str, dict[str, bool]] = {}

    result_observation = observation.get("accepted_result_behavior", {})
    expected_checks = {item["id"] for item in scenario["result_acceptance_checks"]}
    observed_checks = set(result_observation.get("check_ids", []))
    oracle_match = observed_checks == expected_checks
    baseline_result = oracle_match and result_observation.get("baseline_accepted") is True
    candidate_result = oracle_match and result_observation.get("candidate_accepted") is True
    results["accepted_result_behavior"] = {"baseline": baseline_result, "candidate": candidate_result}

    safety = observation.get("safety_permission_outcome", {})
    expected_safety = scenario["permission_safety_outcome"]
    safety_match = (
        safety.get("decision") == expected_safety["decision"]
        and set(safety.get("forbidden_actions", [])) == set(expected_safety["forbidden_actions"])
    )
    baseline_safety = safety_match and safety.get("baseline_preserved") is True
    candidate_safety = safety_match and safety.get("candidate_preserved") is True
    results["safety_permission_outcome"] = {"baseline": baseline_safety, "candidate": candidate_safety}

    receipt = observation.get("verification_receipt", {})
    expected_status = scenario["verification_receipt_status"]
    fields = RECEIPT_FIELDS if expected_status == "required" else set()
    status_match = receipt.get("status") == expected_status
    baseline_receipt = status_match and set(receipt.get("baseline_fields", [])) == fields
    candidate_receipt = status_match and set(receipt.get("candidate_fields", [])) == fields
    results["verification_receipt_completeness"] = {
        "baseline": baseline_receipt,
        "candidate": candidate_receipt,
    }

    dirty = observation.get("dirty_worktree", {})
    before = dirty.get("before")
    baseline_dirty = isinstance(before, list) and dirty.get("baseline_after") == before
    candidate_dirty = isinstance(before, list) and dirty.get("candidate_after") == before
    results["dirty_worktree_preservation"] = {"baseline": baseline_dirty, "candidate": candidate_dirty}

    recovery = observation.get("recoverability", {})
    required = scenario["category"] == "governed"
    recovery_ok = not required and recovery.get("status") == "not_required"
    if required:
        case_id = recovery.get("case_id")
        case = recoverability_by_id.get(case_id)
        case_errors = recoverability_errors(case)
        if isinstance(case, dict):
            checkpoint = case.get("checkpoint", {})
            if set(checkpoint.get("constraints", [])) != set(
                scenario["permission_safety_outcome"]["forbidden_actions"]
            ):
                case_errors.append(f"{case_id} recoverability constraints do not match the safety oracle")
            if not isinstance(checkpoint.get("ownership"), dict) or not checkpoint["ownership"]:
                case_errors.append(f"{case_id} recoverability ownership is missing")
        errors.extend(case_errors)
        recovery_ok = (
            recovery.get("status") == "required"
            and case is not None
            and not case_errors
        )
    results["recoverability"] = {
        "baseline": recovery_ok and recovery.get("baseline_pass") is True,
        "candidate": recovery_ok and recovery.get("candidate_pass") is True,
    }

    for dimension, pair in results.items():
        if not pair["baseline"] or not pair["candidate"] or pair["baseline"] != pair["candidate"]:
            errors.append(f"{scenario_id} parity loss: {dimension}")
    return results, errors


def _metric_summary(
    metric: str,
    corpus: dict[str, Any],
    baseline_by_id: dict[str, dict[str, Any]],
    candidate_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    key = "injected_context_utf8_bytes_proxy" if metric == "context" else "mandatory_helper_count"
    cohort_ids = {
        scenario["id"]
        for scenario in corpus["scenarios"]
        if scenario["cohort_status"] == "efficiency_included" and scenario["category"] in {"light", "standard"}
    }
    positive = []
    zero = []
    errors: list[str] = []
    for scenario in corpus["scenarios"]:
        scenario_id = scenario["id"]
        baseline = baseline_by_id[scenario_id][key]
        candidate = candidate_by_id[scenario_id][key]
        if scenario_id in cohort_ids and baseline > 0:
            positive.append(
                {
                    "id": scenario_id,
                    "baseline": baseline,
                    "candidate": candidate,
                    "relative_reduction": (baseline - candidate) / baseline,
                }
            )
        if baseline == 0:
            zero.append({"id": scenario_id, "baseline": 0, "candidate": candidate})
            if candidate != 0:
                errors.append(f"{scenario_id} zero-baseline {metric} regression: candidate={candidate}")
    reductions = [item["relative_reduction"] for item in positive]
    median = statistics.median(reductions) if reductions else None
    if median is None or median < TARGET_REDUCTION:
        errors.append(f"{metric} median reduction target missed: {median}")
    return (
        {
            "positive_baseline_sample_count": len(positive),
            "zero_baseline_sample_count": len(zero),
            "median_relative_reduction": median,
            "target_relative_reduction": TARGET_REDUCTION,
            "positive_baseline_pairs": positive,
            "zero_baseline_non_regression": zero,
            "outliers_below_target": [item["id"] for item in positive if item["relative_reduction"] < TARGET_REDUCTION],
        },
        errors,
    )


def run_rollback_smoke(root: Path) -> dict[str, Any]:
    dispatcher = root / "codex" / "hooks" / "dhf_preprompt.py"
    helper_results = []
    errors = []
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        skill = temp_root / "legacy-skill.md"
        marker = "SANITIZED_LEGACY_ROUTE_MARKER"
        skill.write_text(marker, encoding="utf-8")
        env = os.environ.copy()
        env.update(
            {
                "DHF_PREPROMPT_SIMPLIFIED_PROFILES": "off",
                "DHF_PREPROMPT_SKILL": str(skill),
                "DHF_PREPROMPT_SHIPQ_ROOT": str(temp_root / "ShipQ"),
            }
        )
        proc = subprocess.run(
            [sys.executable, str(dispatcher)],
            input=json.dumps({"cwd": str(temp_root), "prompt": "complex local feature"}),
            env=env,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            payload = json.loads(proc.stdout)
            context = payload.get("hookSpecificOutput", {}).get("additionalContext", "")
        except json.JSONDecodeError:
            context = ""
        legacy_ok = proc.returncode == 0 and marker in context and "generic-activated:legacy" in proc.stderr
        if not legacy_ok:
            errors.append("explicit rollback did not execute the legacy dispatcher route")

    for helper_name in HELPER_CLIS:
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / helper_name), "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        callable_ok = proc.returncode == 0 and "usage:" in proc.stdout.lower()
        helper_results.append({"name": helper_name, "exit_code": proc.returncode, "usage_output": callable_ok})
        if not callable_ok:
            errors.append(f"legacy helper CLI not callable: {helper_name}")
    return {
        "pass": not errors,
        "explicit_off_value": "off",
        "legacy_dispatcher_route": "generic-activated:legacy" if not errors or legacy_ok else "failed",
        "helpers": helper_results,
        "errors": errors,
    }


def run_comparison(
    corpus: dict[str, Any],
    observations: dict[str, Any],
    root: Path,
    *,
    candidate_measurements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if observations.get("measurement_boundary") != corpus.get("measurement_boundary"):
        errors.append("measurement boundary changed between oracle and observed output")
    observations_by_id = {
        item.get("id"): item for item in observations.get("observations", []) if isinstance(item, dict)
    }
    recoverability_by_id = {
        item.get("id"): item for item in observations.get("recoverability_cases", []) if isinstance(item, dict)
    }
    validator = _validator(root)
    baseline = validator.measure_baseline(corpus, root)
    candidate = candidate_measurements if candidate_measurements is not None else measure_candidate(corpus, root)
    errors.extend(validator.validate_candidate_measurements(corpus, root, candidate))
    baseline_by_id = {item["id"]: item for item in baseline}
    candidate_by_id = {item["id"]: item for item in candidate}
    raw_results = []
    passed_checks = 0
    total_checks = 0
    governed_under_routing = []

    for scenario in corpus["scenarios"]:
        scenario_id = scenario["id"]
        observation = observations_by_id.get(scenario_id)
        if not isinstance(observation, dict):
            errors.append(f"{scenario_id} missing observed output")
            continue
        expected_input = {
            "prompt": scenario["sanitized_prompt"],
            "cwd_class": scenario["cwd_class"],
            "activation_status": scenario["activation_status"],
        }
        if observation.get("input") != expected_input:
            errors.append(f"{scenario_id} paired input identity changed")
        dimension_results, dimension_errors = _dimension_results(
            scenario, observation, recoverability_by_id
        )
        errors.extend(dimension_errors)
        for pair in dimension_results.values():
            total_checks += 1
            if pair["baseline"] and pair["candidate"] and pair["baseline"] == pair["candidate"]:
                passed_checks += 1

        measured = candidate_by_id.get(scenario_id, {})
        if scenario["category"] == "governed":
            signals = measured.get("escalation_signals", [])
            expected_conditional_fields = set(scenario["required_output_fields"]) - {
                "result",
                "scope_and_constraints",
                "verification_receipt",
                "remaining_risk_or_next_action",
            }
            governed_contract_complete = (
                set(scenario["mandatory_helpers"]).issubset(
                    set(measured.get("observed_mandatory_helpers", []))
                )
                and expected_conditional_fields.issubset(
                    set(measured.get("observed_required_output_fields", []))
                )
            )
            if (
                measured.get("selected_profile") != "governed"
                or scenario["escalation_signal"] not in signals
                or not governed_contract_complete
            ):
                governed_under_routing.append(scenario_id)
                errors.append(f"{scenario_id} governed under-routing")
        raw_results.append(
            {
                "id": scenario_id,
                "input": expected_input,
                "dimensions": dimension_results,
                "baseline_measurement": baseline_by_id.get(scenario_id),
                "candidate_measurement": measured,
            }
        )

    context_summary, context_errors = _metric_summary(
        "context", corpus, baseline_by_id, candidate_by_id
    )
    helper_summary, helper_errors = _metric_summary(
        "helpers", corpus, baseline_by_id, candidate_by_id
    )
    errors.extend(context_errors)
    errors.extend(helper_errors)
    rollback = run_rollback_smoke(root)
    errors.extend(rollback["errors"])
    parity = {
        "dimensions": list(DIMENSIONS),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "rate": passed_checks / total_checks if total_checks else 0.0,
    }
    return {
        "schema_version": 1,
        "pass": not errors and total_checks == len(corpus["scenarios"]) * len(DIMENSIONS),
        "scenario_count": len(corpus["scenarios"]),
        "measurement_boundary": corpus["measurement_boundary"],
        "parity": parity,
        "governed_under_routing": governed_under_routing,
        "efficiency": {"context": context_summary, "helpers": helper_summary},
        "recoverability": {
            "case_count": len(recoverability_by_id),
            "field_oracle": list(RECOVERABILITY_FIELDS),
            "stale_cases": sorted(
                case_id
                for case_id, case in recoverability_by_id.items()
                if case.get("checkpoint", {}).get("verification_evidence", {}).get("freshness") == "stale"
            ),
        },
        "rollback_smoke": rollback,
        "raw_results": raw_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic paired DHF simplification acceptance checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("corpus")
    compare.add_argument("--observations", required=True)
    compare.add_argument("--json", action="store_true")
    args = parser.parse_args()

    corpus_path = Path(args.corpus).resolve()
    observations_path = Path(args.observations).resolve()
    root = corpus_path.parents[2]
    try:
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        observations = json.loads(observations_path.read_text(encoding="utf-8"))
        report = run_comparison(corpus, observations, root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"pass={str(report['pass']).lower()} parity={report['parity']['passed_checks']}/"
            f"{report['parity']['total_checks']} context_median="
            f"{report['efficiency']['context']['median_relative_reduction']:.6f} helper_median="
            f"{report['efficiency']['helpers']['median_relative_reduction']:.6f}"
        )
    if not report["pass"]:
        print("ERROR: " + "; ".join(report["errors"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
