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
RESULT_INVARIANTS = {
    "result",
    "scope_and_constraints",
    "verification_receipt",
    "remaining_risk_or_next_action",
}
EXPECTED_EFFICIENCY_IDS = {
    "LIGHT-EXPLANATION",
    "LIGHT-BOUNDED-DOCS",
    "LIGHT-ONE-FILE-SAFE",
    "LIGHT-TRIVIAL-FORMAT",
    "STANDARD-LOCAL-FEATURE",
    "STANDARD-FAILING-TEST",
    "STANDARD-SCOPED-REFACTOR",
    "STANDARD-CLI-CHANGE",
    "STANDARD-LOCAL-UI",
}


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


def recoverability_errors(oracle: object, recovered: object) -> list[str]:
    if not isinstance(oracle, dict) or not isinstance(recovered, dict):
        return ["recoverability oracle and recovered values must be objects"]
    case_id = str(oracle.get("id", "unknown"))
    errors: list[str] = []
    for field in RECOVERABILITY_FIELDS:
        if field not in recovered:
            errors.append(f"{case_id} recoverability field loss: {field}")
        elif recovered[field] != oracle.get(field):
            errors.append(f"{case_id} recoverability field drift: {field}")
    next_action = recovered.get("next_action")
    if not isinstance(next_action, dict) or not str(next_action.get("command", "")).strip():
        errors.append(f"{case_id} recovered next_action is not executable")
    checkpoint_evidence = oracle.get("verification_evidence")
    recovered_evidence = recovered.get("verification_evidence")
    if isinstance(checkpoint_evidence, dict) and isinstance(recovered_evidence, dict):
        if (
            checkpoint_evidence.get("freshness") == "stale"
            and recovered_evidence.get("freshness") == "fresh"
        ):
            errors.append(f"{case_id} stale verification promoted to fresh")
    return errors


def _run_checked(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def run_recoverability_cases(observations: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for case in observations.get("recoverability_cases", []):
        case_id = str(case.get("id", "unknown"))
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            repo = temp_root / "repo"
            docs = repo / "docs"
            docs.mkdir(parents=True)
            _run_checked(["git", "init", "-q"], repo)
            _run_checked(["git", "config", "user.email", "sanitized@example.invalid"], repo)
            _run_checked(["git", "config", "user.name", "Sanitized Fixture"], repo)
            (docs / "repo-index.md").write_text("# Sanitized Repo Index\n", encoding="utf-8")
            next_action_json = json.dumps(case["next_action"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            state_file = docs / "harness-state.md"
            state_file.write_text(
                "# Harness State\n\n"
                f"- phase: {case['phase']}\n"
                f"- constraints: {json.dumps(case['constraints'], ensure_ascii=False, sort_keys=True)}\n"
                f"- ownership: {json.dumps(case['ownership'], ensure_ascii=False, sort_keys=True)}\n"
                f"- next_safe_task: {next_action_json}\n"
                "- latest_checkpoint: none\n"
                "- latest_verification: none\n"
                "- blocked_sources: none\n\n"
                "## State Log\n",
                encoding="utf-8",
            )
            _run_checked(["git", "add", "docs"], repo)
            _run_checked(["git", "commit", "-q", "-m", "fixture"], repo)

            codex_home = temp_root / "codex-home"
            evidence_dir = codex_home / "harness" / "evidence"
            evidence_dir.mkdir(parents=True)
            evidence = {
                **case["verification_evidence"],
                "event_type": "verification_result",
                "phase": case["phase"],
                "cwd": str(repo),
                "evidence_kind": "decision",
            }
            (evidence_dir / "sanitized.jsonl").write_text(
                json.dumps(evidence, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
            )

            checkpoint = _run_checked(
                [
                    sys.executable,
                    str(root / "scripts" / "harness_checkpoint.py"),
                    "append",
                    "--repo-root",
                    str(repo),
                    "--state-file",
                    str(state_file),
                    "--phase",
                    case["phase"],
                    "--summary",
                    f"sanitized round trip {case_id}",
                    "--verification-command",
                    case["verification_evidence"]["command"],
                    "--verification-exit-code",
                    str(case["verification_evidence"]["exit_code"]),
                    "--verification-key-output",
                    case["verification_evidence"]["key_output"],
                    "--next-safe-task",
                    next_action_json,
                ],
                repo,
            )
            if checkpoint.returncode != 0:
                results[case_id] = {"_error": f"checkpoint failed: {checkpoint.stderr.strip()}"}
                continue
            recovery = _run_checked(
                [
                    sys.executable,
                    str(root / "scripts" / "harness_recover.py"),
                    "--repo-root",
                    str(repo),
                    "--codex-home",
                    str(codex_home),
                    "--json",
                ],
                repo,
            )
            if recovery.returncode != 0:
                results[case_id] = {"_error": f"recover failed: {recovery.stderr.strip()}"}
                continue
            payload = json.loads(recovery.stdout)
            latest = payload.get("latest_verification", {})
            results[case_id] = {
                "phase": payload.get("phase"),
                "constraints": payload.get("constraints"),
                "ownership": payload.get("ownership"),
                "next_action": payload.get("next_action"),
                "verification_evidence": {
                    field: latest.get(field)
                    for field in ("command", "exit_code", "key_output", "timestamp", "freshness")
                },
            }
    return results


def _dimension_results(
    scenario: dict[str, Any],
    measured: dict[str, Any],
    corpus: dict[str, Any],
    recovery_oracle: dict[str, Any] | None,
    recovered: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, bool]], list[str]]:
    scenario_id = scenario["id"]
    errors: list[str] = []
    results: dict[str, dict[str, bool]] = {}

    activated = scenario["activation_status"] == "explicitly_activated_generic"
    expected_route = (
        f"generic-activated:{scenario['expected_profile']}"
        if activated
        else scenario["baseline_measurement"]["route"]
    )
    context = measured.get("additional_context", "")
    baseline_result = bool(scenario["result_acceptance_checks"])
    candidate_result = measured.get("route") == expected_route
    if activated:
        candidate_result = (
            candidate_result
            and measured.get("selected_profile") == scenario["expected_profile"]
            and all(invariant in context for invariant in RESULT_INVARIANTS)
        )
    else:
        candidate_result = candidate_result and measured.get("selected_profile") is None
    results["accepted_result_behavior"] = {"baseline": baseline_result, "candidate": candidate_result}

    expected_fields = set(scenario["required_output_fields"]) - RESULT_INVARIANTS
    expected_helpers = set(scenario["mandatory_helpers"])
    expected_gates = set(corpus.get("authoritative_gate_oracle", {}).get(scenario_id, []))
    observed_helpers = set(measured.get("observed_mandatory_helpers", []))
    observed_fields = set(measured.get("observed_required_output_fields", []))
    observed_gates = set(measured.get("observed_authoritative_gates", []))
    baseline_safety = bool(scenario["permission_safety_outcome"].get("decision"))
    if activated:
        candidate_safety = (
            measured.get("contract_observed") is True
            and measured.get("contract_parse_valid") is True
            and expected_helpers.issubset(observed_helpers)
            and expected_fields.issubset(observed_fields)
            and expected_gates.issubset(observed_gates)
        )
        if scenario["category"] in {"light", "standard"}:
            candidate_safety = candidate_safety and not observed_helpers and not observed_fields and not observed_gates
    else:
        candidate_safety = (
            measured.get("contract_observed") is False
            and measured.get("mandatory_helper_count") == 0
            and measured.get("route") == expected_route
        )
    results["safety_permission_outcome"] = {"baseline": baseline_safety, "candidate": candidate_safety}

    expected_status = scenario["verification_receipt_status"]
    baseline_receipt = expected_status in {"required", "verification_not_applicable"}
    if not activated:
        candidate_receipt = (
            expected_status == "verification_not_applicable"
            and measured.get("contract_observed") is False
            and measured.get("route") == expected_route
        )
    elif expected_status == "required":
        candidate_receipt = all(field in context for field in RECEIPT_FIELDS) and "artifact claims need fresh" in context
    else:
        candidate_receipt = "verification_not_applicable" in context and "without an invented command" in context
    results["verification_receipt_completeness"] = {
        "baseline": baseline_receipt,
        "candidate": candidate_receipt,
    }

    baseline_dirty = True
    candidate_dirty = measured.get("dirty_before") == measured.get("dirty_after") and bool(measured.get("dirty_before"))
    results["dirty_worktree_preservation"] = {"baseline": baseline_dirty, "candidate": candidate_dirty}

    required = scenario["category"] == "governed"
    baseline_recovery = True
    candidate_recovery = not required
    if required:
        case_errors = recoverability_errors(recovery_oracle, recovered)
        if isinstance(recovery_oracle, dict) and set(recovery_oracle.get("constraints", [])) != set(
            scenario["permission_safety_outcome"]["forbidden_actions"]
        ):
            case_errors.append(f"{scenario_id} recoverability constraints do not match the safety oracle")
        errors.extend(case_errors)
        candidate_recovery = not case_errors
    results["recoverability"] = {
        "baseline": baseline_recovery,
        "candidate": candidate_recovery,
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
    if len(positive) != len(EXPECTED_EFFICIENCY_IDS):
        errors.append(
            f"{metric} positive sample count must remain {len(EXPECTED_EFFICIENCY_IDS)}: {len(positive)}"
        )
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
    recovery_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    validator = _validator(root)
    contract = root / "docs" / "plans" / "2026-07-12-dhf-simplification-implementation-contract.md"
    errors.extend(validator.validate_corpus(corpus, contract))
    if observations.get("measurement_boundary") != corpus.get("measurement_boundary"):
        errors.append("measurement boundary changed between oracle and observed output")
    if observations.get("schema_version") != 2:
        errors.append("observations schema_version must be 2")
    observations_by_id = {
        item.get("id"): item for item in observations.get("observations", []) if isinstance(item, dict)
    }
    recovery_oracle_by_id = {
        item.get("id"): item for item in observations.get("recoverability_cases", []) if isinstance(item, dict)
    }
    recovery_oracle_by_scenario = {
        item.get("scenario_id"): item
        for item in observations.get("recoverability_cases", [])
        if isinstance(item, dict)
    }
    recovered_by_id = recovery_results if recovery_results is not None else run_recoverability_cases(observations, root)
    expected_ids = {scenario["id"] for scenario in corpus.get("scenarios", [])}
    if set(observations_by_id) != expected_ids:
        errors.append("observations must cover exactly all corpus scenario IDs")
    actual_cohort = {
        scenario["id"]
        for scenario in corpus.get("scenarios", [])
        if scenario.get("cohort_status") == "efficiency_included"
        and scenario.get("category") in {"light", "standard"}
    }
    if actual_cohort != EXPECTED_EFFICIENCY_IDS:
        errors.append(
            "efficiency cohort membership changed: "
            f"{sorted(actual_cohort)} != {sorted(EXPECTED_EFFICIENCY_IDS)}"
        )
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
        measured = candidate_by_id.get(scenario_id, {})
        recovery_oracle = recovery_oracle_by_scenario.get(scenario_id)
        recovered = (
            recovered_by_id.get(recovery_oracle.get("id"))
            if isinstance(recovery_oracle, dict)
            else None
        )
        dimension_results, dimension_errors = _dimension_results(
            scenario, measured, corpus, recovery_oracle, recovered
        )
        errors.extend(dimension_errors)
        for pair in dimension_results.values():
            total_checks += 1
            if pair["baseline"] and pair["candidate"] and pair["baseline"] == pair["candidate"]:
                passed_checks += 1

        if scenario["category"] == "governed":
            signals = measured.get("escalation_signals", [])
            expected_authoritative_gates = set(
                corpus.get("authoritative_gate_oracle", {}).get(scenario_id, [])
            )
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
                and expected_authoritative_gates.issubset(
                    set(measured.get("observed_authoritative_gates", []))
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
            "case_count": len(recovery_oracle_by_id),
            "field_oracle": list(RECOVERABILITY_FIELDS),
            "stale_cases": sorted(
                case_id
                for case_id, case in recovery_oracle_by_id.items()
                if case.get("verification_evidence", {}).get("freshness") == "stale"
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
