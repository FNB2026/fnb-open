#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline RFC-0004 contract probe; not an HTTP server or FNB implementation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = "specs/openapi/object-exchange/v1/openapi.yaml"
MANIFEST = "specs/openapi/object-exchange/v1/artifact-digests.json"
PUBLIC_MANIFEST = "specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json"
RELEASE = "v0.1.0-preview.1"
TRANSPORT = "1.0"
TAG = "object-exchange-v1.0.0-preview.1"
IDENTITIES = {
    "actor": "actor_id", "ai-inference": "inference_id", "asset": "asset_id",
    "audit-tombstone": "audit_id", "block-draft": "draft_id", "block": "block_id",
    "correction-patch": "correction_id", "flow-event": "event_id",
    "invalidation-record": "invalidation_id", "memory": "memory_id", "node": "node_id",
    "permission-snapshot": "permission_snapshot_id", "relationship": "relationship_id",
    "source-state-change": "source_change_id",
}
PROBLEMS = {
    "malformed-envelope": (400, "Malformed exchange envelope"),
    "unsupported-media-type": (415, "Unsupported exchange representation"),
    "payload-too-large": (413, "Exchange payload too large"),
    "unsupported-transport-version": (400, "Unsupported transport version"),
    "unsupported-protocol-release": (400, "Unsupported protocol release"),
    "evaluation-failure": (500, "Exchange evaluation unavailable"),
}
ROLE_TYPES = {
    "protocol_chain": {"flow_event": "flow-event", "node": "node",
                       "ai_inference": "ai-inference", "block_draft": "block-draft",
                       "correction": "correction-patch", "block": "block"},
    "source_state_chain": {"permission_snapshot": "permission-snapshot",
                           "source_state_change": "source-state-change",
                           "invalidation": "invalidation-record"},
}
BOUNDARY_PATHS = (
    ARTIFACT, "specs/openapi/object-exchange/v1/README.md",
    "rfcs/0004-protocol-object-exchange.md", "tools/object-exchange-contract.py",
    "tests/conformance/transport/test_object_exchange.py",
    "tests/conformance/transport/openapi-3.1.schema.json",
    "tools/validate-public-artifacts.py", "tools/fnb-conformance.py", PUBLIC_MANIFEST,
    "tools/requirements-validation.lock",
)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


PUBLIC = module("exchange_public_rules", ROOT / "tools/validate-public-artifacts.py")
RELEASE_TOOLS = module("exchange_release_tools", ROOT / "tools/fnb-conformance.py")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def boundary_manifest(root=ROOT):
    return {"manifest_version": "1.0", "transport_version": TRANSPORT,
            "artifact_version": "1.0.0-preview.1", "protocol_release": RELEASE,
            "release_tag": TAG, "algorithm": "sha256",
            "artifacts": [{"path": path, "bytes": len((root / path).read_bytes()),
                           "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
                          for path in BOUNDARY_PATHS]}


def verify_boundary(root=ROOT):
    if read(root / MANIFEST) != boundary_manifest(root):
        raise AssertionError("transport artifact manifest differs from exact expected bytes/set")


def problem(suffix):
    status, title = PROBLEMS[suffix]
    return status, "application/problem+json", {
        "type": "https://www.fnbapp.net/problems/object-exchange/1.0/" + suffix,
        "title": title, "status": status,
    }


def require(condition):
    # Do not use Python assert: optimisation (-O) must never disable judgement.
    if not condition:
        raise AssertionError("exchange profile rule failed")


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("non-JSON number")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=Decimal, parse_constant=nonfinite)


class ContractProbe:
    """Test-side evaluator. No sockets, private state, HTTP framing, or reports."""

    def __init__(self, root=ROOT):
        self.root = root
        self.document = read(root / ARTIFACT)  # JSON is also valid YAML 1.2.

    def wire_validator(self, name, registry=Registry()):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                  "$ref": "#/components/schemas/" + name,
                  "components": self.document["components"]}
        return Draft202012Validator(schema, registry=registry,
                                    format_checker=PUBLIC.FORMAT_CHECKER)

    def verified_schemas(self):
        manifest, check = RELEASE_TOOLS.verify_manifest(self.root, self.root / PUBLIC_MANIFEST)
        if check["status"] != "pass" or manifest["protocol_release"] != RELEASE:
            raise RuntimeError("invalid local release manifest")
        if RELEASE_TOOLS.verify_schema_digests(self.root, manifest)["status"] != "pass":
            raise RuntimeError("invalid local schema bytes")
        schemas = {Path(item["path"]).name: read(self.root / item["path"])
                   for item in manifest["schemas"]}
        expected = {name + ".schema.json" for name in IDENTITIES}
        if set(schemas) != expected:
            raise RuntimeError("unsupported local schema set")
        prefix = f"https://raw.githubusercontent.com/FNB2026/fnb-open/{RELEASE}/specs/v0.1/"
        if any(schema["$id"] != prefix + name for name, schema in schemas.items()):
            raise RuntimeError("invalid local schema identities")
        for schema in schemas.values():
            PUBLIC.ensure_format_support(schema)
        return schemas

    def judge(self, envelope, schemas):
        canonical = {schema["$id"]: name for name, schema in schemas.items()}
        objects, positions = {}, {}
        for position, entry in enumerate(envelope["objects"]):
            name = canonical.get(entry["schema"])
            if name is None:
                raise AssertionError("unknown schema")
            value = entry["object"]
            PUBLIC.validate_instance(schemas, name, value, "exchange object")
            PUBLIC.validate_object_semantics(name, value, "exchange object")
            kind = name.removesuffix(".schema.json")
            identity = (kind, value[IDENTITIES[kind]])
            if identity in objects:
                raise AssertionError("duplicate typed identity")
            objects[identity] = value
            positions[identity] = position

        for (kind, identifier), value in objects.items():
            if kind == "block":
                draft = objects.get(("block-draft", value.get("draft_id")))
                if draft is not None:
                    require(all(draft[field] == value[field]
                                for field in ("owner_id", "block_type", "source_node_ids")))
                    require(draft["status"] in ("confirmed", "rewritten"))
                    require(value["confirmed_by_actor_id"] == value["owner_id"])
                    operation = "confirm" if draft["status"] == "confirmed" else "rewrite"
                    require(value["confirmation_operation"] == operation)
                correction = objects.get(("correction-patch", value.get("correction_id")))
                if (correction is not None and value["confirmation_operation"] == "rewrite"
                        and "draft_id" in value):
                    require(correction["target_type"] == "block_draft")
                    require(correction["target_id"] == value["draft_id"])
                    require(correction["actor_id"] == value["owner_id"])
                    require(correction["operation"] == "replace")
                    require(correction.get("path") == "/proposed_summary")
                    require(correction.get("after") == value.get("summary"))
                    require(PUBLIC.datetime_key(value["confirmed_at"]) >= PUBLIC.datetime_key(correction["created_at"]))
            elif kind == "invalidation-record":
                if value["trigger_type"] == "parent_invalidation":
                    parent_key = (kind, value["parent_invalidation_id"])
                    parent = objects.get(parent_key)
                    if parent is not None:
                        require(positions[parent_key] < positions[(kind, identifier)])
                        require(value["trigger_id"] == parent["idempotency_key"])
                elif value["trigger_type"] in ("source_change", "permission_change"):
                    change = objects.get(("source-state-change", value["trigger_id"]))
                    if change is not None:
                        expected = {
                            "redacted": ("source_change", "source_redacted", "invalidated"),
                            "deleted": ("source_change", "source_deleted", "invalidated"),
                            "permission_withdrawn": ("permission_change", "permission_withdrawn", "invalidated"),
                        }.get(change["new_state"])
                        if change["new_state"] == "stale":
                            require(value["resulting_state"] in ("invalidated", "review_required"))
                            expected = ("source_change", "source_stale", value["resulting_state"])
                        require(expected is not None)  # active has no linked invalidation
                        require((value["trigger_type"], value["reason_code"], value["resulting_state"]) == expected)

        for context in envelope["validation_contexts"]:
            kind, roles = context["kind"], context["roles"]
            if kind == "invalidation_chain":
                keys = [("invalidation-record", identity) for identity in roles["records"]]
                require(all(key in objects for key in keys))
                order = [positions[key] for key in keys]
                require(order == sorted(order))
                PUBLIC.validate_invalidation_chain_instance(
                    schemas, {"records": [objects[key] for key in keys]}, "context")
            else:
                members = {}
                for role, object_type in ROLE_TYPES[kind].items():
                    key = (object_type, roles[role])
                    require(key in objects)
                    members[role] = objects[key]
                validator = (PUBLIC.validate_protocol_chain_instance if kind == "protocol_chain"
                             else PUBLIC.validate_source_state_chain_instance)
                validator(schemas, members, "context")

    def evaluate(self, raw, content_type="application/json", content_encoding=None,
                 max_bytes=None, max_objects=None):
        try:
            return self._evaluate(raw, content_type, content_encoding, max_bytes, max_objects)
        except Exception:
            return problem("evaluation-failure")

    def check_receipt(self, request, result):
        status, media, body = result
        require(status == 200 and media == "application/json")
        self.wire_validator("ObjectExchangeReceipt").validate(body)
        require(all(body[key] == request[key] for key in
                    ("transport_version", "protocol_release", "exchange_id")))

    def _evaluate(self, raw, content_type, content_encoding, max_bytes, max_objects):
        if max_bytes is not None and len(raw) > max_bytes:
            return problem("payload-too-large")
        if not isinstance(content_type, str):
            return problem("unsupported-media-type")
        parts = [part.strip().lower() for part in content_type.split(";")]
        if (parts[0] != "application/json" or
                (len(parts) != 1 and parts != ["application/json", "charset=utf-8"]) or
                content_encoding not in (None, "identity")):
            return problem("unsupported-media-type")
        try:
            envelope = strict_json(raw)
        except (ValueError, UnicodeError, RecursionError):
            return problem("malformed-envelope")
        if (max_objects is not None and isinstance(envelope, dict)
                and isinstance(envelope.get("objects"), list)
                and len(envelope["objects"]) > max_objects):
            return problem("payload-too-large")
        try:
            self.wire_validator("ObjectExchangeEnvelope").validate(envelope)
        except ValidationError:
            return problem("malformed-envelope")
        if envelope["transport_version"] != TRANSPORT:
            return problem("unsupported-transport-version")
        if envelope["protocol_release"] != RELEASE:
            return problem("unsupported-protocol-release")
        try:
            schemas = self.verified_schemas()
            try:
                self.judge(envelope, schemas)
                verdict = "accepted"
            except (AssertionError, ValidationError):
                verdict = "rejected"
        except Exception:
            # No exception details or request data may leak into Problem Details.
            return problem("evaluation-failure")
        receipt = {key: envelope[key] for key in
                   ("transport_version", "protocol_release", "exchange_id")}
        receipt["status"] = verdict
        return 200, "application/json", receipt


if __name__ == "__main__":
    if sys.argv[1:] == ["--print-manifest"]:
        print(json.dumps(boundary_manifest(), indent=2))
    elif not sys.argv[1:]:
        verify_boundary()
        print("transport artifact byte manifest verified (tag publication not asserted)")
    else:
        sys.exit("usage: object-exchange-contract.py [--print-manifest]")
