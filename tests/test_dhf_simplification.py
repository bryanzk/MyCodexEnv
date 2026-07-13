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
CORPUS = ROOT / "tests" / "fixtures" / "dhf_simplification_scenarios.json"
VALIDATOR = ROOT / "scripts" / "validate_dhf_simplification_corpus.py"
CONTRACT = ROOT / "docs" / "plans" / "2026-07-12-dhf-simplification-implementation-contract.md"


def load_validator():
    if not VALIDATOR.is_file():
        raise AssertionError(f"missing Slice 0 validator: {VALIDATOR.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("dhf_simplification_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("Slice 0 validator is not importable")
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


if __name__ == "__main__":
    unittest.main()
