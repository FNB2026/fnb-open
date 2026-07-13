#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate FNB public JSON schemas, examples, and conformance fixtures."""

from __future__ import annotations

import json
import sys
from datetime import datetime
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
CANONICAL_SCHEMA_PREFIX = (
    "https://raw.githubusercontent.com/FNB2026/fnb-open/main/specs/v0.1/"
)


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
        expected_id = f"{CANONICAL_SCHEMA_PREFIX}{path.name}"
        if schema_id != expected_id:
            raise AssertionError(
                f"{path.relative_to(ROOT)}: $id must be canonical: {expected_id}"
            )
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


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_relationship_semantics(relationship: dict[str, Any], label: str) -> None:
    participants = set(relationship["participant_ids"])
    assertion_actors = {assertion["actor_id"] for assertion in relationship["assertions"]}
    if not assertion_actors.issubset(participants):
        raise AssertionError(f"{label}: every assertion actor must be a participant")


def validate_inference_semantics(inference: dict[str, Any], label: str) -> None:
    evidence_refs = set(inference["explanation"]["evidence_refs"])
    if not evidence_refs.issubset(set(inference["input_refs"])):
        raise AssertionError(f"{label}: AIInference evidence must resolve through its inputs")


def validate_object_semantics(schema_name: str, instance: dict[str, Any], label: str) -> None:
    if schema_name == "relationship.schema.json":
        validate_relationship_semantics(instance, label)
    elif schema_name == "ai-inference.schema.json":
        validate_inference_semantics(instance, label)


def validate_protocol_chain_instance(
    schemas: dict[str, dict[str, Any]], chain: dict[str, Any], label: str
) -> None:
    for key, schema_name in CHAIN_SCHEMA_MAP.items():
        if key not in chain:
            raise AssertionError(f"{label}: missing {key}")
        validate_instance(schemas, schema_name, chain[key], f"{label}#{key}")

    event = chain["flow_event"]
    node = chain["node"]
    inference = chain["ai_inference"]
    draft = chain["block_draft"]
    correction = chain["correction"]
    block = chain["block"]

    validate_inference_semantics(inference, f"{label}#ai_inference")

    checks = [
        (event["event_id"] in node["source_event_ids"], "Node must reference its FlowEvent"),
        (event["event_id"] in inference["input_refs"], "AIInference must reference its FlowEvent"),
        (node["node_id"] in inference["input_refs"], "AIInference must reference its Node"),
        (draft["inference_id"] == inference["inference_id"], "BlockDraft must reference its AIInference"),
        (draft["source_node_ids"] == block["source_node_ids"], "Block must preserve draft source Nodes"),
        (draft["owner_id"] == block["owner_id"], "Block must preserve the draft owner"),
        (correction["actor_id"] == draft["owner_id"], "Correction actor must own the draft"),
        (draft["block_type"] == block["block_type"], "Block must preserve the draft type"),
        (draft["status"] in {"confirmed", "rewritten"}, "Rejected or pending Draft must not create a Block"),
        (correction["target_id"] == draft["draft_id"], "CorrectionPatch must target the BlockDraft"),
        (block.get("draft_id") == draft["draft_id"], "AI-derived Block must reference its BlockDraft"),
        (block["confirmed_by_actor_id"] == block["owner_id"], "Reference-chain Block must be confirmed by its owner"),
    ]
    if draft["status"] == "rewritten":
        checks.extend(
            [
                (correction["operation"] == "replace", "Rewritten Draft must have a replace Correction"),
                (block["confirmation_operation"] == "rewrite", "Rewritten Draft must record rewrite confirmation"),
                (block.get("correction_id") == correction["correction_id"], "Rewritten Block must reference its Correction"),
                (correction.get("path") == "/proposed_summary", "Reference Correction must target the proposed summary"),
                (correction.get("after") == block.get("summary"), "Correction result must equal the final Block summary"),
            ]
        )
    elif draft["status"] == "confirmed":
        checks.append((block["confirmation_operation"] == "confirm", "Confirmed Draft must record confirm operation"))

    checks.extend(
        [
            (
                parse_datetime(block["confirmed_at"]) >= parse_datetime(correction["created_at"]),
                "Block confirmation must not predate its Correction",
            ),
            (
                parse_datetime(correction["created_at"]) >= parse_datetime(event["occurred_at"]),
                "Correction must not predate its source event",
            ),
        ]
    )
    for passed, message in checks:
        if not passed:
            raise AssertionError(f"{label}: {message}")


def validate_protocol_chain(schemas: dict[str, dict[str, Any]]) -> None:
    path = EXAMPLE_DIR / "synthetic-protocol-chain.json"
    validate_protocol_chain_instance(schemas, load_json(path), str(path.relative_to(ROOT)))


def validate_fixtures(schemas: dict[str, dict[str, Any]]) -> None:
    valid_paths = sorted((FIXTURE_DIR / "valid").glob("*.json"))
    invalid_paths = sorted((FIXTURE_DIR / "invalid").glob("*.json"))
    invalid_chain_paths = sorted((FIXTURE_DIR / "invalid-chains").glob("*.json"))
    invalid_semantic_paths = sorted((FIXTURE_DIR / "invalid-semantics").glob("*.json"))
    if not valid_paths or not invalid_paths or not invalid_chain_paths or not invalid_semantic_paths:
        raise AssertionError("conformance suite requires both valid and invalid fixtures")

    for path in valid_paths:
        fixture = load_json(path)
        validate_instance(schemas, fixture["schema"], fixture["instance"], str(path.relative_to(ROOT)))
        validate_object_semantics(fixture["schema"], fixture["instance"], str(path.relative_to(ROOT)))

    for path in invalid_paths:
        fixture = load_json(path)
        schema_name = fixture["schema"]
        validator = Draft202012Validator(schemas[schema_name], format_checker=FORMAT_CHECKER)
        if not list(validator.iter_errors(fixture["instance"])):
            raise AssertionError(f"{path.relative_to(ROOT)}: expected schema validation to fail")

    for path in invalid_chain_paths:
        try:
            validate_protocol_chain_instance(schemas, load_json(path), str(path.relative_to(ROOT)))
        except AssertionError:
            continue
        raise AssertionError(f"{path.relative_to(ROOT)}: expected protocol semantics to fail")

    for path in invalid_semantic_paths:
        fixture = load_json(path)
        label = str(path.relative_to(ROOT))
        validate_instance(schemas, fixture["schema"], fixture["instance"], label)
        try:
            validate_object_semantics(fixture["schema"], fixture["instance"], label)
        except AssertionError:
            continue
        raise AssertionError(f"{label}: expected object semantics to fail")

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
