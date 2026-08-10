#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any


MODEL_TIERS = {
    "economy": {"model": "gpt-5.4-mini", "reasoning_effort": "low"},
    "balanced": {"model": "gpt-5.4", "reasoning_effort": "medium"},
    "frontier": {"model": "gpt-5.5", "reasoning_effort": "high"},
}

SIMPLE_PATTERNS = [
    r"\btranslate\b",
    r"\bsummarize\b",
    r"\bformat\b",
    r"\brename\b",
    r"\bcopy\b",
    r"翻译",
    r"总结",
    r"润色",
    r"格式",
    r"改名",
    r"说明同步",
    r"README",
]

MEDIUM_PATTERNS = [
    r"\bimplement\b",
    r"\bfix\b",
    r"\btest\b",
    r"\brefactor\b",
    r"\bscript\b",
    r"实现",
    r"修复",
    r"测试",
    r"重构",
    r"脚本",
]

COMPLEX_PATTERNS = [
    r"\barchitecture\b",
    r"\bmigration\b",
    r"\bcross[- ]module\b",
    r"\bdatabase\b",
    r"\bauth\b",
    r"\bsecurity\b",
    r"\bdeploy\b",
    r"\brollback\b",
    r"\bapi contract\b",
    r"\bparallel agents?\b",
    r"架构",
    r"迁移",
    r"跨模块",
    r"数据库",
    r"认证",
    r"鉴权",
    r"安全",
    r"部署",
    r"回滚",
    r"并行",
    r"多次.*切换",
]

QUALITY_FLOOR_PATTERNS = [
    r"\bsecurity\b",
    r"\bauth\b",
    r"\bcredential\b",
    r"\btoken\b",
    r"\bprivacy\b",
    r"\bmigration\b",
    r"\bdeploy\b",
    r"\bproduction\b",
    r"\bdestructive\b",
    r"安全",
    r"认证",
    r"鉴权",
    r"凭据",
    r"令牌",
    r"隐私",
    r"迁移",
    r"部署",
    r"生产",
    r"破坏性",
]


def load_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def nested_dict(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("tool_input", "input", "arguments", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def first_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    data = nested_dict(payload)
    for source in (payload, data):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def first_value(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    data = nested_dict(payload)
    for source in (payload, data):
        for key in keys:
            if key in source and source[key] not in ("", None):
                return source[key]
    return None


def count_matches(patterns: list[str], text: str) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE))


def prompt_text(payload: dict[str, Any]) -> str:
    prompt = first_text(payload, ("prompt", "user_prompt", "message", "task", "input_text"))
    subtask = first_text(payload, ("subtask", "current_task", "step", "phase_task"))
    if subtask:
        return subtask
    return prompt


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    text = prompt_text(payload)
    full_prompt = first_text(payload, ("prompt", "user_prompt", "message", "task", "input_text"))
    phase = first_text(payload, ("phase", "lifecycle_stage"))

    if not text:
        return {
            "complexity": "unknown",
            "tier": "balanced",
            "confidence": "low",
            "reasons": ["missing_prompt"],
            "switch_allowed": True,
        }

    simple = count_matches(SIMPLE_PATTERNS, text)
    medium = count_matches(MEDIUM_PATTERNS, text)
    complex_hits = count_matches(COMPLEX_PATTERNS, text)
    quality_floor = count_matches(QUALITY_FLOOR_PATTERNS, text)

    if text != full_prompt:
        full_complex_hits = count_matches(COMPLEX_PATTERNS, full_prompt)
        full_quality_floor = count_matches(QUALITY_FLOOR_PATTERNS, full_prompt)
    else:
        full_complex_hits = complex_hits
        full_quality_floor = quality_floor

    word_count = len(re.findall(r"\S+", text))
    reasons: list[str] = []

    if quality_floor > 0:
        reasons.append("quality_floor")
    if complex_hits > 0:
        reasons.append("complexity_signals")
    if simple > 0:
        reasons.append("simple_signal")
    if word_count > 120:
        reasons.append("long_prompt")
    if phase in {"review", "validation", "ship"}:
        reasons.append(f"phase:{phase}")

    if phase == "review":
        complexity = "complex"
        tier = "frontier"
        confidence = "high"
    elif phase == "validation" and not quality_floor and not complex_hits:
        complexity = "simple"
        tier = "economy"
        confidence = "medium"
    elif quality_floor or complex_hits >= 2 or word_count > 180:
        complexity = "complex"
        tier = "frontier"
        confidence = "high"
    elif complex_hits == 1 or medium >= 1 or word_count > 45:
        complexity = "medium"
        tier = "balanced"
        confidence = "medium"
    elif simple >= 1 and word_count <= 45:
        complexity = "simple"
        tier = "economy"
        confidence = "medium"
    elif word_count <= 3 and not medium and not complex_hits and not quality_floor:
        complexity = "simple"
        tier = "economy"
        confidence = "medium"
        reasons.append("short_prompt")
    else:
        complexity = "medium"
        tier = "balanced"
        confidence = "medium"

    if text != full_prompt and simple >= 1 and not quality_floor and not complex_hits:
        complexity = "simple"
        tier = "economy"
        confidence = "medium"
        reasons.append("subtask_downshift")
    elif text != full_prompt and (full_quality_floor or full_complex_hits):
        reasons.append("parent_task_complex")

    if not reasons:
        reasons.append("matched_default")

    return {
        "complexity": complexity,
        "tier": tier,
        "confidence": confidence,
        "reasons": reasons,
        "switch_allowed": True,
    }


def switch_points(payload: dict[str, Any]) -> list[dict[str, str]]:
    text = first_text(payload, ("prompt", "user_prompt", "message", "task", "input_text"))
    if not text or count_matches(COMPLEX_PATTERNS, text) == 0:
        return []
    return [
        {"stage": "research", "model": "gpt-5.4-mini", "reasoning_effort": "low"},
        {"stage": "planning", "model": "gpt-5.5", "reasoning_effort": "high"},
        {"stage": "development", "model": "gpt-5.4", "reasoning_effort": "medium"},
        {"stage": "validation", "model": "gpt-5.4-mini", "reasoning_effort": "low"},
        {"stage": "review", "model": "gpt-5.5", "reasoning_effort": "high"},
    ]


def nested_value(payload: dict[str, Any], containers: tuple[str, ...], keys: tuple[str, ...]) -> Any:
    for container in containers:
        value = payload.get(container)
        if isinstance(value, dict):
            for key in keys:
                if key in value and value[key] not in ("", None):
                    return value[key]
    return first_value(payload, keys)


def token_usage(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_tokens": nested_value(payload, ("usage", "token_usage"), ("input_tokens", "prompt_tokens")),
        "output_tokens": nested_value(payload, ("usage", "token_usage"), ("output_tokens", "completion_tokens")),
        "total_tokens": nested_value(payload, ("usage", "token_usage"), ("total_tokens", "tokens_used")),
    } | {}


def normalize_unavailable(data: dict[str, Any]) -> dict[str, Any]:
    return {key: (value if value is not None else "unavailable") for key, value in data.items()}


def five_hour_limit(payload: dict[str, Any]) -> dict[str, Any]:
    remaining = nested_value(
        payload,
        ("limits", "quota", "rate_limit"),
        ("five_hour_remaining", "five_hour_limit_remaining", "remaining_5h", "limit_remaining"),
    )
    reset_at = nested_value(
        payload,
        ("limits", "quota", "rate_limit"),
        ("five_hour_reset_at", "reset_at_5h", "limit_reset_at"),
    )
    if remaining is None:
        remaining = os.environ.get("CODEX_5H_LIMIT_REMAINING")
    if reset_at is None:
        reset_at = os.environ.get("CODEX_5H_LIMIT_RESET_AT")
    return normalize_unavailable({"remaining": remaining, "reset_at": reset_at})


def build_telemetry(payload: dict[str, Any], routing: dict[str, Any]) -> dict[str, Any]:
    actual_model = first_text(payload, ("model", "current_model", "selected_model", "active_model"))
    models = []
    if actual_model:
        models.append(actual_model)
    routed_model = str(routing["model"])
    if routed_model not in models:
        models.append(routed_model)
    return {
        "models_used": models,
        "token_usage": normalize_unavailable(token_usage(payload)),
        "five_hour_limit": five_hour_limit(payload),
    }


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    classification = classify(payload)
    tier = MODEL_TIERS[classification.pop("tier")]
    routing = {**tier, **classification, "switch_points": switch_points(payload)}
    telemetry = build_telemetry(payload, routing)
    context = (
        "Model routing recommendation: "
        f"use `{routing['model']}` with `{routing['reasoning_effort']}` reasoning "
        f"for this prompt/subtask; complexity={routing['complexity']}; "
        f"reasons={', '.join(routing['reasons'])}. "
        "For multi-stage tasks, re-run routing at each stage or subtask boundary.\n"
        "每次最终回复必须包含 telemetry：本轮处理过程中使用的 model、token 消耗、"
        "以及 5小时 limit 剩余。若 hook payload 未提供真实 token 或 limit 字段，"
        "必须写 `unavailable`，不得估算或编造。"
    )
    return {
        "continue": True,
        "routing": routing,
        "telemetry": telemetry,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
    }


def main() -> int:
    json.dump(build_response(load_payload()), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
