# SPDX-License-Identifier: Apache-2.0
"""Offline contract tests, not network or third-party implementation certification."""

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("exchange_contract", ROOT / "tools/object-exchange-contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
PREFIX = f"https://raw.githubusercontent.com/FNB2026/fnb-open/{contract.RELEASE}/specs/v0.1/"


def world(name):
    return contract.read(ROOT / f"tests/fixtures/generated/{name}.seed-42.json")


def envelope(material):
    entries = [{"schema": PREFIX + material["object_schemas"][name], "object": value}
               for name, value in material["objects"].items()]
    contexts = []
    for description in material["validation"]:
        kind = description["kind"]
        if kind == "invalidation_chain":
            roles = {"records": [material["objects"][name]["invalidation_id"]
                                 for name in description["records"]]}
        else:
            roles = {}
            for role, name in description["members"].items():
                schema = material["object_schemas"][name].removesuffix(".schema.json")
                roles[role] = material["objects"][name][contract.IDENTITIES[schema]]
        contexts.append({"kind": kind, "roles": roles})
    return {"transport_version": "1.0", "protocol_release": contract.RELEASE,
            "exchange_id": "synthetic-contract-case", "objects": entries,
            "validation_contexts": contexts}


def rekey(value):
    fields = ("trigger_type", "trigger_id", "target_type", "target_id", "resulting_state")
    value["idempotency_key"] = "sha256:" + hashlib.sha256(
        "|".join(value[field] for field in fields).encode()).hexdigest()


def independent(request):
    identifiers = {}
    for entry in request["objects"]:
        name = entry["schema"].removeprefix(PREFIX).removesuffix(".schema.json")
        identity = entry["object"][contract.IDENTITIES[name]]
        identifiers[identity] = identity + "_second"

    def rewrite(value):
        if isinstance(value, str):
            return identifiers.get(value, value)
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {key: rewrite(item) for key, item in value.items()}
        return value

    return rewrite(request)


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.probe = contract.ContractProbe()
        self.request = envelope(world("basic-memory"))

    def evaluate(self, request=None, **kwargs):
        raw = json.dumps(self.request if request is None else request).encode()
        return self.probe.evaluate(raw, **kwargs)

    def assert_outcome(self, result, outcome):
        status, media, body = result
        self.assertEqual(status, 200)
        self.assertEqual(media, "application/json")
        self.assertEqual(body["status"], outcome)
        self.assertEqual(set(body), {"transport_version", "protocol_release", "exchange_id", "status"})
        self.probe.wire_validator("ObjectExchangeReceipt").validate(body)

    def assert_problem(self, result, suffix):
        status, media, body = result
        self.assertEqual(media, "application/problem+json")
        self.assertEqual(status, contract.PROBLEMS[suffix][0])
        self.assertEqual(body["status"], status)
        self.assertTrue(body["type"].endswith("/" + suffix))
        self.assertEqual(set(body), {"type", "title", "status"})
        schema = self.probe.document["paths"]["/exchange"]["post"]["responses"][str(status)]["content"][media]["schema"]
        Draft202012Validator({**self.probe.document, **schema}).validate(body)

    def item(self, kind, request=None):
        return next(entry["object"] for entry in (request or self.request)["objects"]
                    if entry["schema"] == PREFIX + kind + ".schema.json")

    def test_openapi_structure_and_schema_dialect(self):
        metadata = contract.read(ROOT / "tests/conformance/transport/openapi-3.1.schema.json")
        Draft202012Validator(metadata).validate(self.probe.document)
        doc = self.probe.document
        self.assertEqual(doc["openapi"], "3.1.0")
        self.assertEqual(doc["jsonSchemaDialect"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(set(doc["paths"]), {"/exchange"})
        self.assertEqual(set(doc["paths"]["/exchange"]), {"post"})
        self.assertNotIn("servers", doc)
        self.assertNotIn("securitySchemes", doc["components"])
        self.assertEqual(set(doc["paths"]["/exchange"]["post"]["responses"]), {"200", "400", "413", "415", "500"})
        for schema in doc["components"]["schemas"].values():
            Draft202012Validator.check_schema(schema)

    def test_exact_frozen_schema_reference_set(self):
        schemas = self.probe.verified_schemas()
        refs = {value["$ref"] for value in self.probe.document["components"]["schemas"].values()
                if "$ref" in value and not value["$ref"].startswith("#")}
        self.assertEqual(refs, {value["$id"] for value in schemas.values()})
        declared = self.probe.document["x-fnb-protocol-schemas"]
        self.assertEqual({item["schema"]: item["identity_field"] for item in declared},
                         {PREFIX + name + ".schema.json": field for name, field in contract.IDENTITIES.items()})
        registry = Registry().with_resources((value["$id"], Resource.from_contents(value))
                                             for value in schemas.values())
        samples = {}
        for scenario in ("basic-memory", "relationship-correction", "source-redaction", "permission-withdrawal"):
            material = world(scenario)
            samples.update({material["object_schemas"][key].removesuffix(".schema.json"): value
                            for key, value in material["objects"].items()})
        for name, field in contract.IDENTITIES.items():
            self.assertIn(field, schemas[name + ".schema.json"]["required"])
            sample_path = ROOT / f"tests/conformance/v0.1/valid/{name}.json"
            sample = contract.read(sample_path)["instance"] if sample_path.exists() else samples[name]
            self.probe.wire_validator("Protocol_" + name.replace("-", "_"), registry).validate(sample)

    def test_all_synthetic_worlds(self):
        for name in ("basic-memory", "relationship-correction", "source-redaction", "permission-withdrawal"):
            with self.subTest(name=name):
                self.assert_outcome(self.evaluate(envelope(world(name))), "accepted")

    def test_echo_preserves_strings(self):
        self.request["exchange_id"] = "  Synthetic / Unicode ☕  "
        result = self.evaluate()
        self.assert_outcome(result, "accepted")
        self.probe.check_receipt(self.request, result)
        for key in ("transport_version", "protocol_release", "exchange_id"):
            self.assertEqual(result[2][key], self.request[key])
            broken = dict(result[2], **{key: "wrong"})
            with self.assertRaises(AssertionError):
                self.probe.check_receipt(self.request, (result[0], result[1], broken))

    def test_schema_invalid_is_receipt_not_envelope_error(self):
        self.request["objects"][0]["object"] = {}
        self.assert_outcome(self.evaluate(), "rejected")

    def test_invalid_datetime_is_rejected_for_standalone_object(self):
        for timestamp in ("not-a-timestamp", "2026-01-01T12:00:00", "2026-02-30T12:00:00Z"):
            with self.subTest(timestamp=timestamp):
                value = copy.deepcopy(self.item("flow-event"))
                value["occurred_at"] = timestamp
                request = {**self.request, "objects": [{"schema": PREFIX + "flow-event.schema.json",
                                                        "object": value}], "validation_contexts": []}
                self.assert_outcome(self.evaluate(request), "rejected")

    def test_missing_format_capability_fails_closed(self):
        schemas = self.probe.verified_schemas()
        capabilities = dict(contract.PUBLIC.FORMAT_CHECKER.checkers)
        capabilities.pop("date-time")
        with patch.object(contract.PUBLIC.FORMAT_CHECKER, "checkers", capabilities):
            # Declaring this release requires all its format capabilities, even
            # when the particular request is a valid standalone actor.
            actor = self.request["objects"][0]
            request = {**self.request, "objects": [actor], "validation_contexts": []}
            self.assert_problem(self.evaluate(request), "evaluation-failure")
            with self.assertRaises(RuntimeError):
                contract.PUBLIC.validate_instance(schemas,
                    "flow-event.schema.json", self.item("flow-event"), "format guard")

    def test_timestamp_instants_case_offsets_and_full_precision(self):
        key = contract.PUBLIC.datetime_key
        self.assertEqual(key("2026-01-01t00:00:00z"), key("2026-01-01T08:00:00+08:00"))
        self.assertEqual(key("2026-01-01T00:00:00.1Z"), key("2026-01-01T00:00:00.100000000Z"))
        self.assertLess(key("2026-01-01T00:00:00.0000001Z"), key("2026-01-01T00:00:00.0000002Z"))
        material = world("source-redaction")
        snapshot = material["objects"]["permission_snapshot"]
        snapshot["captured_at"] = "2026-01-01t00:00:00.0000001z"
        snapshot["expires_at"] = "2026-01-01T08:00:00.0000002+08:00"
        request = envelope(material)
        self.assert_outcome(self.evaluate(request), "accepted")
        self.item("permission-snapshot", request)["expires_at"] = "2026-01-01T00:00:00.0000000Z"
        self.assert_outcome(self.evaluate(request), "rejected")
        request = copy.deepcopy(self.request)
        request["validation_contexts"] = []
        correction = self.item("correction-patch", request)
        block = self.item("block", request)
        block["confirmation_operation"] = "rewrite"
        block["correction_id"] = correction["correction_id"]
        self.item("block-draft", request)["status"] = "rewritten"
        correction.update(operation="replace", path="/proposed_summary", after=block.get("summary"),
                          created_at="2026-01-01T00:00:00.0000002Z")
        block["confirmed_at"] = "2026-01-01T00:00:00.0000001Z"
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_unknown_schema_never_resolved(self):
        self.request["objects"][0]["schema"] = "https://sender.invalid/private.schema.json"
        self.assert_outcome(self.evaluate(), "rejected")

    def test_duplicate_typed_identity(self):
        for conflicting in (False, True):
            with self.subTest(conflicting=conflicting):
                request = copy.deepcopy(self.request)
                duplicate = copy.deepcopy(request["objects"][0])
                if conflicting:
                    duplicate["object"]["display_name"] = "Changed synthetic actor"
                request["objects"].append(duplicate)
                self.assert_outcome(self.evaluate(request), "rejected")

    def test_direct_draft_checks_cannot_be_omitted(self):
        for field, bad in (("owner_id", "fnb_actor_other"), ("source_node_ids", ["fnb_node_other"]),
                           ("block_type", "task"), ("confirmed_by_actor_id", "fnb_actor_other"),
                           ("confirmation_operation", "rewrite")):
            with self.subTest(field=field):
                request = copy.deepcopy(self.request)
                request["validation_contexts"] = []
                self.item("block", request)[field] = bad
                self.assert_outcome(self.evaluate(request), "rejected")
        for status in ("pending", "rejected"):
            request = copy.deepcopy(self.request)
            request["validation_contexts"] = []
            self.item("block-draft", request)["status"] = status
            self.assert_outcome(self.evaluate(request), "rejected")

    def test_context_missing_role_object(self):
        self.request["validation_contexts"][0]["roles"]["flow_event"] = "fnb_evt_external"
        self.assert_outcome(self.evaluate(), "rejected")

    def test_context_cross_pairing_is_rejected(self):
        second = envelope(world("basic-memory"))
        # Rename every protocol ID consistently to form an independent chain.
        second = independent(second)
        self.request["objects"].extend(second["objects"])
        self.request["validation_contexts"].extend(second["validation_contexts"])
        self.assert_outcome(self.evaluate(), "accepted")
        self.request["validation_contexts"][0]["roles"]["node"] = second["validation_contexts"][0]["roles"]["node"]
        self.assert_outcome(self.evaluate(), "rejected")

    def test_interleaved_chains(self):
        second = independent(self.request)
        self.request["objects"] = [value for pair in zip(self.request["objects"], second["objects"]) for value in pair]
        self.request["validation_contexts"].extend(second["validation_contexts"])
        self.assert_outcome(self.evaluate(), "accepted")

    def test_missing_external_reference_is_allowed(self):
        self.request["validation_contexts"] = []
        self.request["objects"] = [entry for entry in self.request["objects"]
                                   if entry["schema"].endswith("/block.schema.json")]
        self.assert_outcome(self.evaluate(), "accepted")

    def test_invalidation_parent_and_context_order(self):
        request = envelope(world("relationship-correction"))
        self.assert_outcome(self.evaluate(request), "accepted")
        reversed_context = copy.deepcopy(request)
        reversed_context["validation_contexts"][0]["roles"]["records"].reverse()
        self.assert_outcome(self.evaluate(reversed_context), "rejected")
        request["validation_contexts"] = []
        request["objects"].reverse()
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_external_parent_without_context(self):
        request = envelope(world("relationship-correction"))
        child = next(entry for entry in request["objects"]
                     if entry["object"].get("trigger_type") == "parent_invalidation")
        request["objects"] = [child]
        request["validation_contexts"] = []
        self.assert_outcome(self.evaluate(request), "accepted")
        request["validation_contexts"] = [{"kind": "invalidation_chain", "roles": {"records": [child["object"]["invalidation_id"]]}}]
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_bad_parent_key_and_repeat_target(self):
        request = envelope(world("relationship-correction"))
        parent, child = [entry["object"] for entry in request["objects"]
                         if entry["schema"].endswith("/invalidation-record.schema.json")]
        child["trigger_id"] = "sha256:" + "0" * 64
        rekey(child)
        self.assert_outcome(self.evaluate(request), "rejected")
        child["trigger_id"] = parent["idempotency_key"]
        child["target_type"], child["target_id"] = parent["target_type"], parent["target_id"]
        rekey(child)
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_distinct_contexts_may_repeat_target(self):
        request = envelope(world("relationship-correction"))
        root = next(entry for entry in request["objects"]
                    if entry["object"].get("trigger_type") == "correction_patch")
        other = copy.deepcopy(root)
        other["object"]["invalidation_id"] += "_second"
        other["object"]["trigger_id"] += "_second"
        rekey(other["object"])
        request["objects"] = [root, other]
        request["validation_contexts"] = [{"kind": "invalidation_chain", "roles": {"records": [entry["object"]["invalidation_id"]]}} for entry in request["objects"]]
        self.assert_outcome(self.evaluate(request), "accepted")

    def test_snapshot_is_selected_not_guessed(self):
        request = envelope(world("source-redaction"))
        snapshot = next(entry for entry in request["objects"]
                        if entry["schema"].endswith("/permission-snapshot.schema.json"))
        other = copy.deepcopy(snapshot)
        other["object"]["permission_snapshot_id"] += "_other"
        other["object"]["source_ref"] = "synthetic://different-source"
        request["objects"].append(other)
        self.assert_outcome(self.evaluate(request), "accepted")
        request["validation_contexts"][0]["roles"]["permission_snapshot"] = other["object"]["permission_snapshot_id"]
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_direct_source_mapping_without_context(self):
        request = envelope(world("source-redaction"))
        request["validation_contexts"] = []
        value = self.item("invalidation-record", request)
        value["reason_code"] = "source_deleted"
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_direct_rewrite_checks_without_full_context(self):
        chain = contract.read(ROOT / "examples/synthetic-protocol-chain.json")
        material = {"objects": chain,
                    "object_schemas": contract.PUBLIC.CHAIN_SCHEMA_MAP,
                    "validation": [{"kind": "protocol_chain",
                                    "members": {role: role for role in contract.PUBLIC.CHAIN_SCHEMA_MAP}}]}
        request = envelope(material)
        self.assert_outcome(self.evaluate(request), "accepted")
        request["validation_contexts"] = []
        for field, bad in (("actor_id", "fnb_actor_other"), ("target_id", "fnb_draft_other"),
                           ("target_type", "node"), ("path", "/different_path"),
                           ("after", "Different synthetic summary"),
                           ("created_at", "2099-01-01T00:00:00Z")):
            with self.subTest(field=field):
                changed = copy.deepcopy(request)
                correction = self.item("correction-patch", changed)
                correction[field] = bad
                self.assert_outcome(self.evaluate(changed), "rejected")

    def test_active_source_has_no_linked_invalidation(self):
        request = envelope(world("source-redaction"))
        request["validation_contexts"] = []
        change = self.item("source-state-change", request)
        change.update(previous_state="stale", new_state="active", reason_code="source_restored")
        standalone = copy.deepcopy(request)
        standalone["objects"] = [entry for entry in standalone["objects"]
                                  if entry["schema"].endswith("/source-state-change.schema.json")]
        self.assert_outcome(self.evaluate(standalone), "accepted")
        self.assert_outcome(self.evaluate(request), "rejected")

    def test_later_snapshot_does_not_replace_explicit_role(self):
        request = envelope(world("source-redaction"))
        existing = next(entry for entry in request["objects"]
                        if entry["schema"].endswith("/permission-snapshot.schema.json"))
        later = copy.deepcopy(existing)
        later["object"]["permission_snapshot_id"] += "_later"
        later["object"]["captured_at"] = "2026-02-01T00:00:00Z"
        request["objects"].insert(0, later)
        self.assert_outcome(self.evaluate(request), "accepted")

    def test_every_existing_source_chain_mapping(self):
        for path in sorted((ROOT / "tests/conformance/v0.1/valid-source-state-chains").glob("*.json")):
            with self.subTest(path=path.name):
                chain = contract.read(path)
                material = {"objects": chain,
                            "object_schemas": {"permission_snapshot": "permission-snapshot.schema.json",
                                               "source_state_change": "source-state-change.schema.json",
                                               "invalidation": "invalidation-record.schema.json"},
                            "validation": [{"kind": "source_state_chain", "members": {
                                "permission_snapshot": "permission_snapshot",
                                "source_state_change": "source_state_change", "invalidation": "invalidation"}}]}
                request = envelope(material)
                self.assert_outcome(self.evaluate(request), "accepted")
                request["validation_contexts"] = []
                self.assert_outcome(self.evaluate(request), "accepted")

    def test_malformed_envelopes(self):
        requests = []
        for key in self.request:
            value = copy.deepcopy(self.request)
            del value[key]
            requests.append(value)
        for value in (dict(self.request, extra=True), dict(self.request, exchange_id=""),
                      dict(self.request, objects=[]), dict(self.request, validation_contexts=[{"kind": "unknown", "roles": {}}])):
            requests.append(value)
        value = copy.deepcopy(self.request)
        value["objects"][0]["object"] = []
        requests.append(value)
        value = copy.deepcopy(self.request)
        value["objects"][0]["extra"] = True
        requests.append(value)
        value = copy.deepcopy(self.request)
        del value["validation_contexts"][0]["roles"]["block"]
        requests.append(value)
        for index, request in enumerate(requests):
            with self.subTest(index=index):
                self.assert_problem(self.evaluate(request), "malformed-envelope")

    def test_strict_raw_json_and_number_precision(self):
        raw_values = [b"{", b"\xff", b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}',
                      b'{"a":NaN}', b'{"a":Infinity}', b'{"a":-Infinity}']
        for raw in raw_values:
            with self.subTest(raw=raw):
                self.assert_problem(self.probe.evaluate(raw), "malformed-envelope")
        self.assertEqual(contract.strict_json(b'{"n":9007199254740993.1}')["n"], Decimal("9007199254740993.1"))

    def test_media_encoding_capacity_and_stage_order(self):
        for media in ("text/plain", "application/json;charset=latin1", "application/json;profile=x"):
            self.assert_problem(self.evaluate(content_type=media), "unsupported-media-type")
        for encoding in ("gzip", "br"):
            self.assert_problem(self.evaluate(content_encoding=encoding), "unsupported-media-type")
        self.assert_outcome(self.evaluate(content_type="APPLICATION/JSON; CHARSET=UTF-8"), "accepted")
        self.assert_problem(self.evaluate(max_bytes=1), "payload-too-large")
        self.assert_problem(self.evaluate(max_objects=1), "payload-too-large")
        self.assert_problem(self.probe.evaluate(b"{", content_type="text/plain"), "unsupported-media-type")
        self.request["transport_version"] = "9.0"
        self.request["protocol_release"] = "v9.9.9"
        self.assert_problem(self.evaluate(), "unsupported-transport-version")
        self.request["transport_version"] = "1.0"
        self.assert_problem(self.evaluate(), "unsupported-protocol-release")

    def test_internal_failure_not_verdict_or_data_leak(self):
        for method in ("verified_schemas", "judge", "wire_validator"):
            with self.subTest(method=method), patch.object(self.probe, method, side_effect=RuntimeError("SECRET /private/path")):
                result = self.evaluate()
                self.assert_problem(result, "evaluation-failure")
                self.assertNotIn("SECRET", json.dumps(result))

    def test_corrupt_manifest_and_schema_not_receipt(self):
        with tempfile.TemporaryDirectory(prefix="fnb-transport-integrity-") as directory:
            root = Path(directory)
            (root / contract.ARTIFACT).parent.mkdir(parents=True)
            (root / contract.ARTIFACT).write_bytes((ROOT / contract.ARTIFACT).read_bytes())
            manifest_path = root / contract.PUBLIC_MANIFEST
            manifest_path.parent.mkdir(parents=True)
            manifest = contract.read(ROOT / contract.PUBLIC_MANIFEST)
            for entry in manifest["schemas"]:
                destination = root / entry["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / entry["path"]).read_bytes())
            manifest_path.write_text(json.dumps(manifest))
            probe = contract.ContractProbe(root)
            raw = json.dumps(self.request).encode()
            self.assert_outcome(probe.evaluate(raw), "accepted")
            manifest["protocol_release"] = "v9.9.9"
            manifest_path.write_text(json.dumps(manifest))
            self.assert_problem(probe.evaluate(raw), "evaluation-failure")
            manifest["protocol_release"] = contract.RELEASE
            manifest_path.write_text(json.dumps(manifest))
            (root / manifest["schemas"][0]["path"]).write_bytes(b"{}")
            self.assert_problem(probe.evaluate(raw), "evaluation-failure")

    def test_transport_manifest(self):
        contract.verify_boundary()
        expected = contract.boundary_manifest()
        self.assertEqual(expected["release_tag"], "object-exchange-v1.0.0-preview.1")
        self.assertNotEqual(expected["release_tag"], contract.RELEASE)
        with patch.object(contract, "read", return_value={**expected, "release_tag": "main"}):
            with self.assertRaises(AssertionError):
                contract.verify_boundary()


if __name__ == "__main__":
    unittest.main()
