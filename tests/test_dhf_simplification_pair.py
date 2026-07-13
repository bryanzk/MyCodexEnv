#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
    def setUp(self):
        self.runner = load_runner()
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))

    def measurements(self):
        return self.runner.measure_candidate(self.corpus, ROOT)

    def recovery_results(self):
        return self.runner.run_recoverability_cases(self.observations, ROOT)

    def compare(self, *, corpus=None, observations=None, measurements=None, recovery_results=None):
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
                    raw = capture["raw_task_output"]
                    self.assertIsInstance(raw["result"], str)
                    self.assertIsInstance(raw["scope_and_constraints"], list)
                    self.assertIsInstance(raw["verification_receipt"], dict)
                    self.assertIn("permission_outcome", raw)

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
        self.assertEqual(self.compare(), self.compare())


if __name__ == "__main__":
    unittest.main()
