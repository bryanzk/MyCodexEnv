#!/usr/bin/env python3
"""Validate calibrated score-convergence contracts for committee review skills."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMMITTEE_REQUIRED_TERMS = (
    "review_rubric",
    "acceptance_ledger",
    "rating caps",
    "max_rounds",
    "blind final review",
    "prior rating",
    "rubric_challenges",
    "residual_risks",
)

DUAL_REQUIRED_TERMS = (
    "review_rubric",
    "acceptance_ledger",
    "blind final review",
    "Do not average",
    "prior rating",
    "new_material_findings",
    "rubric_challenges",
    "residual_risks",
)

PROTOCOL_REQUIRED_TERMS = (
    "Blind final review",
    "prior score",
    "review_rubric_coverage",
    "acceptance_ledger_updates",
    "new_material_findings",
    "rubric_challenges",
    "rating_rationale",
    "residual_risks",
)

COMMITTEE_FORBIDDEN_TERMS = (
    "`committee.rating >= target` and fresh verification passes",
)

DUAL_FORBIDDEN_TERMS = (
    "Codex says no further changes are needed and verification passes",
    "Claude says no further changes are needed and Codex accepts that result",
    "Stop because Codex or Claude explicitly says no further modification is needed",
)

PROTOCOL_FORBIDDEN_TERMS = (
    "Current Codex result:",
    "<Codex committee findings, revisions, and verification evidence>",
)

COMMITTEE_REQUIRED_EVALS = {
    "end-to-end-committee-generates-rubric-ledger",
    "rating-contract-severity-caps",
    "blind-final-review-no-score-anchoring",
    "loop-control-max-rounds",
}

DUAL_REQUIRED_EVALS = {
    "end-to-end-dual-ledger-score-convergence",
    "blind-final-review-hides-prior-scores",
    "disagreement-no-score-averaging",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def load_eval_ids(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    evals = data.get("evals")
    require(isinstance(evals, list) and evals, f"{path} must contain evals")
    required_keys = {
        "id",
        "category",
        "name",
        "prompt",
        "expected_load",
        "expected_output",
        "assertions",
    }
    for case in evals:
        missing = required_keys - case.keys()
        require(not missing, f"{path}: eval missing {sorted(missing)}")
        require(isinstance(case.get("assertions"), list), f"{path}: {case.get('id')} assertions must be a list")
        require(case.get("assertions"), f"{path}: {case.get('id')} needs assertions")
    ids = [case["id"] for case in evals]
    require(len(ids) == len(set(ids)), f"{path}: eval IDs must be unique")
    return set(ids)


def require_terms(path: Path, terms: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for term in terms:
        require(term in text, f"{path} missing scoring-contract term: {term}")


def forbid_terms(path: Path, terms: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for term in terms:
        require(term not in text, f"{path} retains obsolete score shortcut: {term}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--committee-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--dual-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "dual-committee-review-loop",
    )
    args = parser.parse_args()

    committee_root = args.committee_root.resolve()
    dual_root = args.dual_root.resolve()
    require_terms(committee_root / "SKILL.md", COMMITTEE_REQUIRED_TERMS)
    require_terms(dual_root / "SKILL.md", DUAL_REQUIRED_TERMS)
    require_terms(
        dual_root / "references" / "claude-cli-protocol.md",
        PROTOCOL_REQUIRED_TERMS,
    )
    forbid_terms(committee_root / "SKILL.md", COMMITTEE_FORBIDDEN_TERMS)
    forbid_terms(dual_root / "SKILL.md", DUAL_FORBIDDEN_TERMS)
    forbid_terms(
        dual_root / "references" / "claude-cli-protocol.md",
        PROTOCOL_FORBIDDEN_TERMS,
    )

    committee_eval_ids = load_eval_ids(committee_root / "evals" / "evals.json")
    dual_eval_ids = load_eval_ids(dual_root / "evals" / "evals.json")
    require(
        COMMITTEE_REQUIRED_EVALS <= committee_eval_ids,
        f"committee evals missing {sorted(COMMITTEE_REQUIRED_EVALS - committee_eval_ids)}",
    )
    require(
        DUAL_REQUIRED_EVALS <= dual_eval_ids,
        f"dual evals missing {sorted(DUAL_REQUIRED_EVALS - dual_eval_ids)}",
    )

    print(
        "PASS: calibrated scoring contract; "
        f"committee_evals={len(committee_eval_ids)} dual_evals={len(dual_eval_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
