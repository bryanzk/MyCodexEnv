#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "dhf_simplification_scenarios.json"
VALIDATOR = ROOT / "scripts" / "validate_dhf_simplification_corpus.py"
CONTRACT = ROOT / "docs" / "plans" / "2026-07-12-dhf-simplification-implementation-contract.md"
DISPATCHER = ROOT / "codex" / "hooks" / "dhf_preprompt.py"
HELPER_CLIS = [
    ROOT / "scripts" / "harness_recover.py",
    ROOT / "scripts" / "harness_env_probe.py",
    ROOT / "scripts" / "harness_requirements.py",
    ROOT / "scripts" / "harness_report.py",
    ROOT / "scripts" / "harness_agent_team.py",
    ROOT / "scripts" / "harness_checkpoint.py",
]


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

        broken = copy.deepcopy(self.corpus)
        broken["test_catalog"]["TEST-SCHEMA-COUNTS"] = "tests/test_dhf_simplification.py::load_validator"
        errors = self.validator.validate_corpus(broken, CONTRACT)
        self.assertTrue(any("does not resolve to a test callable" in error for error in errors), errors)

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
            response, route = self.dispatcher.route_response(
                {"cwd": tmp, "prompt": "Use complex analysis to explain this deterministic function."}
            )
            self.assertEqual(route, "generic-activated:light")
            context = response["hookSpecificOutput"]["additionalContext"]
            self.assertIn("profile=light", context)
            self.assertNotIn(marker, context)
            self.assertNotIn("Traceback", context)

    def test_feature_switch_off_exercises_legacy_full_skill_route(self):
        marker = "LEGACY_FULL_SKILL_MARKER"
        with __import__("tempfile").TemporaryDirectory() as tmp:
            skill = Path(tmp) / "DHF.md"
            skill.write_text(marker, encoding="utf-8")
            env = os.environ.copy()
            env.update(
                {
                    "DHF_PREPROMPT_SIMPLIFIED_PROFILES": "0",
                    "DHF_PREPROMPT_SKILL": str(skill),
                    "DHF_PREPROMPT_SHIPQ_ROOT": str(Path(tmp) / "ShipQ"),
                }
            )
            proc = subprocess.run(
                [sys.executable, str(DISPATCHER)],
                input=json.dumps({"cwd": tmp, "prompt": "complex local feature"}),
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn(marker, payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("diagnostic=generic-activated:legacy", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
