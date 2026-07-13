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
    if not RUNNER.is_file():
        raise AssertionError(f"missing Slice 4 paired runner: {RUNNER.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("dhf_simplification_pair", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("Slice 4 paired runner is not importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DhfSimplificationPairTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(RUNNER.is_file(), f"missing Slice 4 paired runner: {RUNNER.relative_to(ROOT)}")
        self.runner = load_runner()
        self.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        self.observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))

    def compare(self, observations=None, measurements=None):
        return self.runner.run_comparison(
            self.corpus,
            observations if observations is not None else self.observations,
            ROOT,
            candidate_measurements=measurements,
        )

    def test_focused_cli_emits_sanitized_machine_readable_green_results(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "compare",
                str(CORPUS),
                "--observations",
                str(OBSERVATIONS),
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["pass"])
        self.assertEqual(payload["scenario_count"], 17)
        self.assertEqual(payload["parity"]["passed_checks"], 85)
        self.assertEqual(payload["parity"]["total_checks"], 85)
        self.assertEqual(payload["parity"]["rate"], 1.0)
        self.assertEqual(payload["governed_under_routing"], [])
        for metric in ("context", "helpers"):
            self.assertEqual(payload["efficiency"][metric]["positive_baseline_sample_count"], 9)
            self.assertGreaterEqual(payload["efficiency"][metric]["median_relative_reduction"], 0.4)
        self.assertEqual(payload["efficiency"]["context"]["zero_baseline_sample_count"], 1)
        self.assertEqual(payload["efficiency"]["helpers"]["zero_baseline_sample_count"], 2)
        self.assertTrue(payload["rollback_smoke"]["pass"])

    def test_expected_oracle_and_observed_outputs_are_independent(self):
        self.assertNotIn("expected", json.dumps(self.observations, sort_keys=True))
        broken_corpus = copy.deepcopy(self.corpus)
        broken_corpus["scenarios"][0]["permission_safety_outcome"]["decision"] = "different_oracle"
        report = self.runner.run_comparison(broken_corpus, self.observations, ROOT)
        self.assertTrue(any("safety_permission_outcome" in error for error in report["errors"]), report)

    def test_runner_rejects_parity_loss(self):
        broken = copy.deepcopy(self.observations)
        broken["observations"][0]["accepted_result_behavior"]["candidate_accepted"] = False
        report = self.compare(broken)
        self.assertTrue(any("accepted_result_behavior" in error for error in report["errors"]), report)

    def test_runner_rejects_governed_under_routing(self):
        measured = self.runner.measure_candidate(self.corpus, ROOT)
        governed = next(item for item in measured if item["id"] == "GOVERNED-REMOTE-DEPLOY")
        governed["selected_profile"] = "standard"
        governed["escalation_signals"] = []
        report = self.compare(measurements=measured)
        self.assertIn("GOVERNED-REMOTE-DEPLOY", report["governed_under_routing"])
        self.assertFalse(report["pass"])

    def test_runner_rejects_efficiency_target_miss(self):
        measured = self.runner.measure_candidate(self.corpus, ROOT)
        for item in measured:
            if item["id"].startswith(("LIGHT-", "STANDARD-")):
                item["injected_context_utf8_bytes_proxy"] = 32803
        report = self.compare(measurements=measured)
        self.assertTrue(any("context median reduction target missed" in error for error in report["errors"]), report)

    def test_runner_rejects_changed_measurement_boundary(self):
        broken = copy.deepcopy(self.observations)
        broken["measurement_boundary"]["context_unit"] = "characters"
        report = self.compare(broken)
        self.assertTrue(any("measurement boundary changed" in error for error in report["errors"]), report)

    def test_runner_rejects_zero_baseline_regression(self):
        measured = self.runner.measure_candidate(self.corpus, ROOT)
        ordinary = next(item for item in measured if item["id"] == "CONTROL-ORDINARY-CONTINUE")
        ordinary["injected_context_utf8_bytes_proxy"] = 1
        ordinary["mandatory_helper_count"] = 1
        report = self.compare(measurements=measured)
        self.assertTrue(any("zero-baseline context regression" in error for error in report["errors"]), report)
        self.assertTrue(any("zero-baseline helpers regression" in error for error in report["errors"]), report)

    def test_recoverability_oracle_rejects_field_loss(self):
        broken = copy.deepcopy(self.observations)
        case = broken["recoverability_cases"][0]
        del case["recovered"]["ownership"]
        report = self.compare(broken)
        self.assertTrue(any("recoverability field loss: ownership" in error for error in report["errors"]), report)

    def test_recoverability_oracle_rejects_stale_to_fresh_promotion(self):
        broken = copy.deepcopy(self.observations)
        case = next(
            item
            for item in broken["recoverability_cases"]
            if item["checkpoint"]["verification_evidence"]["freshness"] == "stale"
        )
        case["recovered"]["verification_evidence"]["freshness"] = "fresh"
        report = self.compare(broken)
        self.assertTrue(any("stale verification promoted to fresh" in error for error in report["errors"]), report)

    def test_sanitized_results_are_reproducible(self):
        self.assertEqual(self.compare(), self.compare())


if __name__ == "__main__":
    unittest.main()
