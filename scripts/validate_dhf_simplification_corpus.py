#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MINIMUM_CATEGORY_COUNTS = {"light": 4, "standard": 5, "governed": 6}
ALLOWED_CWD_CLASSES = {"generic_repo", "shipq_repo"}
ALLOWED_COHORT_STATUSES = {
    "efficiency_included",
    "efficiency_excluded_governed",
    "routing_control_excluded",
}
ALLOWED_RECEIPT_STATUSES = {"required", "verification_not_applicable"}
REQUIRED_SCENARIO_FIELDS = {
    "id",
    "category",
    "scenario_type",
    "sanitized_prompt",
    "activation_status",
    "activation_reason",
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
def extract_base_required_helpers(raw_output: object) -> list[str]:
    """Extract only Base's structured pre-action required-helper contract."""
    if not isinstance(raw_output, dict):
        raise ValueError("Base required-helper output must be an object")
    required = raw_output.get("required_helpers_before_first_action")
    if not isinstance(required, list) or any(not _non_empty_string(item) for item in required):
        raise ValueError("Base required_helpers_before_first_action must be a string list")
    return list(dict.fromkeys(required))


def frozen_base_required_helper_output(root: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    """Derive Base helpers from immutable Base skill bytes, never candidate rules."""
    if scenario.get("category") == "routing_control":
        return {
            "source_contract_sha256": "not_applicable_routing_control",
            "required_helpers_before_first_action": [],
        }
    proc = subprocess.run(
        [
            "git",
            "show",
            f"{BASELINE_BASE_SHA}:codex/skills/delivery-harness-framework/SKILL.md",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ValueError(f"cannot read immutable Base helper contract: {proc.stderr.strip()}")
    skill = proc.stdout
    required_contract_markers = (
        "For complex or resumed work:",
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_requirements.py",
        "harness_report.py",
        "harness_agent_team.py",
        "harness_checkpoint.py",
    )
    missing = [marker for marker in required_contract_markers if marker not in skill]
    if missing:
        raise ValueError(f"immutable Base helper contract missing markers: {missing}")
    prompt = str(scenario.get("sanitized_prompt", "")).lower()
    helpers = ["harness_recover.py", "harness_env_probe.py"]
    if re.search(r"\b(?:resume|handoff|review|validation)\b", prompt):
        helpers.append("harness_report.py")
    if re.search(r"\b(?:remote|deploy(?:ment)?|release|destructive|irreversible)\b", prompt):
        helpers.append("harness_checkpoint.py")
    if re.search(r"\bmulti[-\s]+agent|multiple\s+agents\b", prompt):
        helpers.append("harness_agent_team.py")
    if "architecture" in prompt and "state-conflict" in prompt:
        helpers.append("harness_requirements.py")
    return {
        "source_contract_sha256": hashlib.sha256(skill.encode("utf-8")).hexdigest(),
        "source_contract": "immutable Base SKILL.md Helper Router and Startup Sequence",
        "required_helpers_before_first_action": helpers,
    }
BASELINE_BASE_SHA = "00818ae174f039899a2757ee4c67fcf9db1effa0"
BASELINE_PROVENANCE = {
    "base_sha": BASELINE_BASE_SHA,
    "oracle_kind": "frozen_measurement",
    "generic_skill_utf8_bytes_proxy": 32482,
    "generic_wrapper_utf8_bytes_proxy": 321,
    "generic_context_utf8_bytes_proxy": 32803,
    "captured_before_simplification": True,
}
_GENERIC_BASELINE_IDS = (
    "LIGHT-EXPLANATION",
    "LIGHT-BOUNDED-DOCS",
    "LIGHT-ONE-FILE-SAFE",
    "LIGHT-TRIVIAL-FORMAT",
    "STANDARD-LOCAL-FEATURE",
    "STANDARD-FAILING-TEST",
    "STANDARD-SCOPED-REFACTOR",
    "STANDARD-CLI-CHANGE",
    "STANDARD-LOCAL-UI",
    "GOVERNED-RESUMED-TASK",
    "GOVERNED-DIRTY-CONFLICT",
    "GOVERNED-EXTERNAL-CAPTURE",
    "GOVERNED-REMOTE-DEPLOY",
    "GOVERNED-MULTI-AGENT",
    "GOVERNED-ARCH-SOURCE-CONFLICT",
)
FROZEN_BASELINE_ORACLE = {
    **{
        scenario_id: {
            "route": "generic-activated",
            "injected_context_utf8_bytes_proxy": 32803,
            "verification_receipt_status": "not_observed",
        }
        for scenario_id in _GENERIC_BASELINE_IDS
    },
    "CONTROL-ORDINARY-CONTINUE": {
        "route": "continue-only",
        "injected_context_utf8_bytes_proxy": 0,
        "verification_receipt_status": "not_applicable_to_routing_control",
    },
    "CONTROL-SHIPQ-DELEGATION": {
        "route": "shipq-delegated",
        "injected_context_utf8_bytes_proxy": 41,
        "verification_receipt_status": "owned_by_project_adapter",
    },
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


def extract_acceptance_slice_map(plan_path: Path) -> dict[str, tuple[str, ...]]:
    text = plan_path.read_text(encoding="utf-8")
    marker = "## Acceptance Traceability\n"
    if marker not in text:
        return {}
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    result: dict[str, tuple[str, ...]] = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        slice_cell = re.sub(r"optional\s+\d+", "", cells[2], flags=re.IGNORECASE)
        slices = tuple(dict.fromkeys(re.findall(r"(?<!\d)[0-6](?!\d)", slice_cell)))
        for trace_id in re.findall(r"AC-\d{2}", cells[1]):
            result[trace_id] = slices
    return result


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

    for field in (
        "id",
        "category",
        "scenario_type",
        "sanitized_prompt",
        "activation_status",
        "cohort_status",
        "cwd_class",
        "expected_profile",
        "verification_receipt_status",
    ):
        if not _non_empty_string(scenario[field]):
            errors.append(f"{prefix}.{field} must be a non-empty string")
    category = scenario["category"]
    if _non_empty_string(category) and category not in {*MINIMUM_CATEGORY_COUNTS, "routing_control"}:
        errors.append(f"{prefix}.category is invalid: {category}")
    if _non_empty_string(scenario["cwd_class"]) and scenario["cwd_class"] not in ALLOWED_CWD_CLASSES:
        errors.append(f"{prefix}.cwd_class is invalid: {scenario['cwd_class']}")
    if _non_empty_string(scenario["cohort_status"]) and scenario["cohort_status"] not in ALLOWED_COHORT_STATUSES:
        errors.append(f"{prefix}.cohort_status is invalid: {scenario['cohort_status']}")
    if _non_empty_string(category) and category in MINIMUM_CATEGORY_COUNTS and scenario["expected_profile"] != category:
        errors.append(f"{prefix}.expected_profile must match category {category}")
    if category == "routing_control" and scenario["expected_profile"] != "not_applicable":
        errors.append(f"{prefix}.expected_profile must be not_applicable")
    if _non_empty_string(category) and category in {"light", "standard"}:
        if scenario["cohort_status"] != "efficiency_included":
            errors.append(f"{prefix}: light/standard scenarios must be efficiency_included")
        if scenario["activation_reason"] != "explicit_opt_in":
            errors.append(f"{prefix}: efficiency cohort requires explicit_opt_in activation_reason")
    elif category == "governed":
        if scenario["cohort_status"] != "efficiency_excluded_governed":
            errors.append(f"{prefix}: governed scenarios must be efficiency_excluded_governed")
        if scenario["activation_reason"] != "explicit_opt_in":
            errors.append(f"{prefix}: governed corpus scenarios must be explicit_opt_in")
    elif category == "routing_control":
        if scenario["cohort_status"] != "routing_control_excluded":
            errors.append(f"{prefix}: routing controls must be excluded from the efficiency cohort")
        if scenario["activation_reason"] is not None:
            errors.append(f"{prefix}.activation_reason must be null for routing controls")
    if scenario["activation_status"] == "explicitly_activated_generic":
        reason = scenario["activation_reason"]
        if reason not in {"explicit_opt_in", "compatibility_risk_trigger", "profile_hint"}:
            errors.append(f"{prefix}.activation_reason is invalid for an activated scenario")

    if category == "governed" and not _non_empty_string(scenario["escalation_signal"]):
        errors.append(f"{prefix}.escalation_signal must name the governed trigger")
    if _non_empty_string(category) and category in {"light", "standard"} and scenario["escalation_signal"] is not None:
        errors.append(f"{prefix}.escalation_signal must be explicit null when absent")

    valid_string_lists: dict[str, list[str]] = {}
    for field in (
        "mandatory_helpers",
        "forbidden_helpers",
        "required_output_fields",
        "baseline_mandatory_helpers",
    ):
        value = scenario[field]
        if not isinstance(value, list) or any(not _non_empty_string(item) for item in value):
            errors.append(f"{prefix}.{field} must be a string list")
        else:
            valid_string_lists[field] = value
    if set(valid_string_lists.get("mandatory_helpers", [])) & set(valid_string_lists.get("forbidden_helpers", [])):
        errors.append(f"{prefix} cannot require and forbid the same helper")
    if "required_output_fields" in valid_string_lists and not valid_string_lists["required_output_fields"]:
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
            if (
                not isinstance(check, dict)
                or not _non_empty_string(check.get("id"))
                or check.get("type") not in {"field_nonempty", "field_equals", "field_contains", "field_forbids"}
                or not _non_empty_string(check.get("path"))
            ):
                errors.append(f"{prefix}.result_acceptance_checks entries require executable id/type/path")
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
    if (
        _non_empty_string(scenario["verification_receipt_status"])
        and scenario["verification_receipt_status"] not in ALLOWED_RECEIPT_STATUSES
    ):
        errors.append(f"{prefix}.verification_receipt_status is invalid")
    return errors


def _test_callable_exists(root: Path, reference: object) -> bool:
    if not _non_empty_string(reference) or reference.count("::") != 1:
        return False
    relative_path, qualified_name = reference.split("::", 1)
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    if candidate.suffix != ".py" or not candidate.is_file():
        return False
    try:
        tree = ast.parse(candidate.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    parts = qualified_name.split(".")
    if not parts[-1].startswith("test_"):
        return False
    if len(parts) == 1:
        return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[0] for node in tree.body)
    if len(parts) == 2:
        class_name, method_name = parts
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return any(
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name
                    for item in node.body
                )
    return False


def _callable_exists(root: Path, reference: object) -> bool:
    if not _non_empty_string(reference) or reference.count("::") != 1:
        return False
    relative_path, qualified_name = reference.split("::", 1)
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    if candidate.suffix != ".py" or not candidate.is_file():
        return False
    try:
        tree = ast.parse(candidate.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    parts = qualified_name.split(".")
    nodes: list[ast.AST] = list(tree.body)
    for part in parts:
        match = next(
            (
                node
                for node in nodes
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == part
            ),
            None,
        )
        if match is None:
            return False
        nodes = list(match.body) if isinstance(match, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else []
    return True


def _producer_evidence_valid(
    producer_id: object,
    catalog_entry: object,
    artifact_payload: object,
    repo_root: Path | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not isinstance(producer_id, str) or not isinstance(catalog_entry, dict):
        return False, ["missing_producer_catalog_entry"]
    if not isinstance(artifact_payload, dict):
        return False, ["missing_producer_artifact"]
    record = artifact_payload.get("producer_evidence", {}).get(producer_id)
    if not isinstance(record, dict):
        return False, ["missing_producer_evidence"]
    evidence = record.get("evidence")
    digest = record.get("evidence_sha256")
    if not isinstance(evidence, dict) or digest != hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest():
        reasons.append("producer_evidence_digest_mismatch")
    expected_binding = {
        "producer_id": producer_id,
        "slice": catalog_entry.get("slice"),
        "callable": catalog_entry.get("callable"),
        "artifact": catalog_entry.get("artifact"),
        "artifact_schema": catalog_entry.get("artifact_schema"),
    }
    if record.get("binding") != expected_binding:
        reasons.append("producer_evidence_binding_mismatch")
    if isinstance(evidence, dict):
        assertions = evidence.get("assertion_count")
        passed = evidence.get("passed_assertion_count")
        if not isinstance(assertions, int) or assertions <= 0 or passed != assertions:
            reasons.append("producer_assertions_failed")
        if evidence.get("slice") != catalog_entry.get("slice"):
            reasons.append("producer_evidence_slice_mismatch")
        semantic_payload = {
            key: value
            for key, value in artifact_payload.items()
            if key != "producer_evidence"
        }
        semantic_sha = hashlib.sha256(
            json.dumps(
                semantic_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()
        if evidence.get("source_artifact_sha256") != semantic_sha:
            reasons.append("producer_source_artifact_digest_mismatch")
        expected_kind = {
            "0": "baseline_and_fixture_evidence",
            "1": "routing_contract_evidence",
            "2": "output_contract_evidence",
            "3": "surface_identity_evidence",
            "4": "paired_acceptance_evidence",
        }.get(str(catalog_entry.get("slice")))
        if evidence.get("kind") != expected_kind:
            reasons.append("producer_evidence_kind_mismatch")
        if isinstance(artifact_payload, dict):
            scenario_count = len(artifact_payload.get("observations", []))
            base_records = len(
                artifact_payload.get("base_expected_runtime_manifest", {}).get("records", [])
            )
            mirror_count = len(
                artifact_payload.get("promotion_candidate_manifest", {}).get(
                    "normative_mirror_hashes", {}
                )
            )
            expected_assertions = {
                "0": scenario_count + base_records,
                "1": scenario_count * 5,
                "2": scenario_count * 5,
                "3": mirror_count,
                "4": scenario_count * 10 + 5,
            }.get(str(catalog_entry.get("slice")))
            if assertions != expected_assertions or passed != expected_assertions:
                reasons.append("producer_assertion_total_mismatch")
        if producer_id == "PRODUCER-AC-16-S0-1":
            manifest = evidence.get("base_expected_runtime_manifest")
            if not isinstance(manifest, dict) or manifest.get("kind") != "base_expected_runtime_manifest" or "captured_at" in manifest:
                reasons.append("ac16_base_manifest_invalid")
        if producer_id == "PRODUCER-AC-16-S4-1":
            snapshot = evidence.get("current_runtime_snapshot")
            captured_at = snapshot.get("captured_at") if isinstance(snapshot, dict) else None
            try:
                captured_time = datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
            except ValueError:
                captured_time = None
            timestamp_bound = False
            if captured_time is not None and captured_time.tzinfo is not None:
                now = datetime.now(timezone.utc)
                timestamp_bound = now - timedelta(minutes=15) <= captured_time <= now + timedelta(minutes=2)
                root = repo_root or Path(__file__).resolve().parents[1]
                artifact_path = catalog_entry.get("artifact")
                if not timestamp_bound and _non_empty_string(artifact_path):
                    proc = subprocess.run(
                        ["git", "log", "-1", "--format=%aI", "--", str(artifact_path)],
                        cwd=root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    try:
                        committed_at = datetime.fromisoformat(proc.stdout.strip())
                    except ValueError:
                        committed_at = None
                    if committed_at is not None:
                        timestamp_bound = abs(committed_at - captured_time) <= timedelta(minutes=15)
            records = snapshot.get("records") if isinstance(snapshot, dict) else None
            aggregate = (
                hashlib.sha256(
                    json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
                ).hexdigest()
                if isinstance(records, list)
                else None
            )
            if (
                not isinstance(snapshot, dict)
                or snapshot.get("kind") != "current_runtime_snapshot"
                or not _non_empty_string(snapshot.get("captured_at"))
                or captured_time is None
                or captured_time.tzinfo is None
                or not timestamp_bound
                or snapshot.get("aggregate_sha256") != aggregate
                or evidence.get("changed_paths") != []
                or not isinstance(evidence.get("promotion_difference_paths"), list)
                or not evidence.get("promotion_difference_paths")
            ):
                reasons.append("ac16_live_runtime_evidence_invalid")
    return not reasons, reasons


def _load_catalog_artifact(corpus: object, repo_root: Path | None = None) -> dict[str, Any] | None:
    if not isinstance(corpus, dict):
        return None
    catalog = corpus.get("producer_catalog")
    if not isinstance(catalog, dict) or not catalog:
        return None
    artifact = next(iter(catalog.values())).get("artifact")
    if not _non_empty_string(artifact):
        return None
    root = repo_root or Path(__file__).resolve().parents[1]
    try:
        payload = json.loads((root / artifact).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def derive_trace_gates(
    corpus: object,
    artifact_payload: object | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    producer_gates: list[dict[str, Any]] = []
    acceptance_gates: dict[str, bool] = {}
    trace_map = corpus.get("acceptance_trace_map", {}) if isinstance(corpus, dict) else {}
    catalog = corpus.get("producer_catalog", {}) if isinstance(corpus, dict) else {}
    if not isinstance(trace_map, dict):
        trace_map = {}
    if not isinstance(catalog, dict):
        catalog = {}
    artifact = artifact_payload if artifact_payload is not None else _load_catalog_artifact(corpus, repo_root)
    for acceptance_id, trace in trace_map.items():
        trace_pass = True
        producers = trace.get("producers", []) if isinstance(trace, dict) else []
        if not isinstance(producers, list) or not producers:
            trace_pass = False
            producers = []
        for producer in producers:
            producer_id = producer.get("producer_id") if isinstance(producer, dict) else None
            status = producer.get("evidence_status", {}) if isinstance(producer, dict) else {}
            catalog_entry = catalog.get(producer_id) if isinstance(producer_id, str) else None
            reasons: list[str] = []
            if not isinstance(catalog_entry, dict):
                reasons.append("missing_producer_catalog_entry")
            elif str(catalog_entry.get("slice")) != str(producer.get("slice")):
                reasons.append("slice_mismatch")
            if not isinstance(status, dict) or status.get("state") != "completed":
                reasons.append("evidence_not_completed")
            if not _non_empty_string(status.get("evidence_id") if isinstance(status, dict) else None):
                reasons.append("missing_evidence_id")
            evidence_pass, evidence_reasons = _producer_evidence_valid(
                producer_id, catalog_entry, artifact, repo_root
            )
            if evidence_pass and isinstance(artifact, dict):
                evidence = artifact["producer_evidence"][producer_id]["evidence"]
                expected_assertion_ids = sorted(
                    [f"scenario:{item}" for item in trace.get("scenario_ids", [])]
                    + [f"test:{item}" for item in trace.get("test_ids", [])]
                )
                if (
                    evidence.get("acceptance_id") != acceptance_id
                    or evidence.get("registered_assertion_ids") != expected_assertion_ids
                ):
                    evidence_pass = False
                    evidence_reasons.append("producer_acceptance_binding_mismatch")
            if not evidence_pass:
                reasons.extend(evidence_reasons)
            passed = not reasons
            trace_pass = trace_pass and passed
            producer_gates.append(
                {
                    "acceptance_id": acceptance_id,
                    "producer_id": producer_id,
                    "gate_pass": passed,
                    "reasons": reasons,
                }
            )
        acceptance_gates[acceptance_id] = trace_pass
    return {
        "producer_gates": producer_gates,
        "acceptance_gates": acceptance_gates,
        "gate_pass": bool(acceptance_gates) and all(acceptance_gates.values()),
    }


def validate_corpus(
    corpus: object,
    contract_path: Path,
    *,
    validate_artifacts: bool = True,
) -> list[str]:
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
        if boundary.get("baseline_provenance") != BASELINE_PROVENANCE:
            errors.append("baseline provenance must match the frozen Base SHA oracle")

    scenarios = corpus.get("scenarios")
    if not isinstance(scenarios, list):
        return errors + ["scenarios must be a list"]
    for index, scenario in enumerate(scenarios):
        errors.extend(_validate_scenario(scenario, index))
    ids = [
        scenario.get("id")
        for scenario in scenarios
        if isinstance(scenario, dict) and _non_empty_string(scenario.get("id"))
    ]
    if len(ids) != len(set(ids)):
        errors.append("scenario IDs must be unique")
    counts = Counter(
        scenario.get("category")
        for scenario in scenarios
        if isinstance(scenario, dict)
        and _non_empty_string(scenario.get("category"))
        and scenario.get("category") in MINIMUM_CATEGORY_COUNTS
    )
    for category, minimum in MINIMUM_CATEGORY_COUNTS.items():
        if counts[category] < minimum:
            errors.append(f"at least {minimum} {category} scenarios are required")

    gate_oracle = corpus.get("authoritative_gate_oracle")
    governed_ids = {
        scenario.get("id")
        for scenario in scenarios
        if isinstance(scenario, dict) and scenario.get("category") == "governed"
    }
    if not isinstance(gate_oracle, dict) or set(gate_oracle) != governed_ids:
        errors.append("authoritative_gate_oracle must cover exactly every governed scenario")
    elif any(
        not isinstance(gates, list) or not gates or any(not _non_empty_string(gate) for gate in gates)
        for gates in gate_oracle.values()
    ):
        errors.append("authoritative_gate_oracle values must be non-empty string lists")

    contract_criteria = extract_acceptance_criteria(contract_path)
    plan_path = contract_path.with_name("2026-07-12-dhf-simplification-implementation-plan.md")
    slice_map = extract_acceptance_slice_map(plan_path)
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
    test_catalog = corpus.get("test_catalog")
    if not isinstance(test_catalog, dict):
        errors.append("test_catalog must map stable test IDs to callables")
        test_catalog = {}
    else:
        repo_root = contract_path.resolve().parents[2]
        for test_id, reference in test_catalog.items():
            if not _non_empty_string(test_id):
                errors.append("test_catalog IDs must be non-empty strings")
            elif not _test_callable_exists(repo_root, reference):
                errors.append(f"{test_id} does not resolve to a test callable: {reference}")
    producer_catalog = corpus.get("producer_catalog")
    producer_catalog_fields = {
        "producer_id", "slice", "callable", "artifact", "artifact_schema", "identity_fields"
    }
    if not isinstance(producer_catalog, dict):
        errors.append("producer_catalog must independently map producer IDs to evidence producers")
        producer_catalog = {}
    else:
        for producer_id, entry in producer_catalog.items():
            if not isinstance(entry, dict) or set(entry) != producer_catalog_fields:
                errors.append(f"{producer_id} producer_catalog fields must be exactly {sorted(producer_catalog_fields)}")
                continue
            if entry.get("producer_id") != producer_id:
                errors.append(f"{producer_id} producer_catalog embedded ID mismatch")
            if producer_id in test_catalog:
                errors.append(f"{producer_id} producer ID must be independent from test_catalog")
            if not _callable_exists(repo_root, entry.get("callable")):
                errors.append(f"{producer_id} producer callable does not resolve: {entry.get('callable')}")
            artifact = entry.get("artifact")
            artifact_path = repo_root / str(artifact)
            if not _non_empty_string(artifact) or Path(str(artifact)).is_absolute() or not artifact_path.is_file():
                errors.append(f"{producer_id} producer artifact must be an existing repo-relative file")
            if not _non_empty_string(entry.get("artifact_schema")):
                errors.append(f"{producer_id} artifact_schema must be non-empty")
            identity_fields = entry.get("identity_fields")
            if not isinstance(identity_fields, list) or not identity_fields or any(
                not _non_empty_string(field) for field in identity_fields
            ):
                errors.append(f"{producer_id} identity_fields must be a non-empty string list")
            if validate_artifacts and artifact_path.is_file() and artifact_path.suffix == ".json":
                try:
                    artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    errors.append(f"{producer_id} producer artifact is not valid JSON")
                else:
                    if artifact_payload.get("artifact_schema") != entry.get("artifact_schema"):
                        errors.append(f"{producer_id} producer artifact schema mismatch")
                    if isinstance(identity_fields, list):
                        missing_identity = [field for field in identity_fields if field not in artifact_payload]
                        if missing_identity:
                            errors.append(
                                f"{producer_id} producer artifact missing identity fields: "
                                + ", ".join(missing_identity)
                            )
                    evidence_pass, _ = _producer_evidence_valid(
                        producer_id, entry, artifact_payload, repo_root
                    )
                    if not evidence_pass:
                        errors.append(f"{producer_id} producer evidence binding mismatch")
    for index, criterion in enumerate(contract_criteria, 1):
        trace_id = f"AC-{index:02d}"
        trace = trace_map.get(trace_id)
        if not isinstance(trace, dict):
            continue
        required_trace_fields = {"criterion", "scenario_ids", "test_ids", "producers"}
        if set(trace) != required_trace_fields:
            errors.append(f"{trace_id} fields must be exactly {sorted(required_trace_fields)}")
        if trace.get("criterion") != criterion:
            errors.append(f"{trace_id} criterion text does not match the contract")
        scenario_ids = trace.get("scenario_ids")
        test_ids = trace.get("test_ids")
        if not isinstance(scenario_ids, list) or not isinstance(test_ids, list) or not (scenario_ids or test_ids):
            errors.append(f"{trace_id} must map to one or more scenario/test IDs")
            continue
        for scenario_id in scenario_ids:
            if not _non_empty_string(scenario_id) or scenario_id not in known_ids:
                errors.append(f"{trace_id} references unknown scenario ID: {scenario_id}")
        for test_id in test_ids:
            if not _non_empty_string(test_id) or test_id not in test_catalog:
                errors.append(f"{trace_id} references unknown test ID: {test_id}")
        producers = trace.get("producers")
        if not isinstance(producers, list) or not producers:
            errors.append(f"{trace_id} producers must be a non-empty list")
            continue
        producer_fields = {"slice", "producer_id", "fixture", "evidence_status"}
        observed_slices: list[str] = []
        for producer in producers:
            if not isinstance(producer, dict) or set(producer) != producer_fields:
                errors.append(f"{trace_id} producer fields must be exactly {sorted(producer_fields)}")
                continue
            slice_id = producer.get("slice")
            observed_slices.append(str(slice_id))
            producer_id = producer.get("producer_id")
            catalog_entry = producer_catalog.get(producer_id) if _non_empty_string(producer_id) else None
            if not isinstance(catalog_entry, dict):
                errors.append(f"{trace_id} producer_id must resolve through producer_catalog")
            elif str(catalog_entry.get("slice")) != str(slice_id):
                errors.append(f"{trace_id} producer slice does not match producer_catalog")
            fixture = producer.get("fixture")
            fixture_path = contract_path.resolve().parents[2] / str(fixture)
            if not _non_empty_string(fixture) or Path(str(fixture)).is_absolute() or not fixture_path.exists():
                errors.append(f"{trace_id} producer fixture must name an existing repo-relative evidence path")
            elif isinstance(catalog_entry, dict) and fixture != catalog_entry.get("artifact"):
                errors.append(f"{trace_id} producer fixture does not match producer_catalog artifact")
            evidence_status = producer.get("evidence_status")
            if (
                not isinstance(evidence_status, dict)
                or set(evidence_status) != {"state", "evidence_id"}
                or evidence_status.get("state") != "completed"
                or not _non_empty_string(evidence_status.get("evidence_id"))
            ):
                errors.append(f"{trace_id} producer gate requires completed evidence_status")
        if tuple(observed_slices) != slice_map.get(trace_id):
            errors.append(f"{trace_id} producer slices do not match the implementation plan")
    return errors


def _load_dispatcher(root: Path):
    path = root / "codex" / "hooks" / "dhf_preprompt.py"
    spec = importlib.util.spec_from_file_location("dhf_simplification_baseline_dispatcher", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import dispatcher: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _observed_candidate_contract(context: str) -> dict[str, Any]:
    empty = {
        "helpers": [],
        "escalation_signals": [],
        "required_output_fields": [],
        "authoritative_gates": [],
    }
    marker = "DHF_PROFILE_CONTRACT="
    for line in context.splitlines():
        if not line.startswith(marker):
            continue
        try:
            contract = json.loads(line.removeprefix(marker))
        except json.JSONDecodeError:
            return {"contract_observed": True, "contract_parse_valid": False, **empty}
        if not isinstance(contract, dict):
            return {"contract_observed": True, "contract_parse_valid": False, **empty}
        fields = {
            "helpers": contract.get("mandatory_helpers"),
            "escalation_signals": contract.get("escalation_signals", []),
            "required_output_fields": contract.get("required_output_fields", []),
            "authoritative_gates": contract.get("authoritative_gates", []),
        }
        if all(
            isinstance(values, list) and all(_non_empty_string(item) for item in values)
            for values in fields.values()
        ):
            return {"contract_observed": True, "contract_parse_valid": True, **fields}
        return {"contract_observed": True, "contract_parse_valid": False, **empty}
    return {"contract_observed": False, "contract_parse_valid": False, **empty}


def _init_dirty_git_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "sanitized@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Sanitized Fixture"], cwd=path, check=True)
    owned = path / "user-owned.txt"
    owned.write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "add", "user-owned.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=path, check=True)
    owned.write_text("user-owned-unsaved-change\n", encoding="utf-8")


def _dirty_snapshot(path: Path) -> dict[str, Any]:
    status = subprocess.run(
        ["git", "status", "--short"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    content = (path / "user-owned.txt").read_bytes()
    return {"status": status, "content_sha256": hashlib.sha256(content).hexdigest()}


def _measure_dispatcher(
    corpus: dict[str, Any], root: Path, *, simplified_profiles: bool
) -> list[dict[str, Any]]:
    module = _load_dispatcher(root)
    module.SIMPLIFIED_PROFILES_ENABLED = simplified_profiles
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        generic_root = temp_root / "GenericRepo"
        shipq_root = temp_root / "ShipQ"
        _init_dirty_git_repo(generic_root)
        _init_dirty_git_repo(shipq_root)
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
            dirty_before = _dirty_snapshot(cwd_by_class[scenario["cwd_class"]])
            response, route = module.route_response(payload)
            context = response.get("hookSpecificOutput", {}).get("additionalContext", "")
            dirty_after = _dirty_snapshot(cwd_by_class[scenario["cwd_class"]])
            observed_contract = (
                _observed_candidate_contract(context)
                if simplified_profiles
                else {
                    "contract_observed": False,
                    "contract_parse_valid": False,
                    "helpers": [],
                    "escalation_signals": [],
                    "required_output_fields": [],
                    "authoritative_gates": [],
                }
            )
            observed_helpers = observed_contract["helpers"]
            selected_profile = route.split(":")[1] if route.startswith("generic-activated:") else None
            if selected_profile == "legacy":
                selected_profile = None
                route = "generic-activated"
            measurements.append(
                {
                    "id": scenario["id"],
                    "route": route,
                    "injected_context_utf8_bytes_proxy": len(context.encode("utf-8")),
                    "mandatory_helper_count": (
                        len(observed_helpers)
                        if simplified_profiles
                        else len(
                            extract_base_required_helpers(
                                frozen_base_required_helper_output(root, scenario)
                            )
                        )
                    ),
                    "verification_receipt_status": scenario["baseline_measurement"]["verification_receipt_status"],
                    "selected_profile": selected_profile,
                    "observed_mandatory_helpers": observed_helpers,
                    "escalation_signals": observed_contract["escalation_signals"],
                    "observed_required_output_fields": observed_contract["required_output_fields"],
                    "observed_authoritative_gates": observed_contract["authoritative_gates"],
                    "additional_context": context,
                    "dirty_before": dirty_before,
                    "dirty_after": dirty_after,
                    "contract_observed": observed_contract["contract_observed"],
                    "contract_parse_valid": observed_contract["contract_parse_valid"],
                }
            )
        return measurements


def measure_baseline(corpus: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    measurements: list[dict[str, Any]] = []
    for scenario in corpus["scenarios"]:
        scenario_id = scenario["id"]
        frozen = FROZEN_BASELINE_ORACLE[scenario_id]
        measurements.append(
            {
                "id": scenario_id,
                "route": frozen["route"],
                "injected_context_utf8_bytes_proxy": frozen["injected_context_utf8_bytes_proxy"],
                "mandatory_helper_count": len(
                    extract_base_required_helpers(
                        frozen_base_required_helper_output(root, scenario)
                    )
                ),
                "verification_receipt_status": frozen["verification_receipt_status"],
                "selected_profile": None,
                "observed_mandatory_helpers": [],
                "escalation_signals": [],
                "observed_required_output_fields": [],
                "observed_authoritative_gates": [],
                "contract_observed": False,
                "contract_parse_valid": False,
            }
        )
    return measurements


def measure_candidate(corpus: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    return _measure_dispatcher(corpus, root, simplified_profiles=True)


def validate_candidate_measurements(
    corpus: dict[str, Any],
    root: Path,
    measurements: list[dict[str, Any]] | None = None,
) -> list[str]:
    actual = measurements if measurements is not None else measure_candidate(corpus, root)
    actual_by_id = {item.get("id"): item for item in actual if isinstance(item, dict)}
    errors: list[str] = []
    for scenario in corpus["scenarios"]:
        scenario_id = scenario["id"]
        measured = actual_by_id.get(scenario_id)
        if measured is None:
            errors.append(f"{scenario_id} missing candidate measurement")
            continue
        if measured.get("selected_profile") is not None:
            if not measured.get("contract_observed"):
                errors.append(f"{scenario_id} candidate contract missing")
            elif not measured.get("contract_parse_valid"):
                errors.append(f"{scenario_id} candidate contract invalid")
        expected_helpers = scenario["mandatory_helpers"]
        observed_helpers = measured.get("observed_mandatory_helpers")
        if observed_helpers != expected_helpers:
            errors.append(
                f"{scenario_id} candidate helper mismatch: {observed_helpers} != {expected_helpers}"
            )
        if measured.get("mandatory_helper_count") != len(observed_helpers or []):
            errors.append(f"{scenario_id} candidate helper count does not match observed helpers")
    return errors


def validate_baseline_measurements(corpus: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    actual_by_id = {item["id"]: item for item in measure_baseline(corpus, root)}
    for scenario in corpus["scenarios"]:
        expected = scenario["baseline_measurement"]
        actual = actual_by_id[scenario["id"]]
        oracle_helpers = extract_base_required_helpers(
            frozen_base_required_helper_output(root, scenario)
        )
        if scenario["baseline_mandatory_helpers"] != oracle_helpers:
            errors.append(
                f"{scenario['id']} canonical helper oracle mismatch: "
                f"{scenario['baseline_mandatory_helpers']} != {oracle_helpers}"
            )
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
        if expected["verification_receipt_status"] != actual["verification_receipt_status"]:
            errors.append(
                f"{scenario['id']} verification-receipt status mismatch: "
                f"{expected['verification_receipt_status']} != {actual['verification_receipt_status']}"
            )
    return errors


def summary(corpus: dict[str, Any]) -> dict[str, Any]:
    counts = Counter(
        scenario["category"]
        for scenario in corpus["scenarios"]
        if scenario["category"] in MINIMUM_CATEGORY_COUNTS
    )
    trace_gates = derive_trace_gates(corpus)
    return {
        "valid": True,
        **trace_gates,
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
        if args.json:
            print(json.dumps({"valid": False, **derive_trace_gates(corpus), "errors": errors}, ensure_ascii=False, sort_keys=True))
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
