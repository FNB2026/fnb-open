#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate FNB public JSON schemas, examples, and conformance fixtures."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specs" / "v0.1"
EXAMPLE_DIR = ROOT / "examples"
FIXTURE_DIR = ROOT / "tests" / "conformance" / "v0.1"
FIXTURE_WORLD_DIR = ROOT / "tests" / "fixtures" / "generated"

# Envelope produced by tools/fnb-fixtures.py.
WORLD_VERSION = "1.0"
WORLD_PROTOCOL_RELEASE = "v0.1.0-preview.1"
WORLD_GENERATOR = "fnb-fixtures"
WORLD_CHAIN_KINDS = ("protocol_chain", "invalidation_chain", "source_state_chain")
WORLD_REQUIRED = (
    "world_version",
    "protocol_release",
    "generator",
    "scenario",
    "seed",
    "object_schemas",
    "objects",
    "validation",
)

CHAIN_SCHEMA_MAP = {
    "flow_event": "flow-event.schema.json",
    "node": "node.schema.json",
    "ai_inference": "ai-inference.schema.json",
    "block_draft": "block-draft.schema.json",
    "correction": "correction-patch.schema.json",
    "block": "block.schema.json",
}
FORMAT_CHECKER = FormatChecker()
SOURCE_STATES = (
    "active",
    "stale",
    "redacted",
    "deleted",
    "permission_withdrawn",
)
ALLOWED_SOURCE_STATE_TRANSITIONS = {
    ("active", "stale"): "source_stale",
    ("active", "redacted"): "source_redacted",
    ("active", "deleted"): "source_deleted",
    ("active", "permission_withdrawn"): "permission_withdrawn",
    ("stale", "active"): "source_restored",
    ("stale", "redacted"): "source_redacted",
    ("stale", "deleted"): "source_deleted",
    ("stale", "permission_withdrawn"): "permission_withdrawn",
    ("redacted", "deleted"): "source_deleted",
    ("permission_withdrawn", "active"): "permission_restored",
    ("permission_withdrawn", "redacted"): "source_redacted",
    ("permission_withdrawn", "deleted"): "source_deleted",
}
CANONICAL_SCHEMA_PREFIX = (
    "https://raw.githubusercontent.com/FNB2026/fnb-open/v0.1.0-preview.1/specs/v0.1/"
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
        canonical = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
        if path.read_text(encoding="utf-8") != canonical:
            raise AssertionError(
                f"{path.relative_to(ROOT)}: schema must use canonical two-space JSON formatting"
            )
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


def validate_invalidation_semantics(record: dict[str, Any], label: str) -> None:
    material = "|".join(
        [
            record["trigger_type"],
            record["trigger_id"],
            record["target_type"],
            record["target_id"],
            record["resulting_state"],
        ]
    )
    expected = f"sha256:{hashlib.sha256(material.encode('utf-8')).hexdigest()}"
    if record["idempotency_key"] != expected:
        raise AssertionError(
            f"{label}: invalidation idempotency_key must be the SHA-256 of the canonical trigger and target tuple"
        )


def validate_audit_tombstone_semantics(record: dict[str, Any], label: str) -> None:
    occurred_on = date.fromisoformat(record["occurred_on"])
    purge_after = date.fromisoformat(record["purge_after"])
    if purge_after < occurred_on:
        raise AssertionError(f"{label}: audit tombstone purge_after must not predate occurred_on")


def validate_permission_snapshot_semantics(record: dict[str, Any], label: str) -> None:
    expires_at = record.get("expires_at")
    if expires_at and parse_datetime(expires_at) <= parse_datetime(record["captured_at"]):
        raise AssertionError(f"{label}: permission snapshot expires_at must follow captured_at")


def validate_source_state_change_semantics(record: dict[str, Any], label: str) -> None:
    transition = (record["previous_state"], record["new_state"])
    expected_reason = ALLOWED_SOURCE_STATE_TRANSITIONS.get(transition)
    if expected_reason is None:
        raise AssertionError(f"{label}: forbidden source state transition {transition[0]} -> {transition[1]}")
    if record["reason_code"] != expected_reason:
        raise AssertionError(f"{label}: source state transition requires reason_code {expected_reason}")


def validate_source_state_transition_matrix() -> None:
    path = FIXTURE_DIR / "source-state-transition-matrix.json"
    matrix = load_json(path)
    if matrix.get("states") != list(SOURCE_STATES):
        raise AssertionError(f"{path.relative_to(ROOT)}: states must be canonical")
    declared = {
        (item["previous_state"], item["new_state"]): item["reason_code"]
        for item in matrix.get("allowed", [])
    }
    if declared != ALLOWED_SOURCE_STATE_TRANSITIONS:
        raise AssertionError(f"{path.relative_to(ROOT)}: allowed transitions do not match the protocol matrix")
    combinations = {(previous, new) for previous in SOURCE_STATES for new in SOURCE_STATES}
    for transition in combinations:
        if declared.get(transition) != ALLOWED_SOURCE_STATE_TRANSITIONS.get(transition):
            raise AssertionError(f"{path.relative_to(ROOT)}: transition matrix must cover every state pair")


def validate_object_semantics(schema_name: str, instance: dict[str, Any], label: str) -> None:
    if schema_name == "relationship.schema.json":
        validate_relationship_semantics(instance, label)
    elif schema_name == "ai-inference.schema.json":
        validate_inference_semantics(instance, label)
    elif schema_name == "invalidation-record.schema.json":
        validate_invalidation_semantics(instance, label)
    elif schema_name == "audit-tombstone.schema.json":
        validate_audit_tombstone_semantics(instance, label)
    elif schema_name == "permission-snapshot.schema.json":
        validate_permission_snapshot_semantics(instance, label)
    elif schema_name == "source-state-change.schema.json":
        validate_source_state_change_semantics(instance, label)


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


def validate_invalidation_chain_instance(
    schemas: dict[str, dict[str, Any]], chain: dict[str, Any], label: str
) -> None:
    records = chain.get("records")
    if not isinstance(records, list) or not records:
        raise AssertionError(f"{label}: invalidation chain must contain records")
    seen_records: dict[str, dict[str, Any]] = {}
    seen_targets: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        record_label = f"{label}#records[{index}]"
        validate_instance(
            schemas, "invalidation-record.schema.json", record, record_label
        )
        validate_invalidation_semantics(record, record_label)
        if record["trigger_type"] == "parent_invalidation":
            parent_id = record["parent_invalidation_id"]
            parent = seen_records.get(parent_id)
            if parent is None:
                raise AssertionError(
                    f"{record_label}: parent invalidation must reference an earlier record"
                )
            if record["trigger_id"] != parent["idempotency_key"]:
                raise AssertionError(
                    f"{record_label}: parent invalidation trigger_id must equal the parent idempotency_key"
                )
        target = (record["target_type"], record["target_id"])
        if target in seen_targets:
            raise AssertionError(
                f"{record_label}: an invalidation chain must transition each target once"
            )
        seen_records[record["invalidation_id"]] = record
        seen_targets.add(target)


def validate_source_state_chain_instance(
    schemas: dict[str, dict[str, Any]], chain: dict[str, Any], label: str
) -> None:
    snapshot = chain.get("permission_snapshot")
    change = chain.get("source_state_change")
    invalidation = chain.get("invalidation")
    if not all(isinstance(value, dict) for value in (snapshot, change, invalidation)):
        raise AssertionError(f"{label}: source-state chain must include snapshot, change, and invalidation")
    validate_instance(schemas, "permission-snapshot.schema.json", snapshot, f"{label}#permission_snapshot")
    validate_permission_snapshot_semantics(snapshot, f"{label}#permission_snapshot")
    validate_instance(schemas, "source-state-change.schema.json", change, f"{label}#source_state_change")
    validate_source_state_change_semantics(change, f"{label}#source_state_change")
    validate_instance(schemas, "invalidation-record.schema.json", invalidation, f"{label}#invalidation")
    validate_invalidation_semantics(invalidation, f"{label}#invalidation")
    if snapshot["source_ref"] != change["source_ref"]:
        raise AssertionError(f"{label}: permission snapshot and source change must reference the same source")
    if change["new_state"] == "active":
        raise AssertionError(f"{label}: an active source state must not emit an invalidation")
    expected = {
        "redacted": ("source_change", "source_redacted", "invalidated"),
        "deleted": ("source_change", "source_deleted", "invalidated"),
        "permission_withdrawn": ("permission_change", "permission_withdrawn", "invalidated"),
    }.get(change["new_state"])
    if change["new_state"] == "stale":
        expected = ("source_change", "source_stale", invalidation["resulting_state"])
        if invalidation["resulting_state"] not in {"invalidated", "review_required"}:
            raise AssertionError(f"{label}: stale source must invalidate or require review")
    if expected is None or (
        invalidation["trigger_type"],
        invalidation["reason_code"],
        invalidation["resulting_state"],
    ) != expected:
        raise AssertionError(f"{label}: invalidation does not match the source-state transition")
    if invalidation["trigger_id"] != change["source_change_id"]:
        raise AssertionError(f"{label}: direct invalidation must use the source change as its trigger")


def validate_fixtures(schemas: dict[str, dict[str, Any]]) -> None:
    valid_paths = sorted((FIXTURE_DIR / "valid").glob("*.json"))
    invalid_paths = sorted((FIXTURE_DIR / "invalid").glob("*.json"))
    invalid_chain_paths = sorted((FIXTURE_DIR / "invalid-chains").glob("*.json"))
    invalid_semantic_paths = sorted((FIXTURE_DIR / "invalid-semantics").glob("*.json"))
    valid_invalidation_chain_paths = sorted(
        (FIXTURE_DIR / "valid-invalidation-chains").glob("*.json")
    )
    invalid_invalidation_chain_paths = sorted(
        (FIXTURE_DIR / "invalid-invalidation-chains").glob("*.json")
    )
    valid_source_state_chain_paths = sorted(
        (FIXTURE_DIR / "valid-source-state-chains").glob("*.json")
    )
    invalid_source_state_chain_paths = sorted(
        (FIXTURE_DIR / "invalid-source-state-chains").glob("*.json")
    )
    if (
        not valid_paths
        or not invalid_paths
        or not invalid_chain_paths
        or not invalid_semantic_paths
        or not valid_invalidation_chain_paths
        or not invalid_invalidation_chain_paths
        or not valid_source_state_chain_paths
        or not invalid_source_state_chain_paths
    ):
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

    for path in valid_invalidation_chain_paths:
        validate_invalidation_chain_instance(
            schemas, load_json(path), str(path.relative_to(ROOT))
        )

    for path in invalid_invalidation_chain_paths:
        try:
            validate_invalidation_chain_instance(
                schemas, load_json(path), str(path.relative_to(ROOT))
            )
        except AssertionError:
            continue
        raise AssertionError(
            f"{path.relative_to(ROOT)}: expected invalidation-chain semantics to fail"
        )

    for path in valid_source_state_chain_paths:
        validate_source_state_chain_instance(schemas, load_json(path), str(path.relative_to(ROOT)))

    for path in invalid_source_state_chain_paths:
        try:
            validate_source_state_chain_instance(schemas, load_json(path), str(path.relative_to(ROOT)))
        except AssertionError:
            continue
        raise AssertionError(f"{path.relative_to(ROOT)}: expected source-state chain semantics to fail")

    validate_source_state_transition_matrix()

    covered = {load_json(path)["schema"] for path in valid_paths}
    covered.update(CHAIN_SCHEMA_MAP.values())
    missing = sorted(set(schemas) - covered)
    if missing:
        raise AssertionError(f"schemas without a valid instance: {', '.join(missing)}")


def validate_generated_world(schemas: dict[str, dict[str, Any]], world: Any, label: str) -> None:
    """Validate one synthetic fixture world produced by tools/fnb-fixtures.py.

    Every object must satisfy its declared schema and its object-level semantics,
    and every declared chain must pass the same cross-object validators the public
    conformance suite uses.
    """
    if not isinstance(world, dict):
        raise AssertionError(f"{label}: world must be an object")
    for key in WORLD_REQUIRED:
        if key not in world:
            raise AssertionError(f"{label}: missing {key}")
    if world["world_version"] != WORLD_VERSION:
        raise AssertionError(f"{label}: unsupported world_version")
    if world["protocol_release"] != WORLD_PROTOCOL_RELEASE:
        raise AssertionError(
            f"{label}: protocol_release must be {WORLD_PROTOCOL_RELEASE}"
        )
    if world["generator"] != WORLD_GENERATOR:
        raise AssertionError(f"{label}: unexpected generator {world['generator']!r}")
    seed = world["seed"]
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise AssertionError(f"{label}: seed must be a non-negative integer")

    objects = world["objects"]
    declared = world["object_schemas"]
    if not isinstance(objects, dict) or not objects:
        raise AssertionError(f"{label}: world must contain at least one object")
    if not isinstance(declared, dict) or set(declared) != set(objects):
        raise AssertionError(f"{label}: object_schemas must describe every object exactly once")

    for name in sorted(objects):
        object_label = f"{label}#{name}"
        validate_instance(schemas, declared[name], objects[name], object_label)
        validate_object_semantics(declared[name], objects[name], object_label)

    seen_kinds: set[str] = set()
    descriptors = world["validation"]
    if not isinstance(descriptors, list) or not descriptors:
        raise AssertionError(f"{label}: world must declare at least one chain validation")
    for descriptor in descriptors:
        if not isinstance(descriptor, dict) or "kind" not in descriptor:
            raise AssertionError(f"{label}: every validation entry needs a kind")
        kind = descriptor["kind"]
        if kind not in WORLD_CHAIN_KINDS:
            raise AssertionError(f"{label}: unknown validation kind {kind!r}")
        if kind in seen_kinds:
            raise AssertionError(f"{label}: duplicate validation kind {kind!r}")
        seen_kinds.add(kind)
        chain_label = f"{label}:{kind}"

        if kind == "invalidation_chain":
            names = descriptor.get("records")
            if not isinstance(names, list) or not names:
                raise AssertionError(f"{chain_label}: records must be a non-empty list")
            records = []
            for name in names:
                if name not in objects:
                    raise AssertionError(f"{chain_label}: unknown object {name!r}")
                records.append(objects[name])
            validate_invalidation_chain_instance(schemas, {"records": records}, chain_label)
            continue

        members = descriptor.get("members")
        if not isinstance(members, dict) or not members:
            raise AssertionError(f"{chain_label}: members must be a non-empty object")
        chain: dict[str, Any] = {}
        for key, name in members.items():
            if name not in objects:
                raise AssertionError(f"{chain_label}: unknown object {name!r}")
            chain[key] = objects[name]
        if kind == "protocol_chain":
            validate_protocol_chain_instance(schemas, chain, chain_label)
        else:
            validate_source_state_chain_instance(schemas, chain, chain_label)


def validate_generated_worlds(schemas: dict[str, dict[str, Any]]) -> int:
    paths = sorted(FIXTURE_WORLD_DIR.glob("*.json"))
    if not paths:
        raise AssertionError("generated synthetic fixture worlds are missing")
    for path in paths:
        validate_generated_world(schemas, load_json(path), str(path.relative_to(ROOT)))
    return len(paths)


def validate_all_json() -> None:
    for directory in (EXAMPLE_DIR, FIXTURE_DIR, FIXTURE_WORLD_DIR):
        for path in sorted(directory.rglob("*.json")):
            load_json(path)


def main() -> int:
    try:
        schemas = load_schemas()
        validate_all_json()
        validate_protocol_chain(schemas)
        validate_fixtures(schemas)
        worlds = validate_generated_worlds(schemas)
    except (AssertionError, KeyError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"validation passed: {len(schemas)} schemas, "
        f"{len(CHAIN_SCHEMA_MAP)} protocol-chain objects, full valid-instance coverage, "
        f"negative fixtures, {worlds} generated synthetic worlds"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
