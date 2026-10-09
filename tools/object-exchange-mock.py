#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Loopback-only, non-persistent HTTP wrapper for the frozen contract probe."""

from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import json
import math
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBLEM_PREFIX = "https://www.fnbapp.net/problems/object-exchange/1.0/"


def unavailable():
    # Also usable if the frozen validator's dependencies cannot be imported.
    return 500, "application/problem+json", {
        "type": PROBLEM_PREFIX + "evaluation-failure",
        "title": "Exchange evaluation unavailable", "status": 500,
    }


class FrozenEvaluator:
    """Use the unchanged published evaluator, never a second domain judge."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.contract = None
        self.probe = None
        try:
            spec = importlib.util.spec_from_file_location(
                "mock_frozen_contract", self.root / "tools/object-exchange-contract.py")
            contract = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(contract)
            contract.verify_boundary(self.root)
            self.probe = contract.ContractProbe(self.root)
            self.contract = contract
        except Exception:
            # No exception details, paths, or request data leave this boundary.
            pass

    def problem(self, suffix):
        return self.contract.problem(suffix) if self.contract else unavailable()

    def evaluate(self, raw, **kwargs):
        try:
            if self.contract is None or self.probe is None:
                return unavailable()
            self.contract.verify_boundary(self.root)
            result = self.probe.evaluate(raw, **kwargs)
            if result[0] == 200:
                self.probe.check_receipt(self.contract.strict_json(raw), result)
            return result
        except Exception:
            return unavailable()


class MockServer(HTTPServer):
    # Serial processing and close-after-response are deliberate local limits,
    # not production throughput/session guarantees.
    allow_reuse_address = True

    def __init__(self, address=("127.0.0.1", 0), *, root=ROOT,
                 max_bytes=1048576, max_objects=256, request_timeout=5):
        host, port = address
        if not ipaddress.ip_address(host).is_loopback:
            raise ValueError("mock must bind a numeric loopback address")
        if ipaddress.ip_address(host).version != 4:
            raise ValueError("this mock supports IPv4 loopback only")
        if (max_bytes < 1 or max_objects < 1 or request_timeout <= 0
                or not math.isfinite(request_timeout)):
            raise ValueError("mock limits must be positive")
        self.evaluator = FrozenEvaluator(root)
        self.max_bytes = max_bytes
        self.max_objects = max_objects
        self.request_timeout = request_timeout
        super().__init__((host, port), ExchangeHandler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(self.request_timeout)
        return connection, address


class ExchangeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "FNB-Local-Mock"
    sys_version = ""

    def log_message(self, *args):
        # Never log supplied URLs, headers, bodies, or identifiers.
        pass

    def respond(self, result):
        status, media, body = result
        encoded = json.dumps(body, ensure_ascii=True, allow_nan=False).encode("utf-8")
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(encoded)
        except (OSError, TimeoutError):
            pass  # A disconnected client cannot be given a second response.

    def send_error(self, code, message=None, explain=None):
        # HTTP framing/routing failures are local adapter behavior, not receipts.
        self.respond((code, "application/json", {"error": "HTTP request not supported"}))

    def do_POST(self):
        if self.path != "/exchange":
            self.send_error(404)
            return
        evaluator = self.server.evaluator
        lengths = self.headers.get_all("Content-Length", [])
        if (self.headers.get_all("Transfer-Encoding") or len(lengths) != 1
                or not re.fullmatch(r"[0-9]+", lengths[0]) or len(lengths[0]) > 20):
            self.respond(evaluator.problem("malformed-envelope"))
            return
        length = int(lengths[0])
        if length > self.server.max_bytes:
            self.respond(evaluator.problem("payload-too-large"))
            return
        types = self.headers.get_all("Content-Type", [])
        encodings = self.headers.get_all("Content-Encoding", [])
        if len(types) != 1 or len(encodings) > 1:
            self.respond(evaluator.problem("unsupported-media-type"))
            return
        # Reuse the frozen probe's representation stage before blocking on a
        # body. Empty input intentionally cannot advance beyond JSON parsing.
        representation = evaluator.evaluate(
            b"", content_type=types[0],
            content_encoding=encodings[0] if encodings else None)
        if representation[0] in (415, 500):
            self.respond(representation)
            return
        try:
            raw = self.rfile.read(length)
        except TimeoutError:
            self.respond(evaluator.problem("evaluation-failure"))
            return
        except OSError:
            self.respond(evaluator.problem("malformed-envelope"))
            return
        if len(raw) != length:
            self.respond(evaluator.problem("malformed-envelope"))
            return
        self.respond(evaluator.evaluate(
            raw, content_type=types[0],
            content_encoding=encodings[0] if encodings else None,
            max_bytes=self.server.max_bytes, max_objects=self.server.max_objects))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="numeric IPv4 loopback only")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-bytes", type=int, default=1048576)
    parser.add_argument("--max-objects", type=int, default=256)
    parser.add_argument("--request-timeout", type=float, default=5)
    args = parser.parse_args()
    try:
        with MockServer((args.host, args.port), max_bytes=args.max_bytes,
                        max_objects=args.max_objects, request_timeout=args.request_timeout) as server:
            print(f"Local non-persistent mock: http://{args.host}:{server.server_port}/exchange",
                  file=sys.stderr, flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError):
        parser.exit(2, "Cannot start local mock; check loopback address, port and limits.\n")


if __name__ == "__main__":
    main()
