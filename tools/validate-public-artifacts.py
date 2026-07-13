#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate FNB public JSON schemas, examples, and conformance fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specs" / "v0.1"
EXAMPLE_DIR = ROOT / "examples"
FIXTURE_DIR = ROOT / "tests" / "conformance" / "v0.1"

CHAIN_SCHEMA_MAP = {
    "flow_event": "flow-event.schema.json",
    "node": "node.schema.json",
    "ai_inference": "ai-inference.schema.json",
    "block_draft": "block-draft.schema.json",
    "correction": "correction-patch.schema.json",
    "block": "block.schema.json",
}
FORMAT_CHECKER = FormatChecker()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    schema_ids: set[str] = set()
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        schema_id = schema.get("$id")
        if not schema_id:
            raise AssertionError(f"{path.relative_to(ROOT)}: missing $id")
        if schema_id in schema_ids:
            raise AssertionError(f"{path.relative_to(ROOT)}: duplicate $id {schema_id}")
        schema_ids.add(schema_id)
        schemas[path.name] = schema
    if not schemas:
        raise AssertionError("no v0.1 schemas found")
    return schemas


def validate_instance(
    schemas: dict[str, dict[str, Any]], schema_name: str, instance: Any, label: str
) -> None:
    try:
        schema = schemas[schema_name]
    except KeyError as exc:
        raise AssertionError(f"{label}: unknown schema {schema_name}") from exc
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(error.message for error in errors)
        raise AssertionError(f"{label}: {details}")


def validate_protocol_chain(schemas: dict[str, dict[str, Any]]) -> None:
    path = EXAMPLE_DIR / "synthetic-protocol-chain.json"
    chain = load_json(path)
    for key, schema_name in CHAIN_SCHEMA_MAP.items():
        if key not in chain:
            raise AssertionError(f"{path.relative_to(ROOT)}: missing {key}")
        validate_instance(schemas, schema_name, chain[key], f"{path.relative_to(ROOT)}#{key}")

    event = chain["flow_event"]
    node = chain["node"]
    inference = chain["ai_inference"]
    draft = chain["block_draft"]
    correction = chain["correction"]
    block = chain["block"]

    checks = [
        (event["event_id"] in node["source_event_ids"], "Node must reference its FlowEvent"),
        (event["event_id"] in inference["input_refs"], "AIInference must reference its FlowEvent"),
        (node["node_id"] in inference["input_refs"], "AIInference must reference its Node"),
        (draft["inference_id"] == inference["inference_id"], "BlockDraft must reference its AIInference"),
        (draft["source_node_ids"] == block["source_node_ids"], "Block must preserve draft source Nodes"),
        (correction["target_id"] == draft["draft_id"], "CorrectionPatch must target the BlockDraft"),
        (block.get("draft_id") == draft["draft_id"], "AI-derived Block must reference its BlockDraft"),
    ]
    for passed, message in checks:
        if not passed:
            raise AssertionError(f"{path.relative_to(ROOT)}: {message}")


def validate_fixtures(schemas: dict[str, dict[str, Any]]) -> None:
    valid_paths = sorted((FIXTURE_DIR / "valid").glob("*.json"))
    invalid_paths = sorted((FIXTURE_DIR / "invalid").glob("*.json"))
    if not valid_paths or not invalid_paths:
        raise AssertionError("conformance suite requires both valid and invalid fixtures")

    for path in valid_paths:
        fixture = load_json(path)
        validate_instance(schemas, fixture["schema"], fixture["instance"], str(path.relative_to(ROOT)))

    for path in invalid_paths:
        fixture = load_json(path)
        schema_name = fixture["schema"]
        validator = Draft202012Validator(schemas[schema_name], format_checker=FORMAT_CHECKER)
        if not list(validator.iter_errors(fixture["instance"])):
            raise AssertionError(f"{path.relative_to(ROOT)}: expected schema validation to fail")

    covered = {load_json(path)["schema"] for path in valid_paths}
    covered.update(CHAIN_SCHEMA_MAP.values())
    missing = sorted(set(schemas) - covered)
    if missing:
        raise AssertionError(f"schemas without a valid instance: {', '.join(missing)}")


def validate_all_json() -> None:
    for directory in (EXAMPLE_DIR, FIXTURE_DIR):
        for path in sorted(directory.rglob("*.json")):
            load_json(path)


def main() -> int:
    try:
        schemas = load_schemas()
        validate_all_json()
        validate_protocol_chain(schemas)
        validate_fixtures(schemas)
    except (AssertionError, KeyError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"validation passed: {len(schemas)} schemas, "
        f"{len(CHAIN_SCHEMA_MAP)} protocol-chain objects, full valid-instance coverage, "
        "negative fixtures"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
