#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate SDK wire metadata and byte-identical bindings from verified local inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "sdk/typescript"
NAMES = ("ObjectExchangeEnvelope", "ExchangeItem", "ValidationContext",
         "ProtocolChainContext", "SourceStateChainContext", "InvalidationChainContext",
         "ObjectExchangeReceipt", "MalformedEnvelope", "UnsupportedMediaType",
         "PayloadTooLarge", "UnsupportedTransportVersion", "UnsupportedProtocolRelease", "EvaluationFailure")
KEYWORDS = {"type", "description", "additionalProperties", "required", "properties",
            "minLength", "minItems", "uniqueItems", "items", "oneOf", "$ref", "const", "enum"}


def check_schema(schema):
    if set(schema) - KEYWORDS:
        raise ValueError("unsupported wire keyword")
    if schema.get("$ref", "#/components/schemas/").removeprefix("#/components/schemas/") not in NAMES and "$ref" in schema:
        raise ValueError("unsupported wire reference")
    for value in schema.get("properties", {}).values():
        check_schema(value)
    for value in schema.get("oneOf", []):
        check_schema(value)
    if "items" in schema:
        check_schema(schema["items"])


def type_of(schema):
    check_schema(schema)
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "oneOf" in schema:
        return " | ".join(type_of(value) for value in schema["oneOf"])
    if "const" in schema:
        return json.dumps(schema["const"])
    if "enum" in schema:
        return " | ".join(json.dumps(value) for value in schema["enum"])
    kind = schema["type"]
    if kind == "object":
        if "properties" not in schema:
            return "object"  # Runtime guard enforces record, not class/array.
        fields = [json.dumps(key) + ("" if key in schema.get("required", []) else "?") + ": " + type_of(value)
                  for key, value in schema["properties"].items()]
        return "{ " + "; ".join(fields) + " }"
    if kind == "array":
        return "Array<" + type_of(schema["items"]) + ">"
    if kind in ("string", "number", "boolean"):
        return kind
    if kind == "integer":
        return "number"
    raise ValueError("unsupported wire type")


def outputs():
    spec = importlib.util.spec_from_file_location("sdk_upstream", ROOT / "tools/object-exchange-contract.py")
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    contract.verify_boundary(ROOT)
    schemas = contract.ContractProbe(ROOT).verified_schemas()
    # Existing generator verifies every domain keyword and detects binding drift.
    import subprocess
    import sys
    subprocess.run([sys.executable, str(ROOT / "tools/generate-bindings.py"), "--check"], check=True, cwd=ROOT)
    document = contract.read(ROOT / contract.ARTIFACT)
    wire = {name: document["components"]["schemas"][name] for name in NAMES}
    declarations = ["// SPDX-License-Identifier: Apache-2.0", "// Generated; do not edit. No domain validity claim."]
    declarations += [f"export type {name} = {type_of(schema)};" for name, schema in wire.items()]
    declarations += ["export const wireSchemas = " + json.dumps(wire, ensure_ascii=True, indent=2) + " as const;",
                     "export const versions = { transport: \"1.0\", protocol: \"v0.1.0-preview.1\" } as const;"]
    problems = [{key: schema["properties"][key]["const"] for key in ("type", "title", "status")}
                for name, schema in wire.items() if name not in NAMES[:7]]
    declarations += ["export const problems = " + json.dumps(problems, indent=2) + " as const;"]
    files = {"src/generated/wire.ts": ("\n".join(declarations) + "\n").encode()}
    source_hashes = {}
    facade = ["// SPDX-License-Identifier: Apache-2.0", "// Generated ESM facade; original declaration bytes remain unchanged."]
    for path in sorted((ROOT / "bindings/typescript/v0.1.0-preview.1").glob("*.d.ts")):
        data = path.read_bytes()
        relative = str(path.relative_to(ROOT))
        original = subprocess.run(["git", "show", "0728b46a6db55a272bcad6e05745d86628632c96:" + relative],
                                  cwd=ROOT, check=True, capture_output=True).stdout
        if original != data:
            raise ValueError("binding snapshot differs from pinned commit")
        files["src/generated/protocol/" + path.name] = data
        source_hashes[relative] = hashlib.sha256(data).hexdigest()
        if path.name != "index.d.ts":
            facade.append('export type * from "./generated/protocol/' + path.name.removesuffix(".d.ts") + '.js";')
    files["src/protocol.ts"] = ("\n".join(facade) + "\n").encode()
    provenance = {"schema_release": contract.RELEASE, "transport_tag": contract.TAG,
                  "binding_snapshot_commit": "0728b46a6db55a272bcad6e05745d86628632c96",
                  "planning_merge": "ff5d8906fb24b513bb641fdbd2f087c327bc101e",
                  "binding_sha256": source_hashes,
                  "canonical_schema_ids": sorted(value["$id"] for value in schemas.values()),
                  "transport_manifest_sha256": hashlib.sha256((ROOT / contract.MANIFEST).read_bytes()).hexdigest()}
    files["provenance.json"] = (json.dumps(provenance, indent=2) + "\n").encode()
    files["LICENSE-APACHE-2.0.txt"] = (ROOT / "LICENSE-APACHE-2.0.txt").read_bytes()
    lock = json.loads((PACKAGE / "package-lock.json").read_text(encoding="utf-8"))
    inventory = [{"SPDXID": "SPDXRef-SDK", "name": lock["name"], "versionInfo": lock["version"],
                  "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
                  "licenseDeclared": "Apache-2.0"}]
    for index, (name, dependency) in enumerate(sorted(lock["packages"].items())):
        if not name:
            continue
        inventory.append({"SPDXID": f"SPDXRef-Dev-{index}", "name": name.removeprefix("node_modules/"),
                          "versionInfo": dependency["version"], "downloadLocation": dependency["resolved"],
                          "filesAnalyzed": False, "licenseDeclared": dependency.get("license", "NOASSERTION"),
                          "comment": "Development lock inventory; optional platform packages are not all installed. Not a runtime dependency."})
    sbom = {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
            "name": "Unpublished SDK workspace and development lock inventory",
            "documentNamespace": "https://www.fnbapp.net/spdx/sdk-workspace/" + hashlib.sha256(json.dumps(lock, sort_keys=True).encode()).hexdigest(),
            "creationInfo": {"created": "2026-10-09T00:00:00Z", "creators": ["Tool: fnb-open-sdk-generator"]},
            "packages": inventory,
            "relationships": [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-SDK"}] +
                [{"spdxElementId": item["SPDXID"], "relationshipType": "BUILD_TOOL_OF", "relatedSpdxElement": "SPDXRef-SDK"} for item in inventory[1:]]}
    files["sbom.spdx.json"] = (json.dumps(sbom, indent=2) + "\n").encode()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    actual = {str(path.relative_to(PACKAGE)) for path in (PACKAGE / "src/generated").rglob("*") if path.is_file()}
    expected = {name for name in generated if name.startswith("src/generated/")}
    if actual - expected:
        raise SystemExit("unexpected generated SDK file")
    for name, data in generated.items():
        path = PACKAGE / name
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit("SDK generation drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print("SDK generated inputs current" if args.check else "SDK generated inputs written")


if __name__ == "__main__":
    main()
