#!/usr/bin/env python3
"""Validate a DHF packet with the portable repository schema."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_SCHEMA = Path(__file__).resolve().parents[1] / "codex" / "runtime" / "dhf-packet.schema.json"
SCHEMA_KEYS = {
    "$schema", "$id", "title", "description", "type", "additionalProperties",
    "required", "properties", "items", "enum", "const", "minLength", "minItems",
    "pattern", "default", "examples",
}


class SchemaError(ValueError):
    pass


def json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaError(f"unsupported schema type: {expected}")


def check_schema(schema: Any, path: str = "$") -> None:
    if not isinstance(schema, dict):
        raise SchemaError(f"{path}: schema node must be an object")
    unsupported = sorted(set(schema) - SCHEMA_KEYS)
    if unsupported:
        raise SchemaError(f"{path}: unsupported schema keyword: {unsupported[0]}")
    expected = schema.get("type")
    if expected is not None and (not isinstance(expected, str) or expected not in {"object", "array", "string", "integer", "number", "boolean", "null"}):
        raise SchemaError(f"{path}: unsupported type declaration")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise SchemaError(f"{path}.properties: must be an object")
    for name, child in properties.items():
        check_schema(child, f"{path}.properties.{name}")
    if "items" in schema:
        check_schema(schema["items"], f"{path}.items")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except (TypeError, re.error) as exc:
            raise SchemaError(f"{path}.pattern: invalid regular expression") from exc


def error(path: str, code: str, message: str) -> dict[str, str]:
    return {"path": path, "code": code, "message": message}


def validate(value: Any, schema: dict[str, Any], path: str = "$") -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    expected = schema.get("type")
    if expected and not json_type_matches(value, expected):
        return [error(path, "type", f"expected {expected}")]
    if "const" in schema and value != schema["const"]:
        errors.append(error(path, "const", "value does not match the required constant"))
    if "enum" in schema and value not in schema["enum"]:
        errors.append(error(path, "enum", "value is not in the allowed set"))

    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            errors.append(error(path, "minLength", f"must contain at least {schema['minLength']} characters"))
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(error(path, "pattern", "value does not match the required pattern"))
    elif isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            errors.append(error(path, "minItems", f"must contain at least {schema['minItems']} items"))
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(validate(item, schema["items"], f"{path}[{index}]"))
    elif isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                errors.append(error(f"{path}.{name}", "required", "required field is missing"))
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in properties:
                    errors.append(error(f"{path}.{name}", "additionalProperties", "field is not allowed"))
        for name, child_schema in properties.items():
            if name in value:
                errors.extend(validate(value[name], child_schema, f"{path}.{name}"))
    return errors


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise OSError(f"{label} read failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} JSON invalid at line {exc.lineno} column {exc.colno}: {exc.msg}") from exc


def emit(payload: dict[str, Any], *, as_json: bool, stream: Any = sys.stdout) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=stream)
    elif payload["ok"]:
        print("dhf packet valid", file=stream)
    else:
        for item in payload["errors"]:
            print(f"ERROR[{item['code']}] {item['path']}: {item['message']}", file=stream)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DHF packet without writing output files.")
    parser.add_argument("packet", help="Path to the packet JSON file.")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to the DHF packet schema.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    packet_path = Path(args.packet).expanduser().resolve()
    schema_path = Path(args.schema).expanduser().resolve()
    try:
        schema = load_json(schema_path, "schema")
        check_schema(schema)
    except (OSError, ValueError, SchemaError) as exc:
        payload = {"ok": False, "status": "error", "packet": str(packet_path), "schema": str(schema_path), "errors": [error("$", "schema_error", str(exc))]}
        emit(payload, as_json=args.json, stream=sys.stdout if args.json else sys.stderr)
        return 2

    try:
        packet = load_json(packet_path, "packet")
    except (OSError, ValueError) as exc:
        payload = {"ok": False, "status": "invalid", "packet": str(packet_path), "schema": str(schema_path), "errors": [error("$", "packet_json", str(exc))]}
        emit(payload, as_json=args.json, stream=sys.stdout if args.json else sys.stderr)
        return 1

    errors = validate(packet, schema)
    payload = {
        "ok": not errors,
        "status": "valid" if not errors else "invalid",
        "packet": str(packet_path),
        "schema": str(schema_path),
        "errors": errors,
    }
    emit(payload, as_json=args.json, stream=sys.stdout if args.json or not errors else sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
