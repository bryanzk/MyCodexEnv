#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


PHASES = {"research", "requirements", "planning", "development", "validation", "review", "ship", "handoff"}


def validate_checkpoint_artifact(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["checkpoint artifact must be an object"]
    if value.get("schema") != "dhf_checkpoint_v1":
        errors.append("checkpoint schema must be dhf_checkpoint_v1")
    if value.get("phase") not in PHASES:
        errors.append("checkpoint phase is invalid")
    constraints = value.get("constraints")
    if not isinstance(constraints, list) or any(
        not isinstance(item, str) or not item.strip() for item in constraints
    ):
        errors.append("constraints must be a list of non-empty strings")
    ownership = value.get("ownership")
    if not isinstance(ownership, dict):
        errors.append("ownership must be an object")
    elif ownership and (
        not isinstance(ownership.get("boundary"), str) or not ownership["boundary"].strip()
    ):
        errors.append("ownership boundary must be a non-empty string")
    next_action = value.get("next_action")
    if (
        not isinstance(next_action, dict)
        or not isinstance(next_action.get("command"), str)
        or not next_action["command"].strip()
    ):
        errors.append("next_action.command must be a non-empty string")
    elif "args" in next_action and (
        not isinstance(next_action["args"], list)
        or any(not isinstance(item, str) for item in next_action["args"])
    ):
        errors.append("next_action.args must be a string list")
    verification = value.get("verification_evidence")
    required_evidence = {"command", "exit_code", "key_output", "timestamp", "freshness"}
    if not isinstance(verification, dict) or set(verification) != required_evidence:
        errors.append("verification_evidence must contain all five structured fields")
    elif verification.get("command") is None:
        if value.get("phase") != "handoff":
            errors.append("unverified evidence is only valid for handoff checkpoints")
        if verification.get("exit_code") is not None or verification.get("key_output") is not None:
            errors.append("unverified evidence exit_code and key_output must be null")
        if not isinstance(verification.get("timestamp"), str) or not verification["timestamp"].strip():
            errors.append("unverified evidence timestamp must be non-empty")
        if verification.get("freshness") != "unknown":
            errors.append("unverified evidence freshness must be unknown")
    else:
        if not isinstance(verification.get("command"), str) or not verification["command"].strip():
            errors.append("verification_evidence.command must be non-empty")
        if not isinstance(verification.get("exit_code"), int):
            errors.append("verification_evidence.exit_code must be an integer")
        if not isinstance(verification.get("key_output"), str) or not verification["key_output"].strip():
            errors.append("verification_evidence.key_output must be non-empty")
        if not isinstance(verification.get("timestamp"), str) or not verification["timestamp"].strip():
            errors.append("verification_evidence.timestamp must be non-empty")
        if verification.get("freshness") not in {"fresh", "stale", "unknown"}:
            errors.append("verification_evidence.freshness is invalid")
    return errors
