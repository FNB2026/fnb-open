#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Deliberately incorrect adapter for the FNB implementation adapter contract v1.0.

It satisfies the handshake perfectly and then accepts everything. It exists for
one reason: to prove that the conformance runner actually detects an
implementation whose verdicts are wrong, rather than rubber-stamping any process
that speaks the contract.

CI runs the runner against this adapter and requires a non-zero exit. If that
ever starts passing, the runner has stopped testing anything.
"""

from __future__ import annotations

import json
import sys

CONTRACT_VERSION = "1.0"


def main() -> int:
    request = json.loads(sys.stdin.read())
    request_id = request.get("request_id", "")
    operation = request.get("operation")

    if operation == "describe":
        response = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "status": "ok",
            "implementation": {"name": "faulty-always-accept-adapter", "version": "0.1.0"},
            "supported_protocol_releases": [request.get("protocol_release")],
        }
    elif operation == "validate":
        response = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "status": "ok",
            "accepted": True,
        }
    else:
        print(f"adapter: unsupported operation {operation!r}", file=sys.stderr)
        return 2

    sys.stdout.write(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
