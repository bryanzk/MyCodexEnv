#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
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
        self.assertEqual(payload["parity"], {"dimensions": list(self.runner.DIMENSIONS), "passed_checks": 85, "total_checks": 85, "rate": 1.0})
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
