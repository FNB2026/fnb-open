#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate a generated SPDX 2.3 release SBOM against the vendored official schema.

The schema is vendored byte-for-byte from the SPDX specification (CC0-1.0) so that
validation is offline and deterministic: no remote schema is fetched at build or
test time. Only structural conformance is asserted here; archive/byte agreement is
checked separately by the Node release tooling.
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA = Path(__file__).resolve().parent / "schemas/spdx-2.3.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sbom", type=Path, help="SPDX JSON document to validate")
    parser.add_argument("--schema", type=Path, default=SCHEMA)
    args = parser.parse_args()
    document = json.loads(args.sbom.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    for error in errors:
        location = "/".join(str(part) for part in error.path) or "<root>"
        print(f"INVALID {location}: {error.message}")
    if errors:
        print(f"SPDX schema validation failed with {len(errors)} error(s)")
        return 1
    print(f"SPDX 2.3 schema validation passed: {args.sbom.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
