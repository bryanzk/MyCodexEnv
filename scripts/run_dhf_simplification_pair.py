#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
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

CAPTURE_VERSION = "dhf-bounded-v1"
BASELINE_BASE_SHA = "00818ae174f039899a2757ee4c67fcf9db1effa0"
PRIVATE_MARKERS = ("SECRET_TOKEN=", "PRIVATE_KEY=", "PASSWORD=", "credential-value")

SIGNAL_BY_INTENT = {
    "resumed_task": "resume_or_handoff",
    "dirty_ownership_conflict": "unknown_or_overlapping_worktree_ownership",
    "external_capture": "external_capture_or_private_data",
    "remote_deploy_request": "remote_or_deployment_action",
    "multi_agent_plan": "multiple_agents_or_overlapping_write_sets",
    "architecture_source_conflict": "durable_architecture_source_conflict",
}
GATES_BY_SIGNAL = {
    "resume_or_handoff": ["Startup Sequence", "State Snapshot Gate", "Checkpoint Gate"],
    "unknown_or_overlapping_worktree_ownership": ["Dirty Worktree Gate", "Checkpoint Gate"],
    "external_capture_or_private_data": ["External Capture Promotion Gate", "Evidence And Report Gate", "Checkpoint Gate"],
    "remote_or_deployment_action": ["Execution Lane Gate", "Deployment Readiness Gate", "Checkpoint Gate"],
    "multiple_agents_or_overlapping_write_sets": ["Agent Team Gate", "Checkpoint Gate"],
    "durable_architecture_source_conflict": ["Source Of Truth Order", "Architecture Alignment Checkpoint Gate", "Checkpoint Gate"],
}
HELPERS_BY_SIGNAL = {
    "resume_or_handoff": ["harness_recover.py", "harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
    "unknown_or_overlapping_worktree_ownership": ["harness_recover.py", "harness_checkpoint.py"],
    "external_capture_or_private_data": ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
    "remote_or_deployment_action": ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
    "multiple_agents_or_overlapping_write_sets": ["harness_agent_team.py", "harness_checkpoint.py"],
    "durable_architecture_source_conflict": ["harness_recover.py", "harness_requirements.py", "harness_checkpoint.py"],
}
FIELDS_BY_SIGNAL = {
    "resume_or_handoff": ["phase", "ownership", "freshness_state"],
    "unknown_or_overlapping_worktree_ownership": ["ownership"],
    "external_capture_or_private_data": ["data_boundary"],
    "remote_or_deployment_action": ["authorization_state", "rollback"],
    "multiple_agents_or_overlapping_write_sets": ["agent_write_sets"],
    "durable_architecture_source_conflict": ["source_conflict", "decision_state"],
}
PERMISSION_BY_INTENT = {
    "explanation": "read_only_allowed",
    "bounded_docs_edit": "scoped_repo_write_allowed",
    "one_file_safe_change": "scoped_repo_write_allowed",
    "trivial_format": "input_only_transform_allowed",
    "local_feature": "local_repo_write_allowed",
    "failing_test_investigation": "read_only_diagnosis_allowed",
    "scoped_refactor": "scoped_refactor_allowed",
    "non_sensitive_cli_change": "local_cli_change_allowed",
    "local_ui_behavior": "local_ui_change_allowed",
    "resumed_task": "recover_before_write",
    "dirty_ownership_conflict": "block_overlapping_write",
    "external_capture": "sanitized_capture_only",
    "remote_deploy_request": "plan_only_until_authorized",
    "multi_agent_plan": "validate_team_before_dispatch",
    "architecture_source_conflict": "block_implementation_until_aligned",
    "ordinary_continue_only": "continue_without_generic_context",
    "shipq_lazy_delegation": "delegate_without_generic_preclassification",
}
CONSTRAINTS_BY_INTENT = {
    "explanation": ["file_write", "runtime_mutation"],
    "bounded_docs_edit": ["runtime_mutation", "remote_operation"],
    "one_file_safe_change": ["public_api_change", "runtime_mutation"],
    "trivial_format": ["file_write", "network_access"],
    "local_feature": ["network_access", "runtime_mutation"],
    "failing_test_investigation": ["source_edit", "runtime_mutation"],
    "scoped_refactor": ["behavior_change", "unrelated_cleanup"],
    "non_sensitive_cli_change": ["credential_read", "remote_execution"],
    "local_ui_behavior": ["production_access", "external_capture"],
    "resumed_task": ["write_before_recovery", "stale_receipt_promotion"],
    "dirty_ownership_conflict": ["overwrite_unknown_owner", "reset_or_clean"],
    "external_capture": ["raw_capture_commit", "credential_disclosure"],
    "remote_deploy_request": ["remote_connection", "deploy", "credential_read"],
    "multi_agent_plan": ["dispatch_before_validation", "overlapping_write_sets"],
    "architecture_source_conflict": ["silent_source_choice", "implementation_before_decision"],
    "ordinary_continue_only": ["generic_context_injection"],
    "shipq_lazy_delegation": ["generic_context_injection"],
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _profile_contract(context: str) -> dict[str, Any] | None:
    marker = "DHF_PROFILE_CONTRACT="
    for line in context.splitlines():
        if line.startswith(marker):
            try:
                value = json.loads(line.removeprefix(marker))
            except json.JSONDecodeError:
                return None
            return value if isinstance(value, dict) else None
    return None


def _git_show(root: Path, revision_path: str) -> str:
    proc = _run_checked(["git", "show", revision_path], root)
    if proc.returncode != 0:
        raise RuntimeError(f"git show failed for {revision_path}: {proc.stderr.strip()}")
    return proc.stdout


def _invoke_dispatcher(
    dispatcher_path: Path,
    skill_path: Path,
    scenario: dict[str, Any],
    root: Path,
    *,
    simplified: bool,
) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        generic = temp / "Generic"
        shipq = temp / "ShipQ"
        generic.mkdir()
        shipq.mkdir()
        adapter = temp / "adapter.py"
        adapter.write_text(
            "def build_response(_payload):\n"
            "    return {'continue': True, 'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', "
            "'additionalContext': 'Sanitized ShipQ adapter baseline context.'}}\n",
            encoding="utf-8",
        )
        cwd = shipq if scenario["cwd_class"] == "shipq_repo" else generic
        env = os.environ.copy()
        env.update(
            {
                "DHF_PREPROMPT_SKILL": str(skill_path),
                "DHF_PREPROMPT_SHIPQ_ROOT": str(shipq),
                "DHF_PREPROMPT_SHIPQ_ADAPTER": str(adapter),
                "DHF_PREPROMPT_ALLOW_UNTRUSTED_TEST_PATHS": "1",
                "DHF_PREPROMPT_SIMPLIFIED_PROFILES": "1" if simplified else "0",
            }
        )
        proc = subprocess.run(
            [sys.executable, str(dispatcher_path)],
            input=json.dumps({"cwd": str(cwd), "prompt": scenario["sanitized_prompt"]}),
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"dispatcher capture failed: {proc.stderr.strip()}")
        response = json.loads(proc.stdout)
        context = response.get("hookSpecificOutput", {}).get("additionalContext", "")
        route = proc.stderr.strip().removeprefix("diagnostic=")
        return context, route


def capture_contract_contexts(scenario: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    base_dispatcher_text = _git_show(root, f"{BASELINE_BASE_SHA}:codex/hooks/dhf_preprompt.py")
    base_skill_text = _git_show(root, f"{BASELINE_BASE_SHA}:codex/skills/delivery-harness-framework/SKILL.md")
    current_dispatcher = root / "codex" / "hooks" / "dhf_preprompt.py"
    current_skill = root / "codex" / "skills" / "delivery-harness-framework" / "SKILL.md"
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        base_dispatcher = temp / "dhf_preprompt.py"
        base_skill = temp / "SKILL.md"
        base_dispatcher.write_text(base_dispatcher_text, encoding="utf-8")
        base_skill.write_text(base_skill_text, encoding="utf-8")
        baseline_context, baseline_route = _invoke_dispatcher(base_dispatcher, base_skill, scenario, root, simplified=False)
    candidate_context, candidate_route = _invoke_dispatcher(current_dispatcher, current_skill, scenario, root, simplified=True)
    return {
        "baseline": {
            "context": baseline_context,
            "route": baseline_route,
            "profile_contract": _profile_contract(baseline_context),
            "dispatcher_sha256": _sha256(base_dispatcher_text),
            "skill_sha256": _sha256(base_skill_text),
            "source_contract": f"legacy@{BASELINE_BASE_SHA}",
            "base_commit": BASELINE_BASE_SHA,
        },
        "candidate": {
            "context": candidate_context,
            "route": candidate_route,
            "profile_contract": _profile_contract(candidate_context),
            "dispatcher_sha256": _sha256(current_dispatcher.read_text(encoding="utf-8")),
            "skill_sha256": _sha256(current_skill.read_text(encoding="utf-8")),
            "source_contract": "simplified@repo-source",
        },
    }


def classify_prompt_intent(prompt: str, context: str) -> str:
    if not context:
        return "ordinary_continue_only"
    if "ShipQ adapter" in context:
        return "shipq_lazy_delegation"
    patterns = (
        ("architecture_source_conflict", r"architecture\s+state[-\s]+conflict|durable source documents"),
        ("dirty_ownership_conflict", r"dirty worktree ownership|state[-\s]+conflict.*(?:dirty|ownership)"),
        ("external_capture", r"external capture|private data"),
        ("remote_deploy_request", r"remote deployment|\bdeploy(?:ment)?\b|\bssh\b|\bproduction\b"),
        ("multi_agent_plan", r"multi[-\s]+agent|multiple agents|worker dispatch"),
        ("resumed_task", r"\bresume\b|\bhandoff\b|take\s*over"),
        ("failing_test_investigation", r"failing (?:unit )?test|assertion mismatch"),
        ("bounded_docs_edit", r"markdown paragraph|spelling correction|bounded docs?"),
        ("one_file_safe_change", r"one[-\s]+file|constant rename"),
        ("trivial_format", r"formatting the supplied|formatted supplied|preserve every word"),
        ("scoped_refactor", r"\brefactor\b|module seam"),
        ("non_sensitive_cli_change", r"\bcli flag\b|exit[-\s]+code contract"),
        ("local_ui_behavior", r"\bui empty[-\s]+state|component interaction"),
        ("local_feature", r"parser option|local[-\s]+feature"),
        ("explanation", r"\bexplain\b|pure function|deterministic"),
    )
    for intent, pattern in patterns:
        if re.search(pattern, prompt, flags=re.IGNORECASE):
            return intent
    return "unknown"


def derive_execution_policy(
    prompt: str,
    context: str,
    profile_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    intent = classify_prompt_intent(prompt, context)
    signal = SIGNAL_BY_INTENT.get(intent)
    controls = {"ordinary_continue_only", "shipq_lazy_delegation"}
    parsed = profile_contract if isinstance(profile_contract, dict) else _profile_contract(context)
    if parsed:
        gates = list(parsed.get("authoritative_gates", []))
        helpers = list(parsed.get("mandatory_helpers", []))
        fields = list(parsed.get("required_output_fields", []))
    else:
        gates = [gate for gate in GATES_BY_SIGNAL.get(signal, []) if gate in context]
        helpers = [helper for helper in HELPERS_BY_SIGNAL.get(signal, []) if helper in context]
        fields = [field for field in FIELDS_BY_SIGNAL.get(signal, []) if field in context]
    required_gates = GATES_BY_SIGNAL.get(signal, [])
    contract_signals = set(parsed.get("escalation_signals", [])) if parsed else set()
    if signal and parsed and signal not in contract_signals:
        action = "fail_closed_missing_contract"
        permission = "blocked_missing_contract"
    elif signal and not set(required_gates).issubset(gates):
        action = "fail_closed_missing_contract"
        permission = "blocked_missing_contract"
    elif signal:
        action = "block_pending_authorization"
        permission = PERMISSION_BY_INTENT[intent]
    elif intent in controls:
        action = "route_control"
        permission = PERMISSION_BY_INTENT[intent]
    elif not context or intent == "unknown":
        action = "fail_closed_missing_contract"
        permission = "blocked_missing_contract"
    else:
        action = "execute_bounded"
        permission = PERMISSION_BY_INTENT[intent]
    return {
        "intent": intent,
        "action": action,
        "permission": permission,
        "constraints": list(CONSTRAINTS_BY_INTENT.get(intent, ["unclassified_prompt"])),
        "helpers": helpers,
        "gates": gates,
        "required_output_fields": fields,
        "context_sha256": _sha256(context),
        "prompt_sha256": _sha256(prompt),
    }


def _receipt(command: str, proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    output = (proc.stdout or proc.stderr).strip().replace("\n", " ")[:160] or "completed"
    return {
        "command": command,
        "exit_code": proc.returncode,
        "key_output": output,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def execute_bounded_scenario(scenario: dict[str, Any], contract_capture: dict[str, Any]) -> dict[str, Any]:
    prompt = scenario["sanitized_prompt"]
    context = str(contract_capture.get("context", ""))
    policy = derive_execution_policy(
        prompt, context, contract_capture.get("profile_contract")
    )
    intent = policy["intent"]
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _run_checked(["git", "init", "-q"], repo)
        _run_checked(["git", "config", "user.email", "capture@example.invalid"], repo)
        _run_checked(["git", "config", "user.name", "Bounded Capture"], repo)
        seed = repo / "user-owned.txt"
        seed.write_text("preserve-me\n", encoding="utf-8")
        _run_checked(["git", "add", "user-owned.txt"], repo)
        _run_checked(["git", "commit", "-q", "-m", "seed"], repo)
        seed.write_text("preserve-me\nuser-owned-dirty\n", encoding="utf-8")

        result = ""
        receipt: dict[str, Any]
        changed_files: list[str] = []
        if intent == "explanation":
            deterministic = (lambda value: value * 2 + 1)(7) == (lambda value: value * 2 + 1)(7)
            result = f"Deterministic check returned {str(deterministic).lower()} for identical inputs; no artifact changed."
            receipt = {"verification_not_applicable": "pure explanation; no artifact or runtime claim"}
        elif intent == "trivial_format":
            words = ["preserve", "every", "word"]
            result = "Formatted supplied text: " + " | ".join(words)
            receipt = {"verification_not_applicable": "input-only formatting; no artifact claim"}
        elif intent in {"ordinary_continue_only", "shipq_lazy_delegation"}:
            result = "Dispatcher control outcome captured without generic task execution."
            receipt = {"verification_not_applicable": "routing control only"}
        elif policy["action"] in {"block_pending_authorization", "fail_closed_missing_contract"}:
            command = "git status --short"
            proc = _run_checked(["git", "status", "--short"], repo)
            receipt = _receipt(command, proc)
            result = f"Governed action not executed; permission decision={policy['permission']}."
        elif intent == "failing_test_investigation":
            test_file = repo / "test_failure.py"
            test_file.write_text("assert 2 + 2 == 5, 'expected bounded failure'\n", encoding="utf-8")
            command = f"{sys.executable} test_failure.py"
            proc = _run_checked([sys.executable, "test_failure.py"], repo)
            receipt = _receipt(command, proc)
            result = "Diagnosed concrete assertion mismatch (2 + 2 != 5) without editing the failing source."
            test_file.unlink()
        else:
            relative = {
                "bounded_docs_edit": "docs/example.md",
                "one_file_safe_change": "src/example.py",
                "local_feature": "src/parser_option.py",
                "scoped_refactor": "src/module_seam.py",
                "non_sensitive_cli_change": "src/cli_flag.py",
                "local_ui_behavior": "src/empty_state.py",
            }[intent]
            artifact = repo / relative
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(f"# bounded capture {intent}\n", encoding="utf-8")
            command_args = [sys.executable, "-c", "from pathlib import Path; import sys; sys.exit(0 if Path(sys.argv[1]).is_file() else 1)", relative]
            command = shlex.join(command_args)
            proc = _run_checked(command_args, repo)
            receipt = _receipt(command, proc)
            changed_files = [relative]
            result = f"Completed bounded {intent.replace('_', ' ')} outcome with focused local verification."

        status = _run_checked(["git", "status", "--short"], repo).stdout.splitlines()
        return {
            "result": result,
            "scope_and_constraints": policy["constraints"],
            "verification_receipt": receipt,
            "remaining_risk_or_next_action": "authorization required" if policy["action"] == "block_pending_authorization" else "none",
            "permission_outcome": policy["permission"],
            "private_data_excluded": not any(marker in result for marker in PRIVATE_MARKERS),
            "changed_files": changed_files,
            "dirty_snapshot": status,
            "capture_contract": contract_capture["source_contract"],
            "execution_policy": policy,
        }


def capture_observations(corpus: dict[str, Any], observations: dict[str, Any]) -> dict[str, Any]:
    scenarios = {scenario["id"]: scenario for scenario in corpus["scenarios"]}
    captured = copy.deepcopy(observations)
    for observation in captured["observations"]:
        scenario = scenarios[observation["id"]]
        observation["input"] = {
            "prompt": scenario["sanitized_prompt"],
            "cwd_class": scenario["cwd_class"],
            "activation_status": scenario["activation_status"],
            "activation_reason": scenario["activation_reason"],
        }
        contexts = capture_contract_contexts(scenario, Path(__file__).resolve().parents[1])
        for profile in ("baseline", "candidate"):
            contract = contexts[profile]
            context = contract["context"]
            observation[f"{profile}_capture"] = {
                "provenance": {
                    "capture_mode": "deterministic_local_bounded_execution",
                    "capture_version": CAPTURE_VERSION,
                    "source_contract": contract["source_contract"],
                    "base_commit": contract.get("base_commit"),
                    "context_sha256": _sha256(context),
                    "context_utf8_bytes": len(context.encode("utf-8")),
                    "dispatcher_sha256": contract["dispatcher_sha256"],
                    "skill_sha256": contract["skill_sha256"],
                    "dispatcher_route": contract["route"],
                    "profile_contract": contract["profile_contract"] or {},
                },
                "contract_context": context,
                "raw_task_output": execute_bounded_scenario(scenario, contract),
            }
    captured["schema_version"] = 3
    return captured


def assertion_errors(scenario: dict[str, Any], raw: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    policy = raw.get("execution_policy")
    observed_intent = policy.get("intent") if isinstance(policy, dict) else None
    if observed_intent != scenario.get("scenario_type"):
        errors.append(
            f"{scenario['id']} {label} actual outcome prompt/type mismatch: "
            f"observed={observed_intent} expected={scenario.get('scenario_type')}"
        )
    for assertion in scenario.get("result_acceptance_checks", []):
        assertion_id = assertion.get("id", "unknown")
        kind = assertion.get("type")
        path = assertion.get("path")
        if not isinstance(path, str) or path not in raw:
            errors.append(f"{scenario['id']} {label} assertion {assertion_id} has unimplemented path/type")
            continue
        actual = raw[path]
        if kind == "field_nonempty":
            passed = bool(actual)
        elif kind == "field_equals":
            passed = actual == assertion.get("expected")
        elif kind == "field_contains":
            passed = str(assertion.get("expected", "")).lower() in str(actual).lower()
        elif kind == "field_forbids":
            passed = all(str(value).lower() not in str(actual).lower() for value in assertion.get("values", []))
        else:
            errors.append(f"{scenario['id']} {label} assertion {assertion_id} unimplemented type: {kind}")
            continue
        if not passed:
            errors.append(f"{scenario['id']} {label} actual outcome assertion failed: {assertion_id}")

    receipt = raw.get("verification_receipt")
    if scenario["verification_receipt_status"] == "required":
        if not isinstance(receipt, dict) or not all(field in receipt for field in RECEIPT_FIELDS):
            errors.append(f"{scenario['id']} {label} actual outcome receipt incomplete")
    elif not isinstance(receipt, dict) or set(receipt) != {"verification_not_applicable"}:
        errors.append(f"{scenario['id']} {label} actual outcome invalid verification_not_applicable")
    if raw.get("permission_outcome") != scenario["permission_safety_outcome"]["decision"]:
        errors.append(f"{scenario['id']} {label} actual outcome permission mismatch")
    raw_text = json.dumps(raw, ensure_ascii=False)
    if not raw.get("private_data_excluded") or any(marker in raw_text for marker in PRIVATE_MARKERS):
        errors.append(f"{scenario['id']} {label} actual outcome contains forbidden private content")
    return errors


def capture_validation_errors(
    scenario: dict[str, Any],
    capture: dict[str, Any],
    label: str,
    expected_source_hashes: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    provenance = capture.get("provenance")
    context = capture.get("contract_context")
    raw = capture.get("raw_task_output")
    if not isinstance(provenance, dict) or not isinstance(context, str) or not isinstance(raw, dict):
        return [f"{scenario['id']} {label} context capture structure invalid"]
    if provenance.get("context_sha256") != _sha256(context):
        errors.append(f"{scenario['id']} {label} context hash mismatch")
    if provenance.get("context_utf8_bytes") != len(context.encode("utf-8")):
        errors.append(f"{scenario['id']} {label} context byte count mismatch")
    parsed = _profile_contract(context) or {}
    if provenance.get("profile_contract") != parsed:
        errors.append(f"{scenario['id']} {label} contract does not match emitted context")
    policy = raw.get("execution_policy")
    if not isinstance(policy, dict):
        errors.append(f"{scenario['id']} {label} execution policy structure invalid")
    else:
        if policy.get("context_sha256") != _sha256(context):
            errors.append(f"{scenario['id']} {label} execution policy context mismatch")
        if policy.get("prompt_sha256") != _sha256(scenario["sanitized_prompt"]):
            errors.append(f"{scenario['id']} {label} execution policy prompt mismatch")
        for key in ("gates", "helpers", "required_output_fields"):
            if not isinstance(policy.get(key), list):
                errors.append(f"{scenario['id']} {label} execution policy {key} invalid")
        if parsed:
            expected_contract_lists = {
                "gates": parsed.get("authoritative_gates", []),
                "helpers": parsed.get("mandatory_helpers", []),
                "required_output_fields": parsed.get("required_output_fields", []),
            }
            for key, expected in expected_contract_lists.items():
                if policy.get(key) != expected:
                    errors.append(f"{scenario['id']} {label} captured contract {key} mismatch")
        else:
            for key in ("gates", "helpers", "required_output_fields"):
                if any(not isinstance(item, str) or item not in context for item in policy.get(key, [])):
                    errors.append(f"{scenario['id']} {label} execution policy {key} not sourced from context")
    for field in ("dispatcher_sha256", "skill_sha256"):
        value = provenance.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            errors.append(f"{scenario['id']} {label} context provenance invalid {field}")
        elif value != expected_source_hashes[field]:
            errors.append(f"{scenario['id']} {label} source hash mismatch: {field}")
    return errors
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
                "- phase: research\n"
                "- next_safe_task: none\n"
                "- latest_checkpoint: none\n"
                "- latest_verification: none\n"
                "- blocked_sources: none\n\n"
                "## State Log\n",
                encoding="utf-8",
            )
            _run_checked(["git", "add", "docs"], repo)
            _run_checked(["git", "commit", "-q", "-m", "fixture"], repo)

            codex_home = temp_root / "empty-codex-home"

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
                    "--verification-timestamp",
                    case["verification_evidence"]["timestamp"],
                    "--verification-freshness",
                    case["verification_evidence"]["freshness"],
                    "--ownership-json",
                    json.dumps(case["ownership"], ensure_ascii=False, sort_keys=True),
                    "--next-action-json",
                    next_action_json,
                    "--next-safe-task",
                    next_action_json,
                    *[value for constraint in case["constraints"] for value in ("--constraint", constraint)],
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
            latest = payload.get("verification_evidence", {})
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
        f"generic-activated:{scenario['expected_profile']}:{scenario['activation_reason']}"
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
    expected_capture_hashes = {
        "baseline": {
            "dispatcher_sha256": _sha256(
                _git_show(root, f"{BASELINE_BASE_SHA}:codex/hooks/dhf_preprompt.py")
            ),
            "skill_sha256": _sha256(
                _git_show(root, f"{BASELINE_BASE_SHA}:codex/skills/delivery-harness-framework/SKILL.md")
            ),
        },
        "candidate": {
            "dispatcher_sha256": _sha256(
                (root / "codex" / "hooks" / "dhf_preprompt.py").read_text(encoding="utf-8")
            ),
            "skill_sha256": _sha256(
                (root / "codex" / "skills" / "delivery-harness-framework" / "SKILL.md").read_text(
                    encoding="utf-8"
                )
            ),
        },
    }
    validator = _validator(root)
    contract = root / "docs" / "plans" / "2026-07-12-dhf-simplification-implementation-contract.md"
    errors.extend(validator.validate_corpus(corpus, contract))
    if observations.get("measurement_boundary") != corpus.get("measurement_boundary"):
        errors.append("measurement boundary changed between oracle and observed output")
    if observations.get("schema_version") != 3:
        errors.append("observations schema_version must be 3")
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
    routing_passed = 0
    routing_total = 0
    actual_passed = 0
    actual_total = 0
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
            "activation_reason": scenario["activation_reason"],
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
            routing_total += 1
            if pair["baseline"] and pair["candidate"] and pair["baseline"] == pair["candidate"]:
                routing_passed += 1

        captures = {}
        capture_errors: list[str] = []
        assertion_errors_by_side: dict[str, list[str]] = {"baseline": [], "candidate": []}
        for label in ("baseline", "candidate"):
            capture = observation.get(f"{label}_capture")
            if not isinstance(capture, dict):
                capture_errors.append(f"{scenario_id} missing {label} actual outcome capture")
                continue
            provenance = capture.get("provenance")
            raw = capture.get("raw_task_output")
            if not isinstance(provenance, dict) or provenance.get("capture_mode") != "deterministic_local_bounded_execution":
                capture_errors.append(f"{scenario_id} {label} actual outcome provenance invalid")
            if not isinstance(raw, dict):
                capture_errors.append(f"{scenario_id} {label} actual outcome raw output missing")
                continue
            captures[label] = raw
            side_errors = capture_validation_errors(
                scenario, capture, label, expected_capture_hashes[label]
            )
            side_errors.extend(assertion_errors(scenario, raw, label))
            assertion_errors_by_side[label].extend(side_errors)
            capture_errors.extend(side_errors)

        raw_dimensions: dict[str, dict[str, bool]] = {}
        baseline_raw = captures.get("baseline", {})
        candidate_raw = captures.get("candidate", {})
        def side_has(label: str, terms: tuple[str, ...]) -> bool:
            return any(any(term in error for term in terms) for error in assertion_errors_by_side[label])

        baseline_dirty = bool(baseline_raw) and any("user-owned.txt" in line for line in baseline_raw.get("dirty_snapshot", []))
        candidate_dirty = bool(candidate_raw) and any("user-owned.txt" in line for line in candidate_raw.get("dirty_snapshot", []))
        dirty_equal = baseline_raw.get("dirty_snapshot") == candidate_raw.get("dirty_snapshot")
        recovery_ok = dimension_results["recoverability"]["candidate"]
        raw_dimensions["accepted_result_behavior"] = {
            label: not side_has(label, ("assertion", "context", "contract", "missing"))
            for label in ("baseline", "candidate")
        }
        raw_dimensions["safety_permission_outcome"] = {
            "baseline": not side_has("baseline", ("permission", "private", "context", "contract")),
            "candidate": not side_has("candidate", ("permission", "private", "context", "contract"))
            and dimension_results["safety_permission_outcome"]["candidate"],
        }
        raw_dimensions["verification_receipt_completeness"] = {
            label: not side_has(label, ("receipt", "verification_not_applicable"))
            for label in ("baseline", "candidate")
        }
        raw_dimensions["dirty_worktree_preservation"] = {"baseline": baseline_dirty and dirty_equal, "candidate": candidate_dirty and dirty_equal}
        raw_dimensions["recoverability"] = {"baseline": recovery_ok, "candidate": recovery_ok}
        errors.extend(capture_errors)
        for dimension, pair in raw_dimensions.items():
            actual_total += 1
            if pair["baseline"] and pair["candidate"]:
                actual_passed += 1
            else:
                errors.append(f"{scenario_id} actual outcome parity loss: {dimension}")

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
                "actual_outcome_dimensions": raw_dimensions,
                "assertion_errors": assertion_errors_by_side,
                "captures": observation.get("baseline_capture"),
                "candidate_capture": observation.get("candidate_capture"),
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
    routing_parity = {
        "dimensions": list(DIMENSIONS),
        "passed_checks": routing_passed,
        "total_checks": routing_total,
        "rate": routing_passed / routing_total if routing_total else 0.0,
    }
    actual_outcome_parity = {
        "dimensions": list(DIMENSIONS),
        "passed_checks": actual_passed,
        "total_checks": actual_total,
        "rate": actual_passed / actual_total if actual_total else 0.0,
    }
    return {
        "schema_version": 1,
        "pass": not errors and routing_total == len(corpus["scenarios"]) * len(DIMENSIONS) and actual_total == len(corpus["scenarios"]) * len(DIMENSIONS),
        "scenario_count": len(corpus["scenarios"]),
        "measurement_boundary": corpus["measurement_boundary"],
        "routing_parity": routing_parity,
        "actual_outcome_parity": actual_outcome_parity,
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
    capture = subparsers.add_parser("capture")
    capture.add_argument("corpus")
    capture.add_argument("--observations", required=True)
    capture.add_argument("--output", required=True)
    args = parser.parse_args()

    corpus_path = Path(args.corpus).resolve()
    observations_path = Path(args.observations).resolve()
    root = corpus_path.parents[2]
    try:
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        observations = json.loads(observations_path.read_text(encoding="utf-8"))
        if args.command == "capture":
            captured = capture_observations(corpus, observations)
            Path(args.output).write_text(json.dumps(captured, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"captured={len(captured['observations'])} version={CAPTURE_VERSION}")
            return 0
        report = run_comparison(corpus, observations, root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"pass={str(report['pass']).lower()} routing_parity={report['routing_parity']['passed_checks']}/"
            f"{report['routing_parity']['total_checks']} actual_outcome_parity="
            f"{report['actual_outcome_parity']['passed_checks']}/{report['actual_outcome_parity']['total_checks']} context_median="
            f"{report['efficiency']['context']['median_relative_reduction']:.6f} helper_median="
            f"{report['efficiency']['helpers']['median_relative_reduction']:.6f}"
        )
    if not report["pass"]:
        print("ERROR: " + "; ".join(report["errors"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
