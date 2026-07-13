#!/usr/bin/env python3
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "dhf_simplification_scenarios.json"
VALIDATOR = ROOT / "scripts" / "validate_dhf_simplification_corpus.py"
CONTRACT = ROOT / "docs" / "plans" / "2026-07-12-dhf-simplification-implementation-contract.md"
DISPATCHER = ROOT / "codex" / "hooks" / "dhf_preprompt.py"
SKILL = ROOT / "codex" / "skills" / "delivery-harness-framework" / "SKILL.md"
EVALS = ROOT / "codex" / "skills" / "delivery-harness-framework" / "evals" / "evals.json"
COMPLETION_ORACLE = (
    ROOT
    / "codex"
    / "skills"
    / "delivery-harness-framework"
    / "evals"
    / "validate_completion_output.py"
)
BASELINE_BASE_SHA = "00818ae174f039899a2757ee4c67fcf9db1effa0"
RESULT_INVARIANTS = [
    "result",
    "scope_and_constraints",
    "verification_receipt",
    "remaining_risk_or_next_action",
]
HELPER_CLIS = [
    ROOT / "scripts" / "harness_recover.py",
    ROOT / "scripts" / "harness_env_probe.py",
    ROOT / "scripts" / "harness_requirements.py",
    ROOT / "scripts" / "harness_report.py",
    ROOT / "scripts" / "harness_agent_team.py",
    ROOT / "scripts" / "harness_checkpoint.py",
]
NORMATIVE_MIRRORS = [
    ROOT / "README.md",
    ROOT / "docs" / "HARNESS_RUNTIME.md",
    ROOT / "docs" / "LIFECYCLE_SKILL_ROUTING.md",
    ROOT / "docs" / "repo-index.md",
]
SURFACES = ROOT / "docs" / "surfaces.json"
PUBLIC_ROUTING_PREFIXES = (
    "docs/delivery-harness-beginner-guide-",
    "docs/project-lifecycle-harness-flow-",
)


def load_validator():
    if not VALIDATOR.is_file():
        raise AssertionError(f"missing Slice 0 validator: {VALIDATOR.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("dhf_simplification_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("Slice 0 validator is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_dispatcher():
    spec = importlib.util.spec_from_file_location("dhf_simplification_candidate_dispatcher", DISPATCHER)
    if spec is None or spec.loader is None:
        raise AssertionError("DHF dispatcher is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_canonical_contract(skill_text: str, dispatcher_text: str) -> dict[str, object]:
    output_contract = skill_text.split("## Output Contract", 1)[1]
    invariant_block = output_contract.split("### Profile Output And Helper Contract", 1)[0]
    invariants = tuple(re.findall(r"^\d+\. `([^`]+)`:", invariant_block, flags=re.MULTILINE))
    profile_block = output_contract.split("### Profile Output And Helper Contract", 1)[1]
    profile_block = profile_block.split("### Governed Escalation Contract", 1)[0]
    skill_profiles = tuple(re.findall(r"^\| `([^`]+)` \|", profile_block, flags=re.MULTILINE))

    tree = ast.parse(dispatcher_text)
    assignments = {
        node.targets[0].id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    dispatcher_profiles = tuple(ast.literal_eval(assignments["PROFILE_RANK"]).keys())
    if skill_profiles != dispatcher_profiles:
        raise AssertionError(
            f"canonical profile drift: skill={skill_profiles}, dispatcher={dispatcher_profiles}"
        )

    switch = assignments["SIMPLIFIED_PROFILES_ENABLED"]
    if not isinstance(switch, ast.Compare) or len(switch.ops) != 1 or not isinstance(switch.ops[0], ast.Eq):
        raise AssertionError("candidate switch must use one exact equality comparison")
    env_get = switch.left
    if not isinstance(env_get, ast.Call) or len(env_get.args) != 2:
        raise AssertionError("candidate switch must declare environment name and default")
    switch_name = ast.literal_eval(env_get.args[0])
    switch_default = ast.literal_eval(env_get.args[1])
    switch_enable = ast.literal_eval(switch.comparators[0])
    return {
        "profiles": skill_profiles,
        "invariants": invariants,
        "switch_name": switch_name,
        "switch_default": switch_default,
        "switch_enable": switch_enable,
    }


def probe_dispatcher_routes(dispatcher) -> dict[str, str]:
    original = {
        "SHIPQ_ROOT": dispatcher.SHIPQ_ROOT,
        "SHIPQ_ADAPTER": dispatcher.SHIPQ_ADAPTER,
        "ALLOW_UNTRUSTED_ADAPTER": dispatcher.ALLOW_UNTRUSTED_ADAPTER,
        "SIMPLIFIED_PROFILES_ENABLED": dispatcher.SIMPLIFIED_PROFILES_ENABLED,
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shipq = root / "ShipQ"
            generic = root / "Generic"
            shipq.mkdir()
            generic.mkdir()
            adapter = root / "adapter.py"
            adapter.write_text(
                "def build_response(_payload):\n"
                "    return {'continue': True, 'hookSpecificOutput': "
                "{'hookEventName': 'UserPromptSubmit', 'additionalContext': 'adapter-owned'}}\n",
                encoding="utf-8",
            )
            dispatcher.SHIPQ_ROOT = shipq
            dispatcher.SHIPQ_ADAPTER = adapter
            dispatcher.ALLOW_UNTRUSTED_ADAPTER = True
            default_generic = dispatcher.route_response(
                {"cwd": str(generic), "prompt": "complex local feature"}
            )[1]
            dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
            return {
                "default_generic": default_generic,
                "opt_out": dispatcher.route_response(
                    {"cwd": str(shipq), "prompt": "complex handoff; skip dhf"}
                )[1],
                "shipq": dispatcher.route_response(
                    {"cwd": str(shipq), "prompt": "complex handoff"}
                )[1],
                "explicit_generic": dispatcher.route_response(
                    {"cwd": str(generic), "prompt": "complex local feature"}
                )[1],
                "ordinary": dispatcher.route_response(
                    {"cwd": str(generic), "prompt": "Rename a local variable."}
                )[1],
            }
    finally:
        for name, value in original.items():
            setattr(dispatcher, name, value)


def mirror_contract_errors(text: str, contract: dict[str, object], routes: dict[str, str]) -> list[str]:
    normalized = " ".join(text.split())
    required = [
        "codex/skills/delivery-harness-framework/SKILL.md",
        "codex/hooks/dhf_preprompt.py",
        *(f"`{profile}`" for profile in contract["profiles"]),
        *(f"`{invariant}`" for invariant in contract["invariants"]),
        f"{contract['switch_name']}={contract['switch_enable']}",
        "repo-source default is `simplified`",
        "Runtime promotion is pending separate authorization",
        "runtime home remains unsynced",
    ]
    if routes == {
        "default_generic": "generic-activated:standard:compatibility_risk_trigger",
        "opt_out": "opt-out",
        "shipq": "shipq-delegated",
        "explicit_generic": "generic-activated:standard:compatibility_risk_trigger",
        "ordinary": "continue-only",
    }:
        required.extend(
            ["explicit generic activation", "continue-only", "opt-out", "ShipQ", "lazy delegation"]
        )
    else:
        return [f"unexpected canonical dispatcher routes: {routes}"]
    return [term for term in required if term not in normalized]


def public_helper_contract_errors(text: str, contract: dict[str, object]) -> list[str]:
    normalized = " ".join(text.split())
    governed = contract["profiles"][-1]
    light = contract["profiles"][0]
    required = [
        f"<code>{governed}</code>",
        "matching escalation signal",
        f"<code>{light}</code>",
        "harness_recover.py",
        "harness_env_probe.py",
        "harness_checkpoint.py",
    ]
    if "不要求" not in normalized and "does not require" not in normalized:
        required.append("不要求|does not require")
    stale = (
        "任何复杂任务、恢复会话、dirty 工作树、跨阶段交接或含糊请求",
        "任何复杂任务、恢复中的会话、脏工作区、跨阶段交接，或目标不清的请求",
        "有意义的工作切片结束时",
        "在有意义的工作切片结束时",
        "Any complex task, resumed session, dirty worktree, cross-stage handoff, or ambiguous request",
        "At the end of meaningful work slices",
        "重大实现切片验证后",
    )
    return [f"missing:{term}" for term in required if term not in normalized] + [
        f"stale:{term}" for term in stale if term in normalized
    ]


def registered_public_routing_mirrors() -> tuple[Path, ...]:
    manifest = json.loads(SURFACES.read_text(encoding="utf-8"))
    paths = []
    for surface in manifest["surfaces"]:
        path = surface["path"]
        if not path.endswith(".html") or not path.startswith(PUBLIC_ROUTING_PREFIXES):
            continue
        if "human" not in surface.get("audience", []):
            raise AssertionError(f"registered public routing surface lacks human audience: {path}")
        paths.append(ROOT / path)
    if not paths:
        raise AssertionError("surfaces manifest registered no lifecycle beginner/flow public pages")
    return tuple(paths)


class DhfSimplificationCorpusTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_validator()
        if not CORPUS.is_file():
            self.fail(f"missing Slice 0 corpus: {CORPUS.relative_to(ROOT)}")
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))

    def test_cli_validates_schema_counts_trace_and_baseline(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "validate",
                str(CORPUS),
                "--contract",
                str(CONTRACT),
                "--check-baseline",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["scenario_count"], 17)
        self.assertEqual(payload["category_counts"], {"light": 4, "standard": 5, "governed": 6})
        self.assertEqual(payload["routing_control_count"], 2)
        self.assertEqual(payload["acceptance_criterion_count"], 18)
        self.assertEqual(payload["baseline_mismatch_count"], 15)

    def test_validation_rejects_schema_and_identity_failures(self):
        broken = copy.deepcopy(self.corpus)
        broken["scenarios"][1]["id"] = broken["scenarios"][0]["id"]
        del broken["scenarios"][2]["permission_safety_outcome"]
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("scenario IDs must be unique" in error for error in errors), errors)
        self.assertTrue(any("permission_safety_outcome" in error for error in errors), errors)

    def test_validation_rejects_category_and_cohort_drift(self):
        broken = copy.deepcopy(self.corpus)
        broken["scenarios"] = [
            scenario for scenario in broken["scenarios"] if scenario["id"] != "LIGHT-TRIVIAL-FORMAT"
        ]
        shipq = next(scenario for scenario in broken["scenarios"] if scenario["id"] == "CONTROL-SHIPQ-DELEGATION")
        shipq["cohort_status"] = "efficiency_included"
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("light scenarios" in error for error in errors), errors)
        self.assertTrue(any("routing controls must be excluded" in error for error in errors), errors)

    def test_validation_rejects_incomplete_acceptance_traceability(self):
        broken = copy.deepcopy(self.corpus)
        broken["acceptance_trace_map"].pop("AC-18")
        broken["acceptance_trace_map"]["AC-01"]["scenario_ids"] = ["UNKNOWN-SCENARIO"]
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("missing acceptance trace IDs: AC-18" in error for error in errors), errors)
        self.assertTrue(any("unknown scenario ID: UNKNOWN-SCENARIO" in error for error in errors), errors)

    def test_catalog_binds_trace_ids_to_real_test_callables(self):
        expected_behavior_tests = {
            "AC-04": "TEST-OPT-OUT-PRECEDENCE",
            "AC-06": "TEST-MALFORMED-PAYLOAD-SAFETY",
            "AC-09": "TEST-HELPER-CLI-CALLABILITY",
        }
        for acceptance_id, test_id in expected_behavior_tests.items():
            self.assertIn(test_id, self.corpus["acceptance_trace_map"][acceptance_id]["test_ids"])
            self.assertIn(test_id, self.corpus["test_catalog"])

        broken = copy.deepcopy(self.corpus)
        broken["acceptance_trace_map"]["AC-01"]["test_ids"] = ["UNKNOWN-TEST"]
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("unknown test ID: UNKNOWN-TEST" in error for error in errors), errors)

        broken = copy.deepcopy(self.corpus)
        broken["test_catalog"]["TEST-SCHEMA-COUNTS"] = "tests/test_dhf_simplification.py::Missing.test_method"
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("does not resolve to a test callable" in error for error in errors), errors)

    def test_completed_slice_acceptance_trace_has_live_evidence_and_callable_bindings(self):
        completed = ("AC-02", "AC-10", "AC-11", "AC-12", "AC-13", "AC-15", "AC-17", "AC-18")
        for acceptance_id in completed:
            with self.subTest(acceptance_id=acceptance_id):
                trace = self.corpus["acceptance_trace_map"][acceptance_id]
                self.assertEqual(set(trace["evidence_status"]), {"state", "evidence_id"})
                self.assertEqual(trace["evidence_status"]["state"], "completed")
                self.assertTrue(trace["evidence_status"]["evidence_id"])
                self.assertTrue(trace["test_ids"])
                for test_id in trace["test_ids"]:
                    self.assertIn(test_id, self.corpus["test_catalog"])

        broken = copy.deepcopy(self.corpus)
        for invalid_state in ("stale", "pending", "banana", "deferred"):
            with self.subTest(invalid_state=invalid_state):
                broken = copy.deepcopy(self.corpus)
                broken["acceptance_trace_map"]["AC-10"]["evidence_status"] = {
                    "state": invalid_state,
                    "evidence_id": "TEST-PAIRED-ACTUAL-OUTCOMES",
                }
                errors = self.validator.validate_corpus(broken, CONTRACT)
                self.assertTrue(any("AC-10" in error and "evidence_status" in error for error in errors), errors)

        broken = copy.deepcopy(self.corpus)
        broken["test_catalog"]["TEST-SCHEMA-COUNTS"] = "tests/test_dhf_simplification.py::load_validator"
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("does not resolve to a test callable" in error for error in errors), errors)

    def test_acceptance_trace_requires_exact_slice_and_executable_producer_binding(self):
        required_fields = {"criterion", "slice", "scenario_ids", "test_ids", "producer", "evidence_status"}
        for acceptance_id, trace in self.corpus["acceptance_trace_map"].items():
            with self.subTest(acceptance_id=acceptance_id):
                self.assertEqual(set(trace), required_fields)
                self.assertIn(trace["producer"], trace["test_ids"])
                self.assertIn(trace["producer"], self.corpus["test_catalog"])

        mutations = (
            lambda trace: trace.pop("producer"),
            lambda trace: trace.__setitem__("slice", "99"),
            lambda trace: trace.__setitem__("producer", "UNKNOWN-PRODUCER"),
            lambda trace: trace.__setitem__("unexpected", True),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                broken = copy.deepcopy(self.corpus)
                mutate(broken["acceptance_trace_map"]["AC-01"])
                errors = self.validator.validate_corpus(broken, CONTRACT)
                self.assertTrue(any("AC-01" in error and ("fields" in error or "slice" in error or "producer" in error) for error in errors), errors)

    def test_current_dispatcher_opt_out_precedence(self):
        env = os.environ.copy()
        env.update(
            {
                "DHF_PREPROMPT_SKILL": "/tmp/missing-generic-skill",
                "DHF_PREPROMPT_SHIPQ_ROOT": "/tmp/SanitizedShipQ",
                "DHF_PREPROMPT_SHIPQ_ADAPTER": "/tmp/missing-shipq-adapter",
            }
        )
        for payload in (
            {"cwd": "/tmp/GenericRepo", "prompt": "resume complex handoff but skip dhf"},
            {"cwd": "/tmp/SanitizedShipQ", "prompt": "complex project task; do not use dhf"},
        ):
            proc = subprocess.run(
                [sys.executable, str(DISPATCHER)],
                input=json.dumps(payload),
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), {"continue": True})
            self.assertIn("diagnostic=opt-out", proc.stderr)
            self.assertNotIn("additionalContext", proc.stdout)

    def test_current_dispatcher_malformed_payload_safety(self):
        for input_text in ("{malformed", "[]", json.dumps({"prompt": "resume complex handoff"})):
            proc = subprocess.run(
                [sys.executable, str(DISPATCHER)],
                input=input_text,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), {"continue": True})
            self.assertNotIn("Traceback", proc.stderr)
            self.assertNotIn("additionalContext", proc.stdout)

    def test_current_helper_cli_entry_points_are_callable(self):
        for helper in HELPER_CLIS:
            proc = subprocess.run(
                [sys.executable, str(helper), "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, f"{helper.name}: {proc.stderr}")
            self.assertIn("usage:", proc.stdout.lower(), helper.name)

    def test_baseline_measurement_is_deterministic_and_detects_drift(self):
        first = self.validator.measure_baseline(self.corpus, ROOT)
        second = self.validator.measure_baseline(self.corpus, ROOT)
        self.assertEqual(first, second)
        self.assertEqual(
            [item["id"] for item in first],
            [scenario["id"] for scenario in self.corpus["scenarios"]],
        )
        broken = copy.deepcopy(self.corpus)
        broken["scenarios"][0]["baseline_measurement"]["injected_context_utf8_bytes_proxy"] += 1
        errors = self.validator.validate_baseline_measurements(broken, ROOT)
        self.assertTrue(any("injected-context proxy mismatch" in error for error in errors), errors)

    def test_baseline_is_frozen_to_base_sha_independently_of_current_skill(self):
        provenance = self.corpus["measurement_boundary"]["baseline_provenance"]
        self.assertEqual(provenance["base_sha"], BASELINE_BASE_SHA)
        self.assertEqual(provenance["oracle_kind"], "frozen_measurement")
        self.assertEqual(provenance["generic_context_utf8_bytes_proxy"], 32803)
        self.assertEqual(self.validator.BASELINE_BASE_SHA, BASELINE_BASE_SHA)

        baseline = self.validator.measure_baseline(self.corpus, ROOT)
        generic = [item for item in baseline if item["route"] == "generic-activated"]
        self.assertEqual(len(generic), 15)
        self.assertEqual({item["injected_context_utf8_bytes_proxy"] for item in generic}, {32803})
        self.assertEqual(
            {
                scenario["baseline_measurement"]["injected_context_utf8_bytes_proxy"]
                for scenario in self.corpus["scenarios"]
                if scenario["baseline_measurement"]["route"] == "generic-activated"
            },
            {32803},
        )

        candidate = self.validator.measure_candidate(self.corpus, ROOT)
        light = next(item for item in candidate if item["id"] == "LIGHT-EXPLANATION")
        dispatcher = load_dispatcher()
        current_context = dispatcher.profile_context(
            dispatcher.select_governance_profile(
                next(
                    scenario["sanitized_prompt"]
                    for scenario in self.corpus["scenarios"]
                    if scenario["id"] == "LIGHT-EXPLANATION"
                )
            )
        )
        self.assertEqual(light["injected_context_utf8_bytes_proxy"], len(current_context.encode("utf-8")))

        broken = copy.deepcopy(self.corpus)
        broken["measurement_boundary"]["baseline_provenance"]["base_sha"] = "deadbeef"
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("baseline provenance" in error for error in errors), errors)

    def test_candidate_measurement_exposes_selected_profiles_without_rewriting_baseline(self):
        candidate = self.validator.measure_candidate(self.corpus, ROOT)
        by_id = {item["id"]: item for item in candidate}
        self.assertEqual(by_id["LIGHT-EXPLANATION"]["selected_profile"], "light")
        self.assertEqual(by_id["STANDARD-LOCAL-FEATURE"]["selected_profile"], "standard")
        self.assertEqual(by_id["GOVERNED-REMOTE-DEPLOY"]["selected_profile"], "governed")
        self.assertEqual(by_id["CONTROL-ORDINARY-CONTINUE"]["selected_profile"], None)
        self.assertEqual(by_id["CONTROL-SHIPQ-DELEGATION"]["selected_profile"], None)
        self.assertEqual(
            self.corpus["scenarios"][0]["baseline_measurement"]["route"],
            "generic-activated",
        )

    def test_candidate_helper_measurement_is_observed_and_missing_helper_fails(self):
        self.assertTrue(
            hasattr(self.validator, "validate_candidate_measurements"),
            "candidate measurement needs an independent helper validator",
        )
        measured = self.validator.measure_candidate(self.corpus, ROOT)
        self.assertEqual(self.validator.validate_candidate_measurements(self.corpus, ROOT, measured), [])
        self.assertTrue(
            all("contract_observed" in item and "contract_parse_valid" in item for item in measured),
            "candidate measurements must expose contract observation metadata",
        )
        self.assertTrue(all(item["contract_observed"] for item in measured if item["selected_profile"] is not None))
        self.assertTrue(all(item["contract_parse_valid"] for item in measured if item["selected_profile"] is not None))
        remote = next(item for item in measured if item["id"] == "GOVERNED-REMOTE-DEPLOY")
        self.assertEqual(
            remote["observed_mandatory_helpers"],
            ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py"],
        )
        remote["observed_mandatory_helpers"].remove("harness_report.py")
        remote["mandatory_helper_count"] -= 1
        errors = self.validator.validate_candidate_measurements(self.corpus, ROOT, measured)
        self.assertTrue(any("GOVERNED-REMOTE-DEPLOY candidate helper mismatch" in error for error in errors), errors)

    def test_candidate_contract_parser_distinguishes_missing_corrupt_and_valid_zero(self):
        self.assertTrue(
            hasattr(self.validator, "_observed_candidate_contract"),
            "candidate parser must return contract observation metadata",
        )
        missing = self.validator._observed_candidate_contract("profile=light")
        corrupt = self.validator._observed_candidate_contract("DHF_PROFILE_CONTRACT={broken")
        valid_zero = self.validator._observed_candidate_contract('DHF_PROFILE_CONTRACT={"mandatory_helpers":[]}')
        empty_contract = {
            "helpers": [],
            "escalation_signals": [],
            "required_output_fields": [],
            "authoritative_gates": [],
        }
        self.assertEqual(missing, {"contract_observed": False, "contract_parse_valid": False, **empty_contract})
        self.assertEqual(corrupt, {"contract_observed": True, "contract_parse_valid": False, **empty_contract})
        self.assertEqual(valid_zero, {"contract_observed": True, "contract_parse_valid": True, **empty_contract})

        measured = self.validator.measure_candidate(self.corpus, ROOT)
        activated = next(item for item in measured if item["id"] == "LIGHT-EXPLANATION")
        activated["contract_observed"] = False
        activated["contract_parse_valid"] = False
        errors = self.validator.validate_candidate_measurements(self.corpus, ROOT, measured)
        self.assertTrue(any("LIGHT-EXPLANATION candidate contract missing" in error for error in errors), errors)

        corrupt_measured = self.validator.measure_candidate(self.corpus, ROOT)
        corrupt_activated = next(item for item in corrupt_measured if item["id"] == "LIGHT-EXPLANATION")
        corrupt_activated["contract_parse_valid"] = False
        errors = self.validator.validate_candidate_measurements(self.corpus, ROOT, corrupt_measured)
        self.assertTrue(any("LIGHT-EXPLANATION candidate contract invalid" in error for error in errors), errors)

    def test_baseline_helper_measurement_uses_independent_oracle(self):
        broken = copy.deepcopy(self.corpus)
        scenario = broken["scenarios"][0]
        scenario["baseline_mandatory_helpers"] = ["invented_helper.py"]
        scenario["baseline_measurement"]["mandatory_helper_count"] = 1
        errors = self.validator.validate_baseline_measurements(broken, ROOT)
        self.assertTrue(any("canonical helper oracle mismatch" in error for error in errors), errors)

    def test_non_string_identity_fields_return_structured_errors(self):
        broken = copy.deepcopy(self.corpus)
        broken["scenarios"][0]["id"] = ["not", "hashable"]
        broken["scenarios"][1]["category"] = ["not", "hashable"]
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("scenario[0].id must be a non-empty string" in error for error in errors), errors)
        self.assertTrue(any("scenario[1].category must be a non-empty string" in error for error in errors), errors)

    def test_runner_wrapper_does_not_depend_on_test_count(self):
        runner_text = (ROOT / "test_runner.py").read_text(encoding="utf-8")
        self.assertNotIn('require("Ran 5 tests"', runner_text)


class DhfGovernanceProfileTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = load_dispatcher()
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))

    def test_canonical_activated_scenarios_select_deterministic_profiles(self):
        for scenario in self.corpus["scenarios"]:
            if scenario["activation_status"] != "explicitly_activated_generic":
                continue
            with self.subTest(scenario=scenario["id"]):
                selected = self.dispatcher.select_governance_profile(scenario["sanitized_prompt"])
                self.assertEqual(selected.profile, scenario["expected_profile"])
                self.assertEqual(selected.escalation_signal, scenario["escalation_signal"])

    def test_implicit_risk_upgrades_an_explicit_generic_activation(self):
        cases = {
            "Use complex analysis on this sanitized customer private data.": "external_capture_or_private_data",
            "Implement this complex local change, then deploy it remotely.": "remote_or_deployment_action",
            "Review this complex change with multiple agents.": "multiple_agents_or_overlapping_write_sets",
            "Run this complex operation over SSH on the build host.": "remote_or_deployment_action",
            "Rotate this complex API credential and update its stored value.": "external_capture_or_private_data",
            "Apply this complex irreversible data migration that deletes rows.": "destructive_or_irreversible_action",
        }
        for prompt, signal in cases.items():
            with self.subTest(prompt=prompt):
                selection = self.dispatcher.select_governance_profile(prompt)
                self.assertEqual(selection.profile, "governed")
                self.assertEqual(selection.escalation_signal, signal)

    def test_profile_upgrade_is_monotonic_and_malformed_resume_fails_closed(self):
        standard = self.dispatcher.select_governance_profile(
            "Implement this complex local parser option.", active_profile="light"
        )
        self.assertEqual(standard.profile, "standard")
        governed = self.dispatcher.select_governance_profile(
            "Continue this complex local parser option.", active_profile="governed"
        )
        self.assertEqual(governed.profile, "governed")
        malformed = self.dispatcher.select_governance_profile(
            "Resume this complex task with malformed state.", active_profile="not-a-profile"
        )
        self.assertEqual(malformed.profile, "governed")
        self.assertEqual(malformed.escalation_signal, "resume_or_handoff")

    def test_malformed_profile_state_without_risk_keywords_fails_closed(self):
        self.dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
        prompt = "Use complex analysis to format this supplied text."
        absent, absent_route = self.dispatcher.route_response({"cwd": "/tmp/Generic", "prompt": prompt})
        malformed, malformed_route = self.dispatcher.route_response(
            {"cwd": "/tmp/Generic", "prompt": prompt, "dhf_profile_state": "corrupt-state"}
        )
        self.assertEqual(absent_route, "generic-activated:light:compatibility_risk_trigger")
        self.assertIn("profile=light", absent["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(malformed_route, "generic-activated:governed:compatibility_risk_trigger")
        self.assertIn("escalation_signal=malformed_profile_state", malformed["hookSpecificOutput"]["additionalContext"])

    def test_route_precedence_and_shipq_profile_ownership(self):
        with __import__("tempfile").TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shipq_root = tmp_path / "ShipQ"
            generic_root = tmp_path / "Generic"
            shipq_root.mkdir()
            generic_root.mkdir()
            adapter = tmp_path / "adapter.py"
            adapter.write_text(
                "def build_response(_payload):\n"
                "    return {'continue': True, 'hookSpecificOutput': "
                "{'hookEventName': 'UserPromptSubmit', 'additionalContext': 'adapter-owned'}}\n",
                encoding="utf-8",
            )
            self.dispatcher.SHIPQ_ROOT = shipq_root
            self.dispatcher.SHIPQ_ADAPTER = adapter
            self.dispatcher.ALLOW_UNTRUSTED_ADAPTER = True

            opted_out, route = self.dispatcher.route_response(
                {"cwd": str(shipq_root), "prompt": "complex remote deploy; skip dhf"}
            )
            self.assertEqual((opted_out, route), ({"continue": True}, "opt-out"))
            delegated, route = self.dispatcher.route_response(
                {"cwd": str(shipq_root), "prompt": "complex remote deployment"}
            )
            self.assertEqual(route, "shipq-delegated")
            self.assertEqual(delegated["hookSpecificOutput"]["additionalContext"], "adapter-owned")
            ordinary, route = self.dispatcher.route_response(
                {"cwd": str(generic_root), "prompt": "Rename a local variable."}
            )
            self.assertEqual((ordinary, route), ({"continue": True}, "continue-only"))

    def test_enabled_profiles_emit_minimum_context_without_full_skill(self):
        marker = "FULL_SKILL_SECRET_MARKER_/Users/private/unrelated"
        with __import__("tempfile").TemporaryDirectory() as tmp:
            skill = Path(tmp) / "DHF.md"
            skill.write_text(marker, encoding="utf-8")
            self.dispatcher.DHF_SKILL = skill
            self.dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
            response, route = self.dispatcher.route_response(
                {"cwd": tmp, "prompt": "Use complex analysis to explain this deterministic function."}
            )
            self.assertEqual(route, "generic-activated:light:compatibility_risk_trigger")
            context = response["hookSpecificOutput"]["additionalContext"]
            self.assertIn("profile=light", context)
            self.assertNotIn(marker, context)
            self.assertNotIn("Traceback", context)

    def test_output_contract_is_reduced_to_exact_result_invariants(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        output_contract = skill_text.split("## Output Contract", 1)[1]
        invariant_block = output_contract.split("### Profile Output And Helper Contract", 1)[0]
        self.assertEqual(
            re.findall(r"^\d+\. `([^`]+)`:", invariant_block, flags=re.MULTILINE),
            RESULT_INVARIANTS,
        )
        self.assertNotIn("After routing, state:", output_contract)
        for ceremony in (
            "Lifecycle stage selected",
            "Execution lane selected",
            "Dirty worktree classification",
            "effective_feedback_check",
            "conversion_health",
            "empty committee fields",
        ):
            self.assertNotIn(ceremony, invariant_block)

    def test_profile_contract_does_not_mandate_lightweight_ceremony(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        profile_contract = skill_text.split("### Profile Output And Helper Contract", 1)[1]
        profile_contract = profile_contract.split("### Governed Escalation Contract", 1)[0]
        expected_not_mandatory = {
            "light": {
                "harness_recover.py",
                "harness_env_probe.py",
                "harness_report.py",
                "harness_checkpoint.py",
            },
            "standard": {"harness_checkpoint.py", "harness_agent_team.py"},
            "governed": set(),
        }
        rows = {}
        for line in profile_contract.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells and cells[0].strip("`") in expected_not_mandatory:
                rows[cells[0].strip("`")] = {
                    "mandatory": set(re.findall(r"`([^`]+\.py)`", cells[2])),
                    "not_mandatory": set(re.findall(r"`([^`]+\.py)`", cells[3])),
                }
        self.assertEqual(set(rows), set(expected_not_mandatory))
        self.assertEqual(rows["light"]["mandatory"], set())
        self.assertEqual(rows["standard"]["mandatory"], set())
        for profile, helpers in expected_not_mandatory.items():
            self.assertEqual(rows[profile]["not_mandatory"], helpers)
        normalized_contract = " ".join(profile_contract.split())
        for ceremony in (
            "lifecycle phase",
            "default execution lane",
            "dirty status",
            "recovery output",
            "environment probe output",
            "conversion-health boilerplate",
            "effective-feedback boilerplate",
            "checkpoint",
            "empty committee fields",
        ):
            self.assertIn(ceremony, normalized_contract)

    def test_governed_escalation_contract_preserves_scenario_gates(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        governed_contract = skill_text.split("### Governed Escalation Contract", 1)[1]
        governed_contract = governed_contract.split("### Completion Claim Taxonomy", 1)[0]
        rows = {}
        for line in governed_contract.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            signal = cells[0].strip("`")
            rows[signal] = {
                "helpers": set(re.findall(r"`([^`]+\.py)`", cells[1])),
                "fields": set(re.findall(r"`([^`]+)`", cells[2])),
            }
        governed_scenarios = [
            scenario for scenario in self.corpus["scenarios"] if scenario["category"] == "governed"
        ]
        self.assertEqual(set(rows), set(self.dispatcher.MANDATORY_HELPERS_BY_SIGNAL))
        for signal, helpers in self.dispatcher.MANDATORY_HELPERS_BY_SIGNAL.items():
            self.assertEqual(rows[signal]["helpers"], set(helpers), signal)
        for scenario in governed_scenarios:
            with self.subTest(scenario=scenario["id"]):
                row = rows[scenario["escalation_signal"]]
                self.assertEqual(row["helpers"], set(scenario["mandatory_helpers"]))
                self.assertEqual(
                    row["fields"],
                    set(scenario["required_output_fields"]) - set(RESULT_INVARIANTS),
                )

    def test_completion_taxonomy_and_evals_cover_all_claim_classes(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        taxonomy = skill_text.split("### Completion Claim Taxonomy", 1)[1]
        claim_classes = {
            "implemented_or_fixed",
            "documented_or_configured",
            "diagnosed_or_blocked",
            "verification_not_applicable",
        }
        self.assertEqual(set(re.findall(r"^\| `([^`]+)` \|", taxonomy, flags=re.MULTILINE)), claim_classes)
        self.assertIn("command", taxonomy)
        self.assertIn("exit_code", taxonomy)
        self.assertIn("key_output", taxonomy)
        self.assertIn("timestamp", taxonomy)
        self.assertIn("must not invent a command or receipt", taxonomy)

        eval_data = json.loads(EVALS.read_text(encoding="utf-8"))
        claim_evals = {
            case["completion_claim_class"]: case
            for case in eval_data["evals"]
            if "completion_claim_class" in case
        }
        self.assertEqual(set(claim_evals), claim_classes)
        explanation = claim_evals["verification_not_applicable"]
        self.assertTrue(any("must not invent" in assertion for assertion in explanation["assertions"]))
        for claim_class in ("implemented_or_fixed", "documented_or_configured"):
            assertions = " ".join(claim_evals[claim_class]["assertions"])
            for field in ("command", "exit_code", "key_output", "timestamp"):
                self.assertIn(field, assertions)
        blocker_assertions = " ".join(claim_evals["diagnosed_or_blocked"]["assertions"])
        self.assertIn("exact blocker", blocker_assertions)
        self.assertIn("concrete", blocker_assertions)

    def test_profile_context_matches_completion_taxonomy(self):
        explanation = self.dispatcher.profile_context(self.dispatcher.ProfileSelection("light", None))
        self.assertIn("verification_not_applicable", explanation)
        self.assertNotIn("fresh verification_receipt", explanation)
        for claim_class in (
            "implemented_or_fixed",
            "documented_or_configured",
            "diagnosed_or_blocked",
        ):
            self.assertIn(claim_class, explanation)

    def test_multiple_escalation_signals_union_helpers_fields_and_gates(self):
        prompt = (
            "Perform this complex customer private data deployment remotely with multiple agents "
            "and overlapping write sets."
        )
        selection = self.dispatcher.select_governance_profile(prompt)
        self.assertEqual(selection.profile, "governed")
        self.assertEqual(
            selection.escalation_signals,
            (
                "external_capture_or_private_data",
                "remote_or_deployment_action",
                "multiple_agents_or_overlapping_write_sets",
            ),
        )
        context = self.dispatcher.profile_context(selection)
        contract_line = context.split("DHF_PROFILE_CONTRACT=", 1)[1].splitlines()[0]
        contract = json.loads(contract_line)
        self.assertEqual(contract["escalation_signals"], list(selection.escalation_signals))
        self.assertEqual(
            contract["mandatory_helpers"],
            ["harness_env_probe.py", "harness_report.py", "harness_checkpoint.py", "harness_agent_team.py"],
        )
        self.assertEqual(
            set(contract["required_output_fields"]),
            {"data_boundary", "authorization_state", "rollback", "agent_write_sets"},
        )
        self.assertEqual(
            set(contract["authoritative_gates"]),
            {
                "External Capture Promotion Gate",
                "Evidence And Report Gate",
                "Checkpoint Gate",
                "Execution Lane Gate",
                "Deployment Readiness Gate",
                "Agent Team Gate",
            },
        )
        for signal in selection.escalation_signals:
            self.assertIn(signal, context)

    def test_helper_router_startup_and_checkpoint_are_signal_conditional(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        helper_router = skill_text.split("## Helper Router", 1)[1].split("## Startup Sequence", 1)[0]
        startup = skill_text.split("## Startup Sequence", 1)[1].split("## Dirty Worktree Gate", 1)[0]
        checkpoint = skill_text.split("## Checkpoint Gate", 1)[1].split("## Exception Handling Principles", 1)[0]
        self.assertIn("Matching profile and signal", helper_router)
        self.assertIn("Light", helper_router)
        self.assertIn("requires no lifecycle helper", helper_router)
        self.assertNotIn("Prefer runtime helper CLIs when present", helper_router)
        self.assertNotIn("after a meaningful validated implementation slice", helper_router)
        for section in (startup, checkpoint):
            normalized = " ".join(section.split()).lower()
            self.assertIn("matching", normalized)
            self.assertIn("light", normalized)
            self.assertIn("does not", normalized)
            self.assertIn("complex", normalized)
        self.assertNotIn("Run recovery and environment probes when the helper files exist", startup)

    def test_completion_output_oracle_accepts_canonical_samples_and_rejects_bad_samples(self):
        self.assertTrue(COMPLETION_ORACLE.is_file(), "missing executable completion output oracle")
        spec = importlib.util.spec_from_file_location("dhf_completion_output_oracle", COMPLETION_ORACLE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)

        eval_data = json.loads(EVALS.read_text(encoding="utf-8"))
        samples = [case["structured_output_sample"] for case in eval_data["evals"] if "completion_claim_class" in case]
        self.assertEqual(len(samples), 4)
        for sample in samples:
            with self.subTest(claim=sample["completion_claim_class"]):
                self.assertEqual(oracle.validate_output_sample(sample), [])

        bad_explanation = copy.deepcopy(
            next(sample for sample in samples if sample["completion_claim_class"] == "verification_not_applicable")
        )
        bad_explanation["verification_receipt"]["command"] = "invented --check"
        errors = oracle.validate_output_sample(bad_explanation)
        self.assertTrue(any("must not include command receipt fields" in error for error in errors), errors)

        bad_implemented = copy.deepcopy(
            next(sample for sample in samples if sample["completion_claim_class"] == "implemented_or_fixed")
        )
        del bad_implemented["verification_receipt"]["timestamp"]
        errors = oracle.validate_output_sample(bad_implemented)
        self.assertTrue(any("missing receipt fields" in error for error in errors), errors)

        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "bad-sample.json"
            sample_path.write_text(json.dumps(bad_explanation), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(COMPLETION_ORACLE), "--sample", str(sample_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("must not include command receipt fields", proc.stderr)

    def test_feature_switch_defaults_simplified_after_final_gate_and_preserves_explicit_rollback(self):
        marker = "LEGACY_FULL_SKILL_MARKER"
        with __import__("tempfile").TemporaryDirectory() as tmp:
            skill = Path(tmp) / "DHF.md"
            skill.write_text(marker, encoding="utf-8")
            base_env = os.environ.copy()
            base_env.pop("DHF_PREPROMPT_SIMPLIFIED_PROFILES", None)
            base_env.update({"DHF_PREPROMPT_SKILL": str(skill), "DHF_PREPROMPT_SHIPQ_ROOT": str(Path(tmp) / "ShipQ")})

            def run_with(value):
                env = base_env.copy()
                if value is not None:
                    env["DHF_PREPROMPT_SIMPLIFIED_PROFILES"] = value
                return subprocess.run(
                    [sys.executable, str(DISPATCHER)],
                    input=json.dumps({"cwd": tmp, "prompt": "complex local feature"}),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )

            default_proc = run_with(None)
            self.assertEqual(default_proc.returncode, 0, default_proc.stderr)
            default_payload = json.loads(default_proc.stdout)
            self.assertIn("profile=standard", default_payload["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn(marker, default_proc.stdout)
            self.assertIn("diagnostic=generic-activated:standard", default_proc.stderr)

            enabled_proc = run_with("1")
            self.assertEqual(enabled_proc.returncode, 0, enabled_proc.stderr)
            enabled_payload = json.loads(enabled_proc.stdout)
            self.assertIn("profile=standard", enabled_payload["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn(marker, enabled_proc.stdout)
            self.assertIn("diagnostic=generic-activated:standard", enabled_proc.stderr)

            for rollback_value in ("0", "false", "off", "legacy"):
                with self.subTest(rollback_value=rollback_value):
                    proc = run_with(rollback_value)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    payload = json.loads(proc.stdout)
                    self.assertIn(marker, payload["hookSpecificOutput"]["additionalContext"])
                    self.assertIn("diagnostic=generic-activated:legacy", proc.stderr)
                    self.assertNotIn("Traceback", proc.stderr)

            for unrecognized_value in ("", "typo", "true", "on", "enabled", " 1 "):
                with self.subTest(unrecognized_value=unrecognized_value):
                    proc = run_with(unrecognized_value)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    payload = json.loads(proc.stdout)
                    self.assertIn(marker, payload["hookSpecificOutput"]["additionalContext"])
                    self.assertIn("diagnostic=generic-activated:legacy:invalid-switch", proc.stderr)
                    self.assertNotIn(unrecognized_value or "<empty>", proc.stderr)

    def test_adversarial_governed_route_table_and_active_state_continuation(self):
        self.dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
        root = str(ROOT)
        cases = (
            ("Use DHF to explain this function", None, "generic-activated:light:explicit_opt_in", "profile=light"),
            ("use delivery harness for this local feature", None, "generic-activated:standard:explicit_opt_in", "profile=standard"),
            ("请使用交付框架解释这个函数", None, "generic-activated:light:explicit_opt_in", "profile=light"),
            ("continue the next safe action", {"active_profile": "governed"}, "generic-activated:governed:profile_hint", "profile=governed"),
            ("continue the next safe action", {"active_profile": "standard"}, "generic-activated:standard:profile_hint", "profile=standard"),
            ("continue the next safe action", "corrupt", "generic-activated:governed:profile_hint", "malformed_profile_state"),
            ("Use DHF then git push --force", None, "generic-activated:governed:explicit_opt_in", "destructive_or_irreversible_action"),
            ("Use DHF then git reset --hard HEAD~1", None, "generic-activated:governed:explicit_opt_in", "destructive_or_irreversible_action"),
            ("Use DHF then run rm -rf ./cache", None, "generic-activated:governed:explicit_opt_in", "destructive_or_irreversible_action"),
            ("Use DHF to rotate the API key and inspect private customer records", None, "generic-activated:governed:explicit_opt_in", "external_capture_or_private_data"),
            ("Use DHF to SSH to production and deploy", None, "generic-activated:governed:explicit_opt_in", "remote_or_deployment_action"),
        )
        for prompt, state, expected_route, expected_context in cases:
            with self.subTest(prompt=prompt, state=state):
                payload = {"cwd": root, "prompt": prompt}
                if state is not None:
                    payload["dhf_profile_state"] = state
                response, route = self.dispatcher.route_response(payload)
                self.assertEqual(route, expected_route)
                context = response.get("hookSpecificOutput", {}).get("additionalContext", "")
                self.assertIn(expected_context, context)

        opt_out, route = self.dispatcher.route_response(
            {"cwd": root, "prompt": "Use DHF to deploy, but skip DHF", "dhf_profile_state": {"active_profile": "governed"}}
        )
        self.assertEqual((opt_out, route), ({"continue": True}, "opt-out"))

        ordinary, route = self.dispatcher.route_response({"cwd": root, "prompt": "continue formatting"})
        self.assertEqual((ordinary, route), ({"continue": True}, "continue-only"))

    def test_activation_reason_distinguishes_explicit_compatibility_and_profile_hint(self):
        self.dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
        root = str(ROOT)
        cases = (
            ({"cwd": root, "prompt": "Use DHF to explain this function"}, "explicit_opt_in"),
            ({"cwd": root, "prompt": "Implement this complex local parser option"}, "compatibility_risk_trigger"),
            ({"cwd": root, "prompt": "continue the next safe action", "dhf_profile_state": {"active_profile": "standard"}}, "profile_hint"),
        )
        for payload, reason in cases:
            with self.subTest(reason=reason):
                _response, route = self.dispatcher.route_response(payload)
                self.assertTrue(route.endswith(f":{reason}"), route)

        for prompt in ("Estimate complexity", "Discuss resumption semantics", "Describe handoffs", "Check a stateful conflict"):
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    self.dispatcher.route_response({"cwd": root, "prompt": prompt}),
                    ({"continue": True}, "continue-only"),
                )

        broken = copy.deepcopy(self.corpus)
        scenario = next(item for item in broken["scenarios"] if item["cohort_status"] == "efficiency_included")
        scenario["activation_reason"] = "compatibility_risk_trigger"
        errors = load_validator().validate_corpus(broken, CONTRACT)
        self.assertTrue(any("efficiency cohort requires explicit_opt_in" in error for error in errors), errors)

    def test_credential_read_access_and_export_are_governed_without_bare_key_false_positive(self):
        self.dispatcher.SIMPLIFIED_PROFILES_ENABLED = True
        governed_prompts = (
            "Use DHF to read the API key",
            "Use DHF to access credentials",
            "Use DHF to inspect the token",
            "Use DHF to fetch a client secret",
            "Use DHF to load credentials",
            "Use DHF to export the API key",
            "Use DHF to copy the access token",
            "使用交付框架读取凭据",
            "使用交付框架访问 API 密钥",
            "使用交付框架检查令牌",
            "使用交付框架导出密钥",
            "使用交付框架复制 secret",
        )
        for prompt in governed_prompts:
            with self.subTest(prompt=prompt):
                response, route = self.dispatcher.route_response({"cwd": str(ROOT), "prompt": prompt})
                self.assertEqual(route, "generic-activated:governed:explicit_opt_in")
                self.assertIn("external_capture_or_private_data", response["hookSpecificOutput"]["additionalContext"])

        response, route = self.dispatcher.route_response(
            {"cwd": str(ROOT), "prompt": "Use DHF to rename the key in a local dictionary"}
        )
        self.assertNotEqual(route, "generic-activated:governed")
        self.assertNotIn("external_capture_or_private_data", response["hookSpecificOutput"]["additionalContext"])

    def test_normative_mirrors_align_with_simplified_source_stage_contract(self):
        contract = extract_canonical_contract(
            SKILL.read_text(encoding="utf-8"), DISPATCHER.read_text(encoding="utf-8")
        )
        routes = probe_dispatcher_routes(self.dispatcher)
        self.assertEqual(contract["switch_default"], contract["switch_enable"])
        self.assertEqual(contract["switch_default"], "1")
        stale_statements = (
            "Use first for complex or resumed work",
            "after a meaningful validated slice",
            "after validation passes for a meaningful implementation slice",
            "candidate is ready for runtime promotion",
        )
        for mirror in NORMATIVE_MIRRORS:
            text = mirror.read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            with self.subTest(mirror=mirror.relative_to(ROOT)):
                self.assertEqual(mirror_contract_errors(text, contract, routes), [])
                for statement in stale_statements:
                    self.assertNotIn(statement, normalized)

    def test_consistency_oracle_detects_canonical_and_mirror_drift(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        dispatcher_text = DISPATCHER.read_text(encoding="utf-8")
        contract = extract_canonical_contract(skill_text, dispatcher_text)
        routes = probe_dispatcher_routes(self.dispatcher)
        mirror = NORMATIVE_MIRRORS[0].read_text(encoding="utf-8")
        self.assertEqual(mirror_contract_errors(mirror, contract, routes), [])

        first_invariant = contract["invariants"][0]
        mirror_drift = mirror.replace(f"`{first_invariant}`", "`drifted_result`", 1)
        self.assertIn(f"`{first_invariant}`", mirror_contract_errors(mirror_drift, contract, routes))

        switch_drift_text = dispatcher_text.replace(
            'os.environ.get("DHF_PREPROMPT_SIMPLIFIED_PROFILES", "1") == "1"',
            'os.environ.get("DHF_PREPROMPT_SIMPLIFIED_PROFILES", "1") == "candidate"',
            1,
        )
        switch_drift_contract = extract_canonical_contract(skill_text, switch_drift_text)
        self.assertIn(
            f"{switch_drift_contract['switch_name']}={switch_drift_contract['switch_enable']}",
            mirror_contract_errors(mirror, switch_drift_contract, routes),
        )

        governed_profile = contract["profiles"][-1]
        skill_drift = skill_text.replace(f"| `{governed_profile}` |", "| `drifted_profile` |", 1)
        with self.assertRaisesRegex(AssertionError, "canonical profile drift"):
            extract_canonical_contract(skill_drift, dispatcher_text)

    def test_public_docs_limit_runtime_helpers_to_matching_governed_signals(self):
        contract = extract_canonical_contract(
            SKILL.read_text(encoding="utf-8"), DISPATCHER.read_text(encoding="utf-8")
        )
        mirrors = registered_public_routing_mirrors()
        manifest_text = SURFACES.read_text(encoding="utf-8")
        self.assertTrue(all(str(mirror.relative_to(ROOT)) in manifest_text for mirror in mirrors))
        for mirror in mirrors:
            with self.subTest(mirror=mirror.relative_to(ROOT)):
                self.assertEqual(
                    public_helper_contract_errors(mirror.read_text(encoding="utf-8"), contract), []
                )

    def test_canonical_delegation_precedes_generic_state_reads_and_public_flows_show_skip_edge(self):
        skill = SKILL.read_text(encoding="utf-8")
        routing = (ROOT / "docs" / "LIFECYCLE_SKILL_ROUTING.md").read_text(encoding="utf-8")
        required = (
            "directly lazy-delegates",
            "must not recover, read shared state, or pre-classify",
        )
        for phrase in required:
            self.assertIn(phrase, skill)
            self.assertIn(phrase, routing)
        self.assertIn("directly delegates at the project boundary", routing)
        self.assertNotIn("delegate after phase selection", routing)
        self.assertNotIn("after the generic router identifies", routing)
        self.assertNotIn("default standard", SURFACES.read_text(encoding="utf-8"))
        for mirror in registered_public_routing_mirrors():
            text = mirror.read_text(encoding="utf-8")
            if "flowchart TD" not in text:
                continue
            with self.subTest(mirror=mirror.relative_to(ROOT)):
                self.assertIn("ProfileDecision", text)
                self.assertRegex(text, r'ProfileDecision\s+--\s+"(?:light|light / standard|light/standard)')

    def test_surfaces_manifest_identifies_canonical_contract_and_rollout_boundary(self):
        contract = extract_canonical_contract(
            SKILL.read_text(encoding="utf-8"), DISPATCHER.read_text(encoding="utf-8")
        )
        routes = probe_dispatcher_routes(self.dispatcher)
        manifest = json.loads(SURFACES.read_text(encoding="utf-8"))
        by_path = {surface["path"]: surface for surface in manifest["surfaces"]}
        skill_role = by_path["codex/skills/delivery-harness-framework"]["role"]
        dispatcher_role = by_path["codex/hooks/dhf_preprompt.py"]["role"]
        for term in ("canonical", *contract["profiles"], "four Result Invariants"):
            self.assertIn(term, skill_role)
        for term in (
            "explicit generic activation",
            "ordinary continue-only",
            "opt-out precedence",
            "ShipQ lazy delegation",
            "simplified repo-source default",
            "default-on",
            "only exact value 1 enables",
            "recognized rollback values 0, false, off, and legacy",
            "all other explicit values fail-safe to legacy with a bounded diagnostic",
            "runtime promotion pending",
            "runtime unsynced",
            f"{contract['switch_name']}={contract['switch_enable']}",
        ):
            self.assertIn(term, dispatcher_role)


if __name__ == "__main__":
    unittest.main()
