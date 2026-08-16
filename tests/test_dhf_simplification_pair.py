#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_dhf_simplification_pair.py"
CORPUS = ROOT / "tests" / "fixtures" / "dhf_simplification_scenarios.json"
OBSERVATIONS = ROOT / "tests" / "fixtures" / "dhf_simplification_observations.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("dhf_simplification_pair", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("Slice 4 paired runner is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DhfSimplificationPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runner = load_runner()
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))
        cls._candidate_measurements = runner.measure_candidate(corpus, ROOT)
        cls._recovery_results = runner.run_recoverability_cases(observations, ROOT)

    def setUp(self):
        self.runner = load_runner()
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))

    def measurements(self):
        return copy.deepcopy(type(self)._candidate_measurements)

    def recovery_results(self):
        return copy.deepcopy(type(self)._recovery_results)

    def compare(self, *, corpus=None, observations=None, measurements=None, recovery_results=None, fresh=False):
        if not fresh and corpus is None and measurements is None:
            measurements = self.measurements()
        if not fresh and observations is None and recovery_results is None:
            recovery_results = self.recovery_results()
        return self.runner.run_comparison(
            corpus if corpus is not None else self.corpus,
            observations if observations is not None else self.observations,
            ROOT,
            candidate_measurements=measurements,
            recovery_results=recovery_results,
        )

    def test_focused_cli_generates_all_five_dimensions_from_real_paths(self):
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "compare", str(CORPUS), "--observations", str(OBSERVATIONS), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["pass"])
        expected_parity = {"dimensions": list(self.runner.DIMENSIONS), "passed_checks": 85, "total_checks": 85, "rate": 1.0}
        self.assertEqual(payload["routing_parity"], expected_parity)
        self.assertEqual(payload["actual_outcome_parity"], expected_parity)
        self.assertEqual(payload["governed_under_routing"], [])
        self.assertEqual(payload["efficiency"]["context"]["positive_baseline_sample_count"], 9)
        self.assertEqual(payload["efficiency"]["helpers"]["positive_baseline_sample_count"], 9)
        self.assertGreaterEqual(payload["efficiency"]["context"]["median_relative_reduction"], 0.4)
        self.assertGreaterEqual(payload["efficiency"]["helpers"]["median_relative_reduction"], 0.4)
        self.assertTrue(payload["rollback_smoke"]["pass"])
        self.assertEqual(payload["efficiency"]["context"]["positive_baseline_sample_count"], 9)
        self.assertEqual(payload["efficiency"]["helpers"]["positive_baseline_sample_count"], 9)
        self.assertRegex(payload["identities"]["helper_registry_identity"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(payload["identities"]["corpus_identity"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(payload["identities"]["runner_identity"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            payload["identities"]["promotion_candidate_manifest"]["manifest_sha256"],
            r"^[0-9a-f]{64}$",
        )
        state = payload["runtime_boundary"]["runtime_state"]
        self.assertIn(state, {"source_stage_unsynced", "runtime_promoted"})
        if state == "source_stage_unsynced":
            self.assertEqual(payload["runtime_boundary"]["changed_paths"], [])
            self.assertTrue(payload["runtime_boundary"]["promotion_difference_paths"])
        else:
            self.assertTrue(payload["runtime_boundary"]["changed_paths"])
            self.assertEqual(payload["runtime_boundary"]["promotion_difference_paths"], [])
        self.assertTrue(payload["runtime_boundary"]["gate_pass"])
        self.assertTrue(payload["acceptance_trace_gates"]["gate_pass"])

    def test_runner_rejects_manifest_producer_and_identity_drift(self):
        mutations = (
            lambda value: value["promotion_candidate_manifest"].__setitem__("manifest_sha256", "0" * 64),
            lambda value: value["runner_identity"].__setitem__("sha256", "0" * 64),
            lambda value: value["producer_evidence"].pop("PRODUCER-AC-16-S4-1"),
            lambda value: value["base_expected_runtime_manifest"].__setitem__("aggregate_sha256", "0" * 64),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                observations = copy.deepcopy(self.observations)
                mutate(observations)
                report = self.compare(observations=observations)
                self.assertFalse(report["pass"])
                self.assertTrue(report["errors"])

        observations = copy.deepcopy(self.observations)
        producer = observations["producer_evidence"]["PRODUCER-AC-16-S4-1"]
        producer["evidence"]["passed_assertion_count"] -= 1
        report = self.compare(observations=observations)
        self.assertFalse(report["pass"])
        self.assertFalse(report["acceptance_trace_gates"]["acceptance_gates"]["AC-16"])

    def test_transition_identity_pins_current_runner_and_managed_source(self):
        identities = self.runner.identity_bundle(self.corpus, ROOT)
        identity = self.runner.load_transition_identity(ROOT)
        self.assertEqual(self.runner.validate_transition_identity(identity, identities), [])

        broken_runner = copy.deepcopy(identity)
        broken_runner["runner_sha256"] = "0" * 64
        self.assertTrue(
            any("runner" in error for error in self.runner.validate_transition_identity(broken_runner, identities))
        )

        broken_source = copy.deepcopy(identity)
        broken_source["managed_source_hashes_sha256"] = "0" * 64
        self.assertTrue(
            any("managed source" in error for error in self.runner.validate_transition_identity(broken_source, identities))
        )

        broken_authorization = copy.deepcopy(identity)
        broken_authorization["authorized_slices"] = [5]
        self.assertTrue(
            any("authorized slices" in error for error in self.runner.validate_transition_identity(broken_authorization, identities))
        )

    def test_runner_rejects_semantic_producer_forgery_even_with_recomputed_digest(self):
        def resign(record):
            record["evidence_sha256"] = hashlib.sha256(
                json.dumps(
                    record["evidence"],
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ).hexdigest()

        def shrink_assertions(evidence):
            evidence["assertion_count"] = 1
            evidence["passed_assertion_count"] = 1

        def corrupt_snapshot(evidence):
            evidence["current_runtime_snapshot"]["records"][0]["sha256"] = "0" * 64

        def stale_timestamp(evidence):
            evidence["current_runtime_snapshot"]["captured_at"] = "2026-07-12T00:00:00Z"

        for mutate in (shrink_assertions, corrupt_snapshot, stale_timestamp):
            with self.subTest(mutate=mutate):
                observations = copy.deepcopy(self.observations)
                record = observations["producer_evidence"]["PRODUCER-AC-16-S4-1"]
                mutate(record["evidence"])
                resign(record)
                report = self.compare(observations=observations)
                self.assertFalse(report["pass"])
                self.assertFalse(
                    report["acceptance_trace_gates"]["acceptance_gates"]["AC-16"]
                )

    def test_observation_fixture_contains_no_handwritten_pass_booleans(self):
        forbidden = {
            "baseline_accepted", "candidate_accepted", "baseline_preserved", "candidate_preserved",
            "baseline_pass", "candidate_pass", "baseline_fields", "candidate_fields",
        }

        def visit(value):
            if isinstance(value, dict):
                self.assertTrue(forbidden.isdisjoint(value), forbidden & set(value))
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(self.observations)

    def test_observation_fixture_contains_actual_raw_paired_outputs_and_provenance(self):
        for observation in self.observations["observations"]:
            with self.subTest(scenario=observation["id"]):
                for profile in ("baseline", "candidate"):
                    capture = observation[f"{profile}_capture"]
                    self.assertEqual(capture["provenance"]["capture_mode"], "deterministic_local_bounded_execution")
                    self.assertTrue(capture["provenance"]["capture_version"])
                    self.assertTrue(capture["provenance"]["source_contract"])
                    self.assertRegex(capture["provenance"]["context_sha256"], r"^[0-9a-f]{64}$")
                    self.assertGreaterEqual(capture["provenance"]["context_utf8_bytes"], 0)
                    self.assertRegex(capture["provenance"]["dispatcher_sha256"], r"^[0-9a-f]{64}$")
                    self.assertIn("dispatcher_route", capture["provenance"])
                    raw = capture["raw_task_output"]
                    self.assertIsInstance(raw["result"], str)
                    self.assertIsInstance(raw["scope_and_constraints"], list)
                    self.assertIsInstance(raw["verification_receipt"], dict)
                    self.assertIn("permission_outcome", raw)
                    self.assertEqual(raw["execution_policy"]["context_sha256"], capture["provenance"]["context_sha256"])

        activated = next(item for item in self.observations["observations"] if item["id"] == "STANDARD-LOCAL-FEATURE")
        self.assertNotEqual(
            activated["baseline_capture"]["provenance"]["context_sha256"],
            activated["candidate_capture"]["provenance"]["context_sha256"],
        )
        self.assertEqual(activated["baseline_capture"]["provenance"]["base_commit"], self.runner.BASELINE_BASE_SHA)
        self.assertTrue(activated["candidate_capture"]["provenance"]["profile_contract"])
        self.assertEqual(
            activated["candidate_capture"]["provenance"]["source_contract"],
            "simplified@isolated-promotion-bytes",
        )

    def test_context_drives_execution_policy_and_permission_oracle_is_not_capture_input(self):
        scenario = next(item for item in self.corpus["scenarios"] if item["id"] == "GOVERNED-REMOTE-DEPLOY")
        contexts = self.runner.capture_contract_contexts(scenario, ROOT)
        candidate = contexts["candidate"]
        policy = self.runner.derive_execution_policy(
            scenario["sanitized_prompt"], candidate["context"], candidate["profile_contract"]
        )
        self.assertEqual(policy["action"], "block_pending_authorization")
        self.assertIn("Deployment Readiness Gate", policy["gates"])

        corrupted = candidate["context"].replace("Deployment Readiness Gate", "")
        corrupted_policy = self.runner.derive_execution_policy(
            scenario["sanitized_prompt"], corrupted, None
        )
        self.assertNotEqual(corrupted_policy, policy)
        self.assertEqual(corrupted_policy["action"], "fail_closed_missing_contract")

        changed_oracle = copy.deepcopy(scenario)
        changed_oracle["permission_safety_outcome"]["decision"] = "execute_without_authorization"
        original_output = self.runner.execute_bounded_scenario(scenario, candidate)
        changed_output = self.runner.execute_bounded_scenario(changed_oracle, candidate)
        self.assertEqual(original_output["permission_outcome"], changed_output["permission_outcome"])
        self.assertNotEqual(original_output["permission_outcome"], "execute_without_authorization")

    def test_prompt_and_captured_contract_drive_outcome_not_scenario_type(self):
        scenario = next(item for item in self.corpus["scenarios"] if item["id"] == "STANDARD-LOCAL-FEATURE")
        candidate = self.runner.capture_contract_contexts(scenario, ROOT)["candidate"]
        original = self.runner.execute_bounded_scenario(scenario, candidate)

        mismatched_type = copy.deepcopy(scenario)
        mismatched_type["scenario_type"] = "explanation"
        mismatched = self.runner.execute_bounded_scenario(mismatched_type, candidate)
        for field in ("result", "scope_and_constraints", "permission_outcome", "changed_files", "execution_policy"):
            self.assertEqual(original[field], mismatched[field])
        self.assertTrue(
            any(
                "prompt/type mismatch" in error
                for error in self.runner.assertion_errors(mismatched_type, original, "candidate")
            )
        )

        mismatched_prompt = copy.deepcopy(scenario)
        mismatched_prompt["sanitized_prompt"] = "Explain why this pure function is deterministic; do not edit files."
        prompt_driven = self.runner.execute_bounded_scenario(mismatched_prompt, candidate)
        self.assertNotEqual(original["result"], prompt_driven["result"])
        self.assertTrue(self.runner.assertion_errors(scenario, prompt_driven, "candidate"))

    def test_capture_validator_does_not_call_outcome_generation_oracle(self):
        scenario = next(item for item in self.corpus["scenarios"] if item["id"] == "STANDARD-LOCAL-FEATURE")
        capture = copy.deepcopy(
            next(item for item in self.observations["observations"] if item["id"] == scenario["id"])[
                "candidate_capture"
            ]
        )
        expected = {
            field: capture["provenance"][field]
            for field in ("dispatcher_sha256", "skill_sha256")
        }

        def forbidden_same_oracle(*_args, **_kwargs):
            raise AssertionError("validator called the outcome generation oracle")

        self.runner.derive_execution_policy = forbidden_same_oracle
        self.assertEqual(
            self.runner.capture_validation_errors(scenario, capture, "candidate", expected),
            [],
        )

    def test_runner_rejects_context_hash_or_contract_corruption_and_reports_each_side_assertions(self):
        observations = copy.deepcopy(self.observations)
        item = next(row for row in observations["observations"] if row["id"] == "STANDARD-LOCAL-FEATURE")
        item["candidate_capture"]["provenance"]["context_sha256"] = "0" * 64
        report = self.compare(observations=observations)
        self.assertTrue(any("candidate context" in error for error in report["errors"]), report)

        observations = copy.deepcopy(self.observations)
        item = next(row for row in observations["observations"] if row["id"] == "GOVERNED-REMOTE-DEPLOY")
        item["candidate_capture"]["provenance"]["profile_contract"] = {}
        report = self.compare(observations=observations)
        self.assertTrue(any("candidate contract" in error for error in report["errors"]), report)

        clean = self.compare()
        raw = next(row for row in clean["raw_results"] if row["id"] == "STANDARD-LOCAL-FEATURE")
        self.assertEqual(raw["assertion_errors"], {"baseline": [], "candidate": []})

    def test_runner_rejects_valid_looking_but_stale_source_hashes(self):
        for profile, field in (("baseline", "skill_sha256"), ("candidate", "dispatcher_sha256")):
            with self.subTest(profile=profile, field=field):
                observations = copy.deepcopy(self.observations)
                item = next(row for row in observations["observations"] if row["id"] == "STANDARD-LOCAL-FEATURE")
                item[f"{profile}_capture"]["provenance"][field] = "f" * 64
                report = self.compare(observations=observations)
                self.assertFalse(report["pass"])
                self.assertTrue(any(f"{profile} source hash mismatch" in error for error in report["errors"]), report)

    def test_machine_output_separates_routing_and_actual_outcome_parity(self):
        report = self.compare()
        self.assertEqual(report["routing_parity"]["rate"], 1.0)
        self.assertEqual(report["actual_outcome_parity"]["rate"], 1.0)
        self.assertNotIn("parity", report)

    def test_runner_rejects_raw_result_permission_receipt_and_private_content_mutations(self):
        mutations = (
            ("LIGHT-EXPLANATION", "candidate_capture", "result", ""),
            ("GOVERNED-REMOTE-DEPLOY", "candidate_capture", "permission_outcome", "executed_without_authorization"),
            ("STANDARD-LOCAL-FEATURE", "candidate_capture", "verification_receipt", {"command": "x"}),
            ("GOVERNED-EXTERNAL-CAPTURE", "candidate_capture", "result", "SECRET_TOKEN=forbidden-private-value"),
            ("LIGHT-ONE-FILE-SAFE", "candidate_capture", "dirty_snapshot", []),
        )
        for scenario_id, capture_name, field, value in mutations:
            with self.subTest(field=field):
                observations = copy.deepcopy(self.observations)
                item = next(row for row in observations["observations"] if row["id"] == scenario_id)
                item[capture_name]["raw_task_output"][field] = value
                report = self.compare(observations=observations)
                self.assertFalse(report["pass"])
                self.assertTrue(any("actual outcome" in error or "assertion" in error for error in report["errors"]), report)

    def test_runner_rejects_unimplemented_or_false_result_assertions(self):
        for mutation in ("unknown_type", "false_expected"):
            with self.subTest(mutation=mutation):
                corpus = copy.deepcopy(self.corpus)
                check = corpus["scenarios"][0]["result_acceptance_checks"][0]
                if mutation == "unknown_type":
                    check["type"] = "copy_expected_text"
                else:
                    check["expected"] = "not present in actual bounded output"
                report = self.compare(corpus=corpus)
                self.assertFalse(report["pass"])
                self.assertTrue(any("assertion" in error for error in report["errors"]), report)

    def test_run_comparison_invokes_canonical_corpus_validation(self):
        broken = copy.deepcopy(self.corpus)
        broken["schema_version"] = 99
        report = self.compare(corpus=broken)
        self.assertTrue(any("schema_version must be 1" in error for error in report["errors"]), report)

    def test_runner_rejects_shared_boundary_drift_and_cohort_loss(self):
        broken_observations = copy.deepcopy(self.observations)
        broken_observations["measurement_boundary"]["context_unit"] = "characters"
        self.assertTrue(any("measurement boundary" in error for error in self.compare(observations=broken_observations)["errors"]))

        broken_corpus = copy.deepcopy(self.corpus)
        scenario = next(item for item in broken_corpus["scenarios"] if item["id"] == "STANDARD-LOCAL-FEATURE")
        scenario["cohort_status"] = "routing_control_excluded"
        report = self.compare(corpus=broken_corpus)
        self.assertTrue(any("efficiency cohort" in error or "positive sample count" in error for error in report["errors"]), report)

    def test_runner_rejects_result_route_or_profile_loss(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "STANDARD-LOCAL-FEATURE")
        item["selected_profile"] = "light"
        report = self.compare(measurements=measured)
        self.assertTrue(any("accepted_result_behavior" in error for error in report["errors"]), report)

    def test_runner_rejects_safety_helper_and_field_loss(self):
        mutations = (
            ("observed_mandatory_helpers", "harness_report.py"),
            ("observed_required_output_fields", "authorization_state"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                measured = self.measurements()
                item = next(row for row in measured if row["id"] == "GOVERNED-REMOTE-DEPLOY")
                item[field].remove(value)
                if field == "observed_mandatory_helpers":
                    item["mandatory_helper_count"] -= 1
                report = self.compare(measurements=measured)
                self.assertTrue(any("safety_permission_outcome" in error for error in report["errors"]), report)

    def test_governed_profile_mutation_is_reported_as_under_routing(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "GOVERNED-REMOTE-DEPLOY")
        item["selected_profile"] = "standard"
        report = self.compare(measurements=measured)
        self.assertIn("GOVERNED-REMOTE-DEPLOY", report["governed_under_routing"])
        self.assertFalse(report["pass"])

    def test_governed_primary_signal_mutation_is_reported_as_under_routing(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "GOVERNED-REMOTE-DEPLOY")
        item["escalation_signals"].remove("remote_or_deployment_action")
        report = self.compare(measurements=measured)
        self.assertIn("GOVERNED-REMOTE-DEPLOY", report["governed_under_routing"])
        self.assertFalse(report["pass"])

    def test_governed_authoritative_gate_loss_is_reported_as_under_routing(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "GOVERNED-REMOTE-DEPLOY")
        item["observed_authoritative_gates"].remove("Deployment Readiness Gate")
        report = self.compare(measurements=measured)
        self.assertIn("GOVERNED-REMOTE-DEPLOY", report["governed_under_routing"])
        self.assertTrue(any("safety_permission_outcome" in error for error in report["errors"]), report)
        self.assertLess(report["actual_outcome_parity"]["rate"], 1.0)
        self.assertFalse(report["pass"])

    def test_runner_rejects_receipt_contract_loss(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "STANDARD-LOCAL-FEATURE")
        item["additional_context"] = item["additional_context"].replace("timestamp", "")
        report = self.compare(measurements=measured)
        self.assertTrue(any("verification_receipt_completeness" in error for error in report["errors"]), report)

    def test_runner_rejects_real_dirty_worktree_snapshot_change(self):
        measured = self.measurements()
        item = next(row for row in measured if row["id"] == "LIGHT-ONE-FILE-SAFE")
        item["dirty_after"] = {"status": [], "content_sha256": "changed"}
        report = self.compare(measurements=measured)
        self.assertTrue(any("dirty_worktree_preservation" in error for error in report["errors"]), report)

    def test_runner_rejects_recoverability_field_loss_and_stale_promotion(self):
        recovered = self.recovery_results()
        first = next(iter(recovered.values()))
        del first["ownership"]
        report = self.compare(recovery_results=recovered)
        self.assertTrue(any("recoverability field loss: ownership" in error for error in report["errors"]), report)

        recovered = self.recovery_results()
        stale = next(value for value in recovered.values() if value["verification_evidence"]["freshness"] == "stale")
        stale["verification_evidence"]["freshness"] = "fresh"
        report = self.compare(recovery_results=recovered)
        self.assertTrue(any("stale verification promoted to fresh" in error for error in report["errors"]), report)

    def test_checkpoint_artifact_roundtrip_is_self_contained_and_preserves_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            docs = repo / "docs"
            docs.mkdir(parents=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repo, check=True)
            (docs / "repo-index.md").write_text("# Fixture\n", encoding="utf-8")
            state = docs / "harness-state.md"
            state.write_text(
                "# Harness State\n\n- phase: research\n- next_safe_task: none\n"
                "- latest_checkpoint: none\n- latest_verification: none\n- blocked_sources: none\n\n## State Log\n",
                encoding="utf-8",
            )
            checkpoint = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_checkpoint.py"), "append",
                 "--repo-root", str(repo), "--phase", "development", "--summary", "roundtrip",
                 "--constraint", "no_remote", "--constraint", "preserve_dirty",
                 "--ownership-json", '{"boundary":"task_owned_only"}',
                 "--next-action-json", '{"command":"python3 focused.py","args":["--check"]}',
                 "--verification-command", "python3 focused.py --check", "--verification-exit-code", "0",
                 "--verification-key-output", "1 passed", "--verification-timestamp", "2026-07-12T00:00:00Z",
                 "--verification-freshness", "stale", "--next-safe-task", "python3 focused.py --check"],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            recovered = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_recover.py"), "--repo-root", str(repo),
                 "--codex-home", str(Path(tmp) / "empty-codex-home"), "--json"],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            payload = json.loads(recovered.stdout)
            self.assertEqual(payload["constraints"], ["no_remote", "preserve_dirty"])
            self.assertEqual(payload["ownership"], {"boundary": "task_owned_only"})
            self.assertEqual(payload["next_action"], {"command": "python3 focused.py", "args": ["--check"]})
            self.assertEqual(
                payload["verification_evidence"],
                {"command": "python3 focused.py --check", "exit_code": 0, "key_output": "1 passed",
                 "timestamp": "2026-07-12T00:00:00Z", "freshness": "stale"},
            )

    def test_checkpoint_rejects_invalid_structured_fields_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            docs = repo / "docs"
            docs.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            state = docs / "harness-state.md"
            original = "# Harness State\n\n- phase: research\n- next_safe_task: none\n\n## State Log\n"
            state.write_text(original, encoding="utf-8")
            base = [sys.executable, str(ROOT / "scripts" / "harness_checkpoint.py"), "append",
                    "--repo-root", str(repo), "--phase", "development", "--summary", "invalid",
                    "--verification-command", "python3 check.py", "--verification-exit-code", "0",
                    "--verification-key-output", "ok", "--next-safe-task", "python3 check.py"]
            invalid_args = (
                ["--next-action-json", '{"command":""}'],
                ["--next-action-json", '{"command":"python3 check.py","args":"--bad"}'],
                ["--constraint", ""],
                ["--ownership-json", '{"boundary":1}'],
            )
            for extra in invalid_args:
                with self.subTest(extra=extra):
                    proc = subprocess.run(base + extra, cwd=repo, capture_output=True, text=True, check=False)
                    self.assertEqual(proc.returncode, 1, proc.stderr)
                    self.assertIn("ERROR:", proc.stderr)
                    self.assertEqual(state.read_text(encoding="utf-8"), original)

    def test_checkpoint_writer_accepts_only_exact_verified_or_handoff_unverified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            docs = repo / "docs"
            docs.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            state = docs / "harness-state.md"
            base_state = "# Harness State\n\n- phase: research\n- next_safe_task: none\n\n## State Log\n"
            state.write_text(base_state, encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts" / "harness_checkpoint.py"), "append",
                       "--repo-root", str(repo), "--phase", "handoff", "--summary", "blocked",
                       "--allow-unverified", "--blocker", "credential required", "--next-safe-task", "ask owner"]
            valid = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            line = next(line for line in reversed(state.read_text(encoding="utf-8").splitlines()) if line.startswith("- checkpoint_data: "))
            artifact = json.loads(line.removeprefix("- checkpoint_data: "))
            self.assertEqual(
                artifact["verification_evidence"],
                {"command": None, "exit_code": None, "key_output": None,
                 "timestamp": artifact["verification_evidence"]["timestamp"], "freshness": "unknown"},
            )

            state.write_text(base_state, encoding="utf-8")
            invalid = subprocess.run(
                [*command[:command.index("handoff")], "development", *command[command.index("handoff") + 1:]],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertEqual(state.read_text(encoding="utf-8"), base_state)

    def test_recover_distinguishes_absent_malformed_checkpoint_and_preserves_latest_event_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            docs = repo / "docs"
            docs.mkdir(parents=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (docs / "repo-index.md").write_text("# Index\n", encoding="utf-8")
            state = docs / "harness-state.md"
            base_state = "# Harness State\n\n- phase: research\n- next_safe_task: none\n- blocked_sources: none\n\n## State Log\n"
            state.write_text(base_state, encoding="utf-8")
            absent = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_recover.py"), "--repo-root", str(repo), "--codex-home", str(Path(tmp) / "codex"), "--json"],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(absent.returncode, 0, absent.stderr)
            self.assertEqual(json.loads(absent.stdout)["checkpoint_status"], "absent")

            for marker, expected in (("{bad-json", "malformed"), ('{"schema":"wrong"}', "schema-invalid")):
                with self.subTest(expected=expected):
                    state.write_text(base_state + f"- checkpoint_data: {marker}\n", encoding="utf-8")
                    proc = subprocess.run(
                        [sys.executable, str(ROOT / "scripts" / "harness_recover.py"), "--repo-root", str(repo), "--codex-home", str(Path(tmp) / "codex"), "--json"],
                        cwd=repo, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(proc.returncode, 1)
                    self.assertIn(expected, proc.stderr)

            state.write_text(base_state, encoding="utf-8")
            checkpoint = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_checkpoint.py"), "append", "--repo-root", str(repo),
                 "--phase", "development", "--summary", "valid", "--constraint", "no_remote",
                 "--ownership-json", '{"boundary":"task"}', "--next-action-json", '{"command":"python3 next.py"}',
                 "--verification-command", "python3 checkpoint.py", "--verification-exit-code", "0",
                 "--verification-key-output", "checkpoint", "--verification-timestamp", "2026-07-12T00:00:00Z",
                 "--verification-freshness", "stale", "--next-safe-task", "python3 next.py"],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            evidence_dir = Path(tmp) / "codex" / "harness" / "evidence"
            evidence_dir.mkdir(parents=True)
            event = {"event_type":"verification_result","evidence_kind":"decision","cwd":str(repo),
                     "command":"python3 event.py","exit_code":0,"key_output":"event","timestamp":"2026-07-13T00:00:00Z"}
            (evidence_dir / "event.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            recovered = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "harness_recover.py"), "--repo-root", str(repo), "--codex-home", str(Path(tmp) / "codex"), "--json"],
                cwd=repo, capture_output=True, text=True, check=False,
            )
            payload = json.loads(recovered.stdout)
            self.assertEqual(payload["checkpoint_status"], "valid")
            self.assertEqual(payload["verification_evidence"]["command"], "python3 checkpoint.py")
            self.assertEqual(payload["latest_verification"]["command"], "python3 event.py")

    def test_recover_rejects_structurally_complete_but_semantically_invalid_checkpoint(self):
        invalid_artifacts = (
            {"schema":"dhf_checkpoint_v1","phase":"bogus","constraints":["no_remote"],"ownership":{"boundary":"task"},"next_action":{"command":"python3 next.py"},"verification_evidence":{"command":"python3 check.py","exit_code":0,"key_output":"ok","timestamp":"2026-07-12T00:00:00Z","freshness":"fresh"}},
            {"schema":"dhf_checkpoint_v1","phase":"development","constraints":[""],"ownership":{"boundary":"task"},"next_action":{"command":"python3 next.py"},"verification_evidence":{"command":"python3 check.py","exit_code":0,"key_output":"ok","timestamp":"2026-07-12T00:00:00Z","freshness":"fresh"}},
            {"schema":"dhf_checkpoint_v1","phase":"development","constraints":["no_remote"],"ownership":{},"next_action":{"command":"","args":[]},"verification_evidence":{"command":"python3 check.py","exit_code":"0","key_output":"ok","timestamp":"2026-07-12T00:00:00Z","freshness":"fresh"}},
            {"schema":"dhf_checkpoint_v1","phase":"development","constraints":[],"ownership":{},"next_action":{"command":"ask owner"},"verification_evidence":{"command":None,"exit_code":None,"key_output":None,"timestamp":"2026-07-12T00:00:00Z","freshness":"unknown"}},
            {"schema":"dhf_checkpoint_v1","phase":"handoff","constraints":[],"ownership":{},"next_action":{"command":"ask owner"},"verification_evidence":{"command":None,"exit_code":0,"key_output":None,"timestamp":"2026-07-12T00:00:00Z","freshness":"unknown"}},
            {"schema":"dhf_checkpoint_v1","phase":"handoff","constraints":[],"ownership":{},"next_action":{"command":"ask owner"},"verification_evidence":{"command":None,"exit_code":None,"key_output":"invented","timestamp":"2026-07-12T00:00:00Z","freshness":"unknown"}},
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            docs = repo / "docs"
            docs.mkdir(parents=True)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (docs / "repo-index.md").write_text("# Index\n", encoding="utf-8")
            base = "# Harness State\n\n- phase: research\n- next_safe_task: none\n- blocked_sources: none\n\n## State Log\n"
            state = docs / "harness-state.md"
            for artifact in invalid_artifacts:
                with self.subTest(artifact=artifact):
                    state.write_text(
                        base + "- checkpoint_data: " + json.dumps(artifact, separators=(",", ":")) + "\n",
                        encoding="utf-8",
                    )
                    proc = subprocess.run(
                        [sys.executable, str(ROOT / "scripts" / "harness_recover.py"), "--repo-root", str(repo), "--codex-home", str(Path(tmp) / "codex"), "--json"],
                        cwd=repo, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertIn("schema-invalid checkpoint_data recovery blocker", proc.stderr)

    def test_runner_rejects_efficiency_target_and_zero_baseline_regression(self):
        measured = self.measurements()
        for item in measured:
            if item["id"].startswith(("LIGHT-", "STANDARD-")):
                item["injected_context_utf8_bytes_proxy"] = 32803
        report = self.compare(measurements=measured)
        self.assertTrue(any("context median reduction target missed" in error for error in report["errors"]), report)

        measured = self.measurements()
        ordinary = next(item for item in measured if item["id"] == "CONTROL-ORDINARY-CONTINUE")
        ordinary["injected_context_utf8_bytes_proxy"] = 1
        ordinary["mandatory_helper_count"] = 1
        report = self.compare(measurements=measured)
        self.assertTrue(any("zero-baseline context regression" in error for error in report["errors"]), report)
        self.assertTrue(any("zero-baseline helpers regression" in error for error in report["errors"]), report)

    def test_sanitized_results_are_reproducible(self):
        first = self.compare(fresh=True)
        second = self.compare(fresh=True)
        first_timestamp = first["runtime_boundary"]["current_runtime_snapshot"].pop("captured_at")
        second_timestamp = second["runtime_boundary"]["current_runtime_snapshot"].pop("captured_at")
        self.assertRegex(first_timestamp, r"Z$")
        self.assertRegex(second_timestamp, r"Z$")
        self.assertEqual(first, second)

    def test_pair_accepts_exact_runtime_promotion_without_rewriting_slice4_history(self):
        evidence = self.runner._evidence_module(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with mock.patch.object(evidence.Path, "home", return_value=home):
                for source_path in evidence.managed_source_paths(ROOT):
                    target = (
                        home / ".codex" / "hooks" / "dhf_preprompt.py"
                        if source_path == evidence.HOOK_SOURCE
                        else home
                        / ".codex"
                        / "skills"
                        / "delivery-harness-framework"
                        / Path(source_path).relative_to(evidence.SKILL_ROOT)
                    )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((ROOT / source_path).read_bytes())
                promoted = evidence.runtime_boundary_evidence(ROOT)
            with mock.patch.object(self.runner, "_evidence_module", return_value=evidence), mock.patch.object(
                evidence, "runtime_boundary_evidence", return_value=promoted
            ):
                report = self.compare(fresh=True)
        self.assertTrue(report["pass"], report["errors"])
        self.assertEqual(report["runtime_boundary"]["runtime_state"], "runtime_promoted")
        stored = self.observations["producer_evidence"]["PRODUCER-AC-16-S4-1"]["evidence"]
        self.assertEqual(stored["changed_paths"], [])
        self.assertTrue(stored["promotion_difference_paths"])


if __name__ == "__main__":
    unittest.main()
