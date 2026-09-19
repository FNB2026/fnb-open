#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deterministic generator for FNB protocol TypeScript bindings.

Usage:

    python3 tools/generate-bindings.py            # write the bindings
    python3 tools/generate-bindings.py --check    # verify committed bindings

The generator is manifest-driven and fail-closed:

1. read the frozen release manifest
   (``specs/v0.1/releases/<tag>/schema-digests.json``);
2. verify every listed schema byte length and SHA-256 against the manifest;
3. verify every schema ``$id`` is pinned to the frozen tag namespace;
4. reject every JSON Schema keyword outside the explicitly supported set;
5. emit declaration-only TypeScript bindings.

Unsupported semantics are a hard error. Nothing is silently downgraded, and no
conditional ``if``/``then`` relationship is flattened into a wider interface.

``--check`` re-renders the bindings in memory and compares them byte for byte
against the files on disk. That single check is the completeness proof that the
committed bindings are current; CI additionally runs ``git diff --exit-code``
only as a guard against the generator mutating the working tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

DEFAULT_MANIFEST = Path(
    "specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json"
)
OUTPUT_ROOT = Path("bindings/typescript")
REPOSITORY = "FNB2026/fnb-open"

# Keywords this generator understands. Anything else is a hard failure so that a
# newly introduced schema keyword is reviewed deliberately instead of being
# dropped on the floor.
METADATA_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "$comment",
        "default",
        "examples",
        "deprecated",
    }
)
MAPPED_KEYWORDS = frozenset(
    {
        "type",
        "enum",
        "const",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "allOf",
        "if",
        "then",
    }
)
# Recognized, not expressible in TypeScript. Reported in JSDoc instead of being
# presented as if the type system enforced it.
RUNTIME_ONLY_KEYWORDS = frozenset(
    {
        "pattern",
        "format",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minProperties",
        "maxProperties",
        "contentMediaType",
    }
)
SUPPORTED_KEYWORDS = METADATA_KEYWORDS | MAPPED_KEYWORDS | RUNTIME_ONLY_KEYWORDS

SCALAR_TYPES = {
    "string": "string",
    "number": "number",
    "integer": "number",
    "boolean": "boolean",
    "null": "null",
    "object": "Record<string, unknown>",
    "array": "unknown[]",
}

IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
# Guard against surprising branch explosion when enumerating conditional rules.
MAX_BRANCHES = 512

RUNTIME_PREFIX = "Runtime JSON Schema constraint, not expressible in TypeScript: "


class GenerationError(Exception):
    """Raised when the frozen protocol artifacts cannot be rendered faithfully."""


class Rule:
    """One ``allOf`` member of the form ``{if: ..., then: ...}``."""

    def __init__(self, key: str, triggers: frozenset[str], then: dict[str, Any]) -> None:
        self.key = key
        self.triggers = triggers
        self.then = then


def pascal_case(value: str) -> str:
    parts = re.split(r"[^0-9A-Za-z]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def singular(value: str) -> str:
    """Deterministic singularization for array element type names.

    Only a trailing ``s`` is stripped, and only for names longer than three
    characters. The rule is intentionally dumb and documented; a collision it
    produces fails generation rather than silently renaming a type.
    """
    if len(value) > 3 and value.endswith("s") and not value.endswith("ss"):
        return value[:-1]
    return value


def is_object_like(node: dict[str, Any]) -> bool:
    return (
        node.get("type") == "object"
        or "properties" in node
        or "allOf" in node
    )


def member_name(name: str) -> str:
    return name if IDENTIFIER.match(name) else json.dumps(name)


def literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise GenerationError(f"unsupported literal value: {value!r}")


def literal_union(values: list[Any]) -> str:
    if not values:
        raise GenerationError("enum must not be empty")
    rendered = [literal(item) for item in values]
    if len(set(rendered)) != len(rendered):
        raise GenerationError("enum contains duplicate values")
    return " | ".join(rendered)


def jsdoc(lines: list[str], indent: str) -> list[str]:
    lines = [line for line in lines if line]
    if not lines:
        return []
    if len(lines) == 1:
        return [f"{indent}/** {lines[0]} */"]
    out = [f"{indent}/**"]
    out.extend(f"{indent} * {line}".rstrip() for line in lines)
    out.append(f"{indent} */")
    return out


def runtime_notes(node: dict[str, Any]) -> list[str]:
    notes = []
    for key in sorted(RUNTIME_ONLY_KEYWORDS & set(node)):
        value = node[key]
        if key == "uniqueItems" and value is True:
            notes.append("array items must be unique")
        elif key == "format":
            notes.append(f"format `{value}`")
        elif isinstance(value, list):
            notes.append(f"{key} {json.dumps(value)}")
        else:
            notes.append(f"{key} `{value}`")
    return notes


class BindingsFile:
    """Renders a single schema into a TypeScript declaration module."""

    def __init__(
        self, schema_path: str, schema: dict[str, Any], tag: str, digest: str
    ) -> None:
        self.schema_path = schema_path
        self.schema = schema
        self.tag = tag
        self.digest = digest
        self.declarations: list[str] = []
        self.registered: dict[str, str] = {}
        title = schema.get("title")
        if not isinstance(title, str) or not title:
            raise GenerationError(f"{schema_path}: schema title is required for type naming")
        self.root_name = title

    # -- keyword validation -------------------------------------------------

    def check_keywords(self, node: dict[str, Any], where: str) -> None:
        unknown = sorted(set(node) - SUPPORTED_KEYWORDS)
        if unknown:
            raise GenerationError(
                f"{self.schema_path}:{where}: unsupported JSON Schema keyword(s) {unknown}. "
                "Extend the generator deliberately; it never downgrades silently."
            )

    def reserve(self, name: str, origin: str) -> None:
        previous = self.registered.get(name)
        if previous is not None and previous != origin:
            raise GenerationError(
                f"{self.schema_path}: generated type name {name!r} collides between "
                f"{previous} and {origin}"
            )
        self.registered[name] = origin

    # -- rendering ----------------------------------------------------------

    def render(self) -> str:
        self.render_node(self.schema, self.root_name, "$")
        return self.compose()

    def render_node(self, node: dict[str, Any], name: str, where: str) -> str:
        self.check_keywords(node, where)

        if "const" in node:
            return literal(node["const"])
        if "enum" in node:
            return literal_union(node["enum"])

        node_type = node.get("type")
        if isinstance(node_type, list):
            return " | ".join(
                SCALAR_TYPES.get(item, "unknown") if isinstance(item, str) else "unknown"
                for item in node_type
            )

        if node_type == "array":
            items = node.get("items")
            if items is None:
                return "unknown[]"
            item_name = name if is_object_like(items) else f"{name}Item"
            return f"{self.render_node(items, item_name, f'{where}[]')}[]"

        if is_object_like(node):
            return self.render_object(node, name, where)

        if isinstance(node_type, str):
            return SCALAR_TYPES.get(node_type, "unknown")
        return "unknown"

    def render_object(self, node: dict[str, Any], name: str, where: str) -> str:
        additional = node.get("additionalProperties")
        if additional is not None and additional is not False:
            raise GenerationError(
                f"{self.schema_path}:{where}: additionalProperties as a schema is not supported"
            )

        required = set(node.get("required", []))
        properties: dict[str, Any] = node.get("properties", {})
        missing = sorted(required - set(properties))
        if missing:
            raise GenerationError(
                f"{self.schema_path}:{where}: required properties without a definition: {missing}"
            )

        rules = self.collect_rules(node, where)
        base_name = name if not rules else f"{name}Base"

        docs: list[str] = []
        description = node.get("description")
        if isinstance(description, str) and description:
            docs.append(description.strip())
        object_notes = runtime_notes(node)
        if additional is False:
            object_notes.append("additionalProperties is false")
        if object_notes:
            docs.append(RUNTIME_PREFIX + "; ".join(object_notes) + ".")
        if rules:
            docs.append(
                f"Conditional protocol requirements are expressed by the {name} union; "
                "this interface holds only the unconditional fields."
            )

        lines = jsdoc(docs, "")
        lines.append(f"export interface {base_name} {{")
        for prop, sub in properties.items():
            lines.extend(self.render_member(f"{where}.{prop}", prop, sub, prop in required, name))
        lines.append("}")
        self.reserve(base_name, where)
        self.declarations.append("\n".join(lines))

        if not rules:
            return name

        variants = self.render_variants(properties, rules, name, where)
        decl = [f"export type {name} = {base_name} & ("]
        decl.append("  | " + "\n  | ".join(variants))
        decl.append(");")
        self.reserve(name, where)
        self.declarations.append("\n".join(decl))
        return name

    def render_member(
        self,
        where: str,
        prop: str,
        sub: dict[str, Any],
        required: bool,
        owner_name: str,
    ) -> list[str]:
        docs: list[str] = []
        description = sub.get("description") or sub.get("title")
        if isinstance(description, str) and description:
            docs.append(description.strip())
        notes = runtime_notes(sub)
        if sub.get("additionalProperties") is False and is_object_like(sub):
            notes.append("additionalProperties is false")
        if notes:
            docs.append(RUNTIME_PREFIX + "; ".join(notes) + ".")

        child_name = f"{owner_name}{pascal_case(prop)}"
        if sub.get("type") == "array" and isinstance(sub.get("items"), dict):
            if is_object_like(sub["items"]):
                child_name = f"{owner_name}{pascal_case(singular(prop))}"

        rendered = self.render_node(sub, child_name, where)
        optional = "" if required else "?"
        return jsdoc(docs, "  ") + [f"  {member_name(prop)}{optional}: {rendered};"]

    # -- conditional semantics ---------------------------------------------

    def collect_rules(self, node: dict[str, Any], where: str) -> list[Rule]:
        rules: list[Rule] = []
        for index, member in enumerate(node.get("allOf", [])):
            at = f"{where}/allOf[{index}]"
            if not isinstance(member, dict):
                raise GenerationError(f"{self.schema_path}:{at}: allOf members must be objects")
            extra = sorted(set(member) - {"if", "then"})
            if extra:
                raise GenerationError(
                    f"{self.schema_path}:{at}: unsupported allOf member keyword(s) {extra}"
                )
            if "if" not in member or "then" not in member:
                raise GenerationError(f"{self.schema_path}:{at}: if and then are both required")

            condition = member["if"]
            if not isinstance(condition, dict):
                raise GenerationError(f"{self.schema_path}:{at}/if: must be an object")
            self.check_keywords(condition, f"{at}/if")
            extra_condition = sorted(set(condition) - {"properties", "required"})
            if extra_condition:
                raise GenerationError(
                    f"{self.schema_path}:{at}/if: unsupported condition keyword(s) "
                    f"{extra_condition}"
                )
            condition_properties = condition.get("properties", {})
            if not isinstance(condition_properties, dict) or len(condition_properties) != 1:
                raise GenerationError(
                    f"{self.schema_path}:{at}/if: exactly one discriminated property is required"
                )
            key, spec = next(iter(condition_properties.items()))
            if key not in condition.get("required", []):
                raise GenerationError(
                    f"{self.schema_path}:{at}/if: the discriminated property must be required"
                )
            triggers = self.trigger_values(spec, f"{at}/if/properties/{key}")

            consequence = member["then"]
            if not isinstance(consequence, dict):
                raise GenerationError(f"{self.schema_path}:{at}/then: must be an object")
            self.check_keywords(consequence, f"{at}/then")
            extra_consequence = sorted(set(consequence) - {"required", "properties"})
            if extra_consequence:
                raise GenerationError(
                    f"{self.schema_path}:{at}/then: unsupported consequence keyword(s) "
                    f"{extra_consequence}"
                )
            rules.append(Rule(key, triggers, consequence))
        return rules

    def trigger_values(self, spec: dict[str, Any], where: str) -> frozenset[str]:
        if "const" in spec:
            return frozenset({literal(spec["const"])})
        if "enum" in spec:
            return frozenset(literal(item) for item in spec["enum"])
        raise GenerationError(f"{self.schema_path}:{where}: if must use const or enum")

    def render_variants(
        self,
        properties: dict[str, Any],
        rules: list[Rule],
        name: str,
        where: str,
    ) -> list[str]:
        keys = sorted({rule.key for rule in rules})
        for key in keys:
            if key not in properties:
                raise GenerationError(
                    f"{self.schema_path}:{where}: discriminated property {key!r} is not declared"
                )

        domains: dict[str, list[str]] = {}
        for key in keys:
            spec = properties[key]
            if "enum" in spec:
                domains[key] = [literal(item) for item in spec["enum"]]
            else:
                values: set[str] = set()
                for rule in rules:
                    if rule.key == key:
                        values |= rule.triggers
                domains[key] = sorted(values)
            if not domains[key]:
                raise GenerationError(
                    f"{self.schema_path}:{where}: cannot derive a domain for {key!r}"
                )

        total = 1
        for key in keys:
            total *= len(domains[key])
        if total > MAX_BRANCHES:
            raise GenerationError(
                f"{self.schema_path}:{where}: conditional enumeration would produce "
                f"{total} branches, above the {MAX_BRANCHES} limit"
            )

        groups: dict[tuple[Any, ...], list[dict[str, str]]] = {}
        for combination in product_of_domains(keys, domains):
            assignment = dict(zip(keys, combination))
            signature = self.evaluate(assignment, rules, properties, where)
            if signature is None:
                continue
            groups.setdefault(signature, []).append(assignment)

        if not groups:
            raise GenerationError(
                f"{self.schema_path}:{where}: conditional constraints removed every branch"
            )

        variants: list[str] = []
        for signature in sorted(groups, key=lambda item: json.dumps(item, sort_keys=True)):
            assignments = groups[signature]
            merged = self.merge_group(keys, assignments)
            if merged is None:
                # The per-key value sets are not closed under the product, so a
                # merged branch would be wider than the protocol. Pin instead.
                for assignment in sorted(
                    assignments, key=lambda item: json.dumps(item, sort_keys=True)
                ):
                    variants.append(
                        self.render_variant(properties, dict(assignment), signature)
                    )
            else:
                variants.append(self.render_variant(properties, merged, signature))
        return variants

    def evaluate(
        self,
        assignment: dict[str, str],
        rules: list[Rule],
        properties: dict[str, Any],
        where: str,
    ) -> tuple[Any, ...] | None:
        extra_required: set[str] = set()
        narrowed: dict[str, tuple[str, ...]] = {}
        notes: set[str] = set()

        for rule in rules:
            if assignment[rule.key] not in rule.triggers:
                continue
            consequence = rule.then
            extra_required |= set(consequence.get("required", []))
            for prop, spec in consequence.get("properties", {}).items():
                if prop not in properties:
                    raise GenerationError(
                        f"{self.schema_path}:{where}: then constrains undeclared property {prop!r}"
                    )
                extra = sorted(
                    set(spec)
                    - {"const", "enum"}
                    - RUNTIME_ONLY_KEYWORDS
                    - METADATA_KEYWORDS
                )
                if extra:
                    raise GenerationError(
                        f"{self.schema_path}:{where}: unsupported then/properties keyword(s) "
                        f"{extra} for {prop!r}"
                    )
                allowed = None
                if "const" in spec:
                    allowed = (literal(spec["const"]),)
                elif "enum" in spec:
                    allowed = tuple(literal(item) for item in spec["enum"])
                if allowed is not None:
                    if prop in assignment:
                        if assignment[prop] not in allowed:
                            return None
                    else:
                        previous = narrowed.get(prop)
                        if previous is None:
                            narrowed[prop] = allowed
                        else:
                            intersection = tuple(sorted(set(previous) & set(allowed)))
                            if not intersection:
                                return None
                            narrowed[prop] = intersection
                for note in runtime_notes(spec):
                    notes.add(f"{prop}\u0000{note}")

        signature = (
            tuple(sorted(extra_required)),
            tuple(sorted((prop, values) for prop, values in narrowed.items())),
            tuple(sorted(notes)),
        )
        return signature

    def merge_group(
        self, keys: list[str], assignments: list[dict[str, str]]
    ) -> dict[str, tuple[str, ...]] | None:
        merged: dict[str, tuple[str, ...]] = {}
        for key in keys:
            merged[key] = tuple(sorted({item[key] for item in assignments}))
        size = 1
        for key in keys:
            size *= len(merged[key])
        if size != len(assignments):
            return None
        return merged

    def render_variant(
        self,
        properties: dict[str, Any],
        assignment: dict[str, tuple[str, ...]],
        signature: tuple[Any, ...],
    ) -> str:
        extra_required, narrowed, notes = signature
        per_property_notes: dict[str, list[str]] = {}
        for note in notes:
            prop, _, text = note.partition("\u0000")
            per_property_notes.setdefault(prop, []).append(text)

        indent = "      "
        lines: list[str] = []
        for prop, values in assignment.items():
            lines.extend(jsdoc(per_property_notes.pop(prop, []), indent))
            lines.append(f"{indent}{member_name(prop)}: {' | '.join(values)};")
        for prop in extra_required:
            lines.extend(jsdoc(per_property_notes.pop(prop, []), indent))
            lines.append(f"{indent}{member_name(prop)}: {self.property_type(properties, prop)};")
        for prop, values in narrowed:
            if prop in assignment:
                continue
            lines.extend(jsdoc(per_property_notes.pop(prop, []), indent))
            lines.append(f"{indent}{member_name(prop)}: {' | '.join(values)};")
        for prop in sorted(per_property_notes):
            lines.extend(jsdoc(per_property_notes[prop], indent))
            lines.append(f"{indent}{member_name(prop)}: {self.property_type(properties, prop)};")

        # A union member must always be an object type. Emitting a bare
        # `key: type;` member here would produce invalid TypeScript.
        if len(lines) == 1:
            return "{ " + lines[0].strip() + " }"
        return "{\n" + "\n".join(lines) + "\n    }"

    def property_type(self, properties: dict[str, Any], prop: str) -> str:
        spec = properties.get(prop)
        if spec is None:
            return "unknown"
        return self.render_node(
            spec, f"{self.root_name}{pascal_case(prop)}", f"$.{prop}"
        )

    # -- composition --------------------------------------------------------

    def compose(self) -> str:
        header = [
            "/**",
            " * GENERATED FILE — DO NOT EDIT.",
            f" * FNB Protocol: {self.tag}",
            f" * Source: {self.schema_path}",
            f" * Source SHA-256: {self.digest}",
            " * Regenerate with: python3 tools/generate-bindings.py",
            " */",
            "",
        ]
        return "\n".join(header + self.declarations) + "\n"


def product_of_domains(
    keys: list[str], domains: dict[str, list[str]]
) -> Iterator[tuple[str, ...]]:
    if not keys:
        yield ()
        return
    head, rest = keys[0], keys[1:]
    for value in domains[head]:
        for tail in product_of_domains(rest, domains):
            yield (value,) + tail


def verify_release(
    root: Path, manifest_path: Path
) -> tuple[dict[str, Any], list[tuple[str, str, dict[str, Any]]]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError(f"release manifest could not be read: {error}") from error

    for field in ("manifest_version", "release_tag", "algorithm", "schema_count", "schemas"):
        if field not in manifest:
            raise GenerationError(f"release manifest is missing {field!r}")
    if manifest["manifest_version"] != "1.0":
        raise GenerationError("unsupported manifest_version")
    if manifest["algorithm"] != "sha256":
        raise GenerationError("only sha256 manifests are supported")
    tag = manifest["release_tag"]
    if not isinstance(tag, str) or not tag:
        raise GenerationError("release_tag must be a non-empty string")
    if manifest["schema_count"] != len(manifest["schemas"]):
        raise GenerationError("schema_count does not match the schema list")

    prefix = f"https://raw.githubusercontent.com/{REPOSITORY}/{tag}/"
    loaded: list[tuple[str, str, dict[str, Any]]] = []
    for entry in manifest["schemas"]:
        path = entry["path"]
        try:
            payload = (root / path).read_bytes()
        except OSError as error:
            raise GenerationError(f"{path}: could not be read: {error}") from error
        if len(payload) != entry["bytes"]:
            raise GenerationError(f"{path}: byte length differs from the release manifest")
        digest = hashlib.sha256(payload).hexdigest()
        if digest != entry["sha256"]:
            raise GenerationError(f"{path}: sha256 differs from the release manifest")
        schema = json.loads(payload.decode("utf-8"))
        identifier = schema.get("$id")
        if not isinstance(identifier, str) or not identifier.startswith(prefix):
            raise GenerationError(f"{path}: $id is not pinned to the frozen {tag} namespace")
        loaded.append((path, digest, schema))
    return manifest, loaded


def render_all(root: Path, manifest_path: Path) -> dict[str, str]:
    manifest, schemas = verify_release(root, manifest_path)
    tag = manifest["release_tag"]
    directory = f"{OUTPUT_ROOT.as_posix()}/{tag}"

    rendered: dict[str, str] = {}
    modules = []
    for path, digest, schema in schemas:
        module = Path(path).name[: -len(".schema.json")]
        modules.append(module)
        rendered[f"{directory}/{module}.d.ts"] = BindingsFile(
            path, schema, tag, digest
        ).render()

    index = [
        "/**",
        " * GENERATED FILE — DO NOT EDIT.",
        f" * FNB Protocol: {tag}",
        f" * Source: the {len(schemas)} frozen schemas listed in {manifest_path.name}",
        " * Regenerate with: python3 tools/generate-bindings.py",
        " */",
        "",
    ]
    for module in sorted(modules):
        index.append(f'export * from "./{module}";')
    rendered[f"{directory}/index.d.ts"] = "\n".join(index) + "\n"
    return rendered


def run(root: Path, manifest_path: Path, check: bool) -> int:
    rendered = render_all(root, manifest_path)
    directory = next(iter(rendered)).rsplit("/", 1)[0]

    if check:
        stale: list[str] = []
        for relative, content in sorted(rendered.items()):
            target = root / relative
            if not target.exists():
                stale.append(f"missing:    {relative}")
            elif target.read_text(encoding="utf-8") != content:
                stale.append(f"stale:      {relative}")
        expected = {relative.rsplit("/", 1)[1] for relative in rendered}
        actual = root / directory
        if actual.is_dir():
            for candidate in sorted(actual.glob("*.d.ts")):
                if candidate.name not in expected:
                    stale.append(f"unexpected: {directory}/{candidate.name}")
        if stale:
            print("generated bindings are not current:", file=sys.stderr)
            for item in stale:
                print(f"  {item}", file=sys.stderr)
            print("\nRun: python3 tools/generate-bindings.py", file=sys.stderr)
            return 1
        print(f"bindings current: {len(rendered)} generated files under {directory}")
        return 0

    written = 0
    for relative, content in sorted(rendered.items()):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = target.read_text(encoding="utf-8") if target.exists() else None
        if previous != content:
            target.write_text(content, encoding="utf-8")
            print(f"wrote {relative}")
            written += 1
    print(f"generated {len(rendered)} files under {directory} ({written} changed)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate-bindings",
        description=(
            "Generate FNB protocol TypeScript bindings from the frozen release "
            "manifest. Fails closed on unsupported JSON Schema semantics."
        ),
    )
    parser.add_argument("--root", default=".", help="repository checkout root")
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="release schema digest manifest relative to --root",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-render in memory and fail if the committed bindings differ",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        return run(root, manifest_path, args.check)
    except GenerationError as error:
        print(f"generate-bindings: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
