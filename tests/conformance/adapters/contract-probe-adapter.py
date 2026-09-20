#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Contract test double for the FNB implementation adapter contract v1.0.

This file exists so the runner can be exercised end to end, and so an adapter
author has a worked example of the wire shape. It is **not** an FNB
implementation, and it is **not** the conformance authority: it answers by
calling the repository's own validator, which remains the single source of
protocol semantics.

A real third-party adapter would implement validation itself, in its own
language, from the frozen schemas.

Requires the pinned validation dependency:

    python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

CONTRACT_VERSION = "1.0"
IMPLEMENTATION = {"name": "fnb-conformance-contract-probe", "version": "0.1.0"}

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_validator():
    path = REPO_ROOT / "tools" / "validate-public-artifacts.py"
    spec = importlib.util.spec_from_file_location("fnb_validate_public_artifacts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError as error:
        print(f"adapter: request is not JSON: {error}", file=sys.stderr)
        return 2

    request_id = request.get("request_id", "")
    operation = request.get("operation")
    release = request.get("protocol_release")

    if operation == "describe":
        response = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "status": "ok",
            "implementation": IMPLEMENTATION,
            "supported_protocol_releases": [release],
        }
    elif operation == "validate":
        try:
            validator = load_validator()
            schemas = validator.load_schemas()
        except Exception as error:  # noqa: BLE001 - surfaced as an adapter failure
            print(f"adapter: cannot load protocol schemas: {error}", file=sys.stderr)
            return 3
        case = request["case"]
        kind = case["kind"]
        instance = case["instance"]
        try:
            if kind == "object":
                validator.validate_instance(schemas, case["schema"], instance, "case")
                validator.validate_object_semantics(case["schema"], instance, "case")
            elif kind == "protocol_chain":
                validator.validate_protocol_chain_instance(schemas, instance, "case")
            elif kind == "invalidation_chain":
                validator.validate_invalidation_chain_instance(schemas, instance, "case")
            elif kind == "source_state_chain":
                validator.validate_source_state_chain_instance(schemas, instance, "case")
            else:
                print(f"adapter: unsupported case kind {kind!r}", file=sys.stderr)
                return 4
        except (AssertionError, KeyError, TypeError, ValueError):
            accepted = False
        else:
            accepted = True
        response = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "status": "ok",
            "accepted": accepted,
        }
    else:
        print(f"adapter: unsupported operation {operation!r}", file=sys.stderr)
        return 5

    sys.stdout.write(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
