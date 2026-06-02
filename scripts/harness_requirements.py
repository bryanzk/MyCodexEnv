#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "Goal",
    "Audience",
    "Scope",
    "Non-Goals",
    "Constraints",
    "Task Demand (D_task)",
    "Source Of Truth",
    "Acceptance Criteria",
    "Verification Gate",
    "Risks",
    "Handoff Notes",
]


TASK_DEMAND_FIELDS = {
    "estimated_level": "estimated_level",
    "L (reasoning/action steps)": "L",
    "H_tool (tool-selection ambiguity)": "H_tool",
    "S_state (cross-module state tracking)": "S_state",
    "N_obs (observation/external noise)": "N_obs",
}
TASK_DEMAND_REQUIRED = ["estimated_level", "L", "H_tool", "S_state", "N_obs"]
TASK_DEMAND_LEVELS = {"low", "medium", "high"}


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def meaningful_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("<!--")]


def validate_task_demand(lines: list[str]) -> list[str]:
    meaningful = meaningful_lines(lines)
    if not meaningful:
        return ["task demand must be non-empty"]

    values: dict[str, str] = {}
    present: set[str] = set()
    for raw_line in meaningful:
        line = raw_line.removeprefix("- ").strip()
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        field = TASK_DEMAND_FIELDS.get(label.strip())
        if field is None:
            continue
        present.add(field)
        values[field] = value.strip()

    errors: list[str] = []
    for field in TASK_DEMAND_REQUIRED:
        if field not in present:
            errors.append(f"task demand field is required: {field}")
        elif not values.get(field):
            errors.append(f"task demand field must be non-empty: {field}")

    level = values.get("estimated_level")
    if level and level not in TASK_DEMAND_LEVELS:
        errors.append("task demand estimated_level must be one of: low, medium, high")
    return errors


def validate_requirements(path: Path) -> list[str]:
    try:
        sections = parse_sections(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"read failed: {exc}"]

    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in sections:
            errors.append(f"missing heading: ## {heading}")

    if errors:
        return errors

    if not meaningful_lines(sections["Goal"]):
        errors.append("goal must be non-empty")

    errors.extend(validate_task_demand(sections["Task Demand (D_task)"]))

    acceptance = [
        line
        for line in meaningful_lines(sections["Acceptance Criteria"])
        if line.startswith("- [ ]") or line.startswith("- [x]") or line.startswith("- ")
    ]
    if not acceptance:
        errors.append("at least one acceptance criterion is required")

    verification = [
        line
        for line in meaningful_lines(sections["Verification Gate"])
        if line.startswith("- `") or line.startswith("- ")
    ]
    if not verification:
        errors.append("at least one verification command is required")

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_requirements(Path(args.path).expanduser())
    if errors:
        print("ERROR: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Harness Runtime requirements artifact.")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    validate_parser = subparsers.add_parser("validate", help="Validate one requirements Markdown file")
    validate_parser.add_argument("path")
    validate_parser.set_defaults(func=cmd_validate)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
