#!/usr/bin/env python3
"""Validate codex-goalsmith eval matrix shape and coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_CATEGORIES = {
    "positive_routing",
    "negative_routing",
    "forbidden_load",
    "progressive_loading",
    "end_to_end",
}

ALLOWED_CATEGORIES = REQUIRED_CATEGORIES
REQUIRED_FIELDS = {
    "id",
    "category",
    "name",
    "prompt",
    "expected_load",
    "expected_output",
    "assertions",
}


def validate_eval_matrix(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: cannot read valid JSON: {exc}"]

    if data.get("skill_name") != "codex-goalsmith":
        errors.append(f"{path}: skill_name must be codex-goalsmith")

    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        errors.append(f"{path}: evals must be a non-empty list")
        return errors

    ids: set[str] = set()
    categories: set[str] = set()
    for index, case in enumerate(evals):
        label = case.get("id", f"eval[{index}]") if isinstance(case, dict) else f"eval[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label}: eval must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - set(case))
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label}: id must be a non-empty string")
        elif case_id in ids:
            errors.append(f"{label}: duplicate id")
        else:
            ids.add(case_id)

        category = case.get("category")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{label}: unsupported category {category!r}")
        else:
            categories.add(category)

        if not isinstance(case.get("expected_load"), bool):
            errors.append(f"{label}: expected_load must be boolean")

        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{label}: assertions must be a non-empty list")
        elif not all(isinstance(item, str) and item.strip() for item in assertions):
            errors.append(f"{label}: assertions must contain only non-empty strings")

        if category == "progressive_loading" and not case.get("expected_accessory_reads"):
            errors.append(f"{label}: progressive_loading eval must name expected_accessory_reads")

        for field in ("expected_accessory_reads", "forbidden_accessory_reads"):
            if field in case and not (
                isinstance(case[field], list)
                and all(isinstance(item, str) and item.strip() for item in case[field])
            ):
                errors.append(f"{label}: {field} must be a list of non-empty strings")

    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        errors.append(f"{path}: missing categories: {', '.join(missing_categories)}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_evals.py <evals.json>", file=sys.stderr)
        return 2

    errors = validate_eval_matrix(Path(argv[1]))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Eval matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
