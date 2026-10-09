# SPDX-License-Identifier: Apache-2.0
"""Real loopback HTTP tests; synthetic material only, no certification claim."""

import copy
import builtins
from contextlib import closing
import http.client
import importlib.util
import json
import io
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from test_object_exchange import ROOT, PREFIX, envelope, world

spec = importlib.util.spec_from_file_location("exchange_mock", ROOT / "tools/object-exchange-mock.py")
mock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)


class MockHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = mock.MockServer(request_timeout=0.25)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.request = envelope(world("basic-memory"))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.assertFalse(self.thread.is_alive())

    def connection(self):
        return closing(http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3))

    def send(self, raw=None, headers=None, path="/exchange", method="POST"):
        if raw is None:
            raw = json.dumps(self.request, ensure_ascii=False).encode("utf-8")
        with self.connection() as conn:
            conn.request(method, path, raw, headers or {"Content-Type": "application/json"})
            response = conn.getresponse()
            data = response.read()
            self.assertEqual(int(response.getheader("Content-Length")), len(data))
            self.assertEqual(response.getheader("Connection"), "close")
            return response.status, response.getheader("Content-Type"), json.loads(data.decode("utf-8"))

    def receipt(self, result, status, request=None):
        request = self.request if request is None else request
        self.assertEqual(result, (200, "application/json", {
            "transport_version": request["transport_version"],
            "protocol_release": request["protocol_release"],
            "exchange_id": request["exchange_id"], "status": status}))
        self.server.evaluator.probe.check_receipt(request, result)

    def problem(self, result, suffix):
        self.assertEqual(result, self.server.evaluator.contract.problem(suffix))

    def test_all_public_worlds_and_exact_unicode_correlation(self):
        for name in ("basic-memory", "relationship-correction", "source-redaction", "permission-withdrawal"):
            with self.subTest(name=name):
                self.request = envelope(world(name))
                self.request["exchange_id"] = "  HTTP ☕ / 合成  "
                self.receipt(self.send(), "accepted")

    def test_invalid_object_is_200_rejected(self):
        self.request["objects"][0]["object"] = {}
        self.receipt(self.send(), "rejected")

    def test_unknown_schema_is_200_without_url_retrieval(self):
        self.request["objects"][0]["schema"] = "https://sender.invalid/malicious-schema"
        self.receipt(self.send(), "rejected")

    def test_invalid_time_is_protocol_rejection(self):
        flow = next(item for item in self.request["objects"] if item["schema"] == PREFIX + "flow-event.schema.json")
        self.request["objects"] = [flow]
        self.request["validation_contexts"] = []
        for value in ("not-time", "2026-02-30T12:00:00Z", "2026-01-01T12:00:00"):
            with self.subTest(value=value):
                flow["object"]["occurred_at"] = value
                self.receipt(self.send(), "rejected")

    def test_explicit_context_missing_role_and_duplicate_identity(self):
        baseline = copy.deepcopy(self.request)
        self.request["validation_contexts"][0]["roles"]["node"] = "missing-synthetic-node"
        self.receipt(self.send(), "rejected")
        self.request = baseline
        self.request["objects"].append(copy.deepcopy(self.request["objects"][0]))
        self.receipt(self.send(), "rejected")

    def test_strict_utf8_json_and_duplicates_at_any_depth(self):
        for raw in (b'{"x":1,"x":2}', b'{"objects":[{"object":{"x":1,"x":2}}]}',
                    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}',
                    b'{"x":"\xff"}', b'\xff\xfe{\x00}\x00', b'{}{}', b'[]'):
            with self.subTest(raw=raw):
                self.problem(self.send(raw), "malformed-envelope")

    def test_envelope_unknown_member_and_versions(self):
        for key, value, suffix in (("extra", True, "malformed-envelope"),
                                    ("transport_version", "9.0", "unsupported-transport-version"),
                                    ("protocol_release", "v9.0", "unsupported-protocol-release")):
            request = {**self.request, key: value}
            self.problem(self.send(json.dumps(request).encode()), suffix)

    def test_representation_precedes_json_and_versions(self):
        for media in ("text/plain", "application/json; charset=latin1", "application/json; profile=x"):
            with self.subTest(media=media):
                self.problem(self.send(b'invalid', {"Content-Type": media}), "unsupported-media-type")
        self.problem(self.send(headers={"Content-Type": "application/json", "Content-Encoding": "gzip"}),
                     "unsupported-media-type")
        self.problem(self.send(headers={"X-Synthetic": "no content type"}), "unsupported-media-type")
        self.request["transport_version"] = "9.0"
        self.request["protocol_release"] = "v9.0"
        self.problem(self.send(), "unsupported-transport-version")

    def test_supported_media_and_identity_encoding(self):
        self.receipt(self.send(headers={"Content-Type": "Application/JSON; Charset=UTF-8",
                                       "Content-Encoding": "identity"}), "accepted")

    def test_byte_and_object_capacity(self):
        self.server.max_bytes = 3
        self.problem(self.send(b'xxxx', {"Content-Type": "text/plain"}), "payload-too-large")
        self.server.max_bytes = 1048576
        self.server.max_objects = 1
        self.problem(self.send(), "payload-too-large")

    def test_internal_validator_and_format_failures_are_500(self):
        probe = self.server.evaluator.probe
        with patch.object(probe, "judge", side_effect=RuntimeError("DO NOT LEAK")):
            self.problem(self.send(), "evaluation-failure")
        with patch.object(probe, "judge", side_effect=TimeoutError):
            self.problem(self.send(), "evaluation-failure")
        with patch.object(probe, "evaluate", return_value=(200, "application/json", {})):
            self.problem(self.send(), "evaluation-failure")
        capabilities = dict(self.server.evaluator.contract.PUBLIC.FORMAT_CHECKER.checkers)
        capabilities.pop("date-time")
        with patch.object(self.server.evaluator.contract.PUBLIC.FORMAT_CHECKER, "checkers", capabilities):
            self.problem(self.send(), "evaluation-failure")

    def test_missing_schema_and_corrupt_manifests_fail_closed(self):
        contract = self.server.evaluator.contract
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = list(contract.BOUNDARY_PATHS) + [contract.MANIFEST]
            files += [item["path"] for item in contract.read(ROOT / contract.PUBLIC_MANIFEST)["schemas"]]
            for name in files:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            self.server.evaluator = mock.FrozenEvaluator(root)
            self.receipt(self.send(), "accepted")
            schema = root / files[-1]
            schema.unlink()
            self.problem(self.send(), "evaluation-failure")
            shutil.copyfile(ROOT / files[-1], schema)
            schema.write_bytes(b'{}')
            self.problem(self.send(), "evaluation-failure")
            shutil.copyfile(ROOT / files[-1], schema)
            for name in (contract.MANIFEST, contract.PUBLIC_MANIFEST):
                target = root / name
                target.write_bytes(b'{}')
                self.problem(self.send(), "evaluation-failure")
                shutil.copyfile(ROOT / name, target)
            # Loss at startup also leaves no usable evaluator, not a verdict.
            (root / contract.ARTIFACT).unlink()
            self.server.evaluator = mock.FrozenEvaluator(root)
            self.assertEqual(self.send(), mock.unavailable())

    def test_unavailable_import_fails_closed(self):
        with patch.object(mock.importlib.util, "spec_from_file_location", side_effect=ImportError):
            self.server.evaluator = mock.FrozenEvaluator(ROOT)
        self.assertEqual(self.send(), mock.unavailable())

    def test_cli_without_validation_dependencies_returns_500_over_http(self):
        # -S removes site-packages: prove real dependency loss, not just a mock.
        process = subprocess.Popen(
            [sys.executable, "-S", str(ROOT / "tools/object-exchange-mock.py"), "--port", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            self.assertTrue(select.select([process.stderr], [], [], 5)[0], "CLI startup timeout")
            announcement = process.stderr.readline()
            self.assertIn("http://127.0.0.1:", announcement)
            port = int(announcement.split("127.0.0.1:")[1].split("/")[0])
            with closing(http.client.HTTPConnection("127.0.0.1", port, timeout=3)) as conn:
                conn.request("POST", "/exchange", json.dumps(self.request).encode(),
                             {"Content-Type": "application/json"})
                response = conn.getresponse()
                self.assertEqual((response.status, response.getheader("Content-Type"),
                                  json.loads(response.read())), mock.unavailable())
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            process.stderr.close()

    def test_repeated_http_header_and_framing_rejection(self):
        cases = [([("Content-Length", "2"), ("Content-Length", "2")], "malformed-envelope"),
                 ([("Transfer-Encoding", "chunked")], "malformed-envelope"),
                 ([("Content-Length", "-1")], "malformed-envelope"),
                 ([], "malformed-envelope"),
                 ([("Content-Length", "2"), ("Content-Type", "application/json")], "unsupported-media-type"),
                 ([("Content-Length", "2"), ("Content-Encoding", "identity"),
                   ("Content-Encoding", "identity")], "unsupported-media-type")]
        for headers, suffix in cases:
            with self.subTest(headers=headers), self.connection() as conn:
                conn.putrequest("POST", "/exchange")
                conn.putheader("Content-Type", "application/json")
                for name, value in headers:
                    conn.putheader(name, value)
                conn.endheaders(b'{}')
                response = conn.getresponse()
                self.problem((response.status, response.getheader("Content-Type"),
                              json.loads(response.read())), suffix)

    def test_no_outbound_network_or_request_storage(self):
        original_open = builtins.open
        original_io_open = io.open

        def read_only_open(file, mode="r", *args, **kwargs):
            if any(flag in mode for flag in "wax+"):
                raise AssertionError("storage")
            return original_open(file, mode, *args, **kwargs)

        def read_only_io_open(file, mode="r", *args, **kwargs):
            if any(flag in mode for flag in "wax+"):
                raise AssertionError("storage")
            return original_io_open(file, mode, *args, **kwargs)

        with self.connection() as conn:
            conn.connect()  # Only the test client establishes a loopback connection.
            with patch.object(socket, "create_connection", side_effect=AssertionError("outbound")), \
                 patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS")), \
                 patch.object(socket.socket, "connect", side_effect=AssertionError("outbound")), \
                 patch.object(builtins, "open", side_effect=read_only_open), \
                 patch.object(io, "open", side_effect=read_only_io_open), \
                 patch.object(Path, "write_bytes", side_effect=AssertionError("storage")), \
                 patch.object(Path, "write_text", side_effect=AssertionError("storage")):
                conn.request("POST", "/exchange", json.dumps(self.request).encode(),
                             {"Content-Type": "application/json"})
                response = conn.getresponse()
                self.receipt((response.status, response.getheader("Content-Type"),
                              json.loads(response.read())), "accepted")

    def test_incomplete_body_timeout_and_media_precedence(self):
        with self.connection() as conn:
            conn.putrequest("POST", "/exchange")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "20")
            conn.endheaders(b'{}')
            response = conn.getresponse()
            self.problem((response.status, response.getheader("Content-Type"),
                          json.loads(response.read())), "evaluation-failure")
        with self.connection() as conn:
            conn.putrequest("POST", "/exchange")
            conn.putheader("Content-Type", "text/plain")
            conn.putheader("Content-Length", "20")
            conn.endheaders()
            response = conn.getresponse()
            self.problem((response.status, response.getheader("Content-Type"),
                          json.loads(response.read())), "unsupported-media-type")

    def test_short_body_and_duplicate_member_beside_valid_envelope(self):
        raw = json.dumps(self.request).encode()
        raw = raw[:-1] + b',"exchange_id":"second"}'
        self.problem(self.send(raw), "malformed-envelope")
        with self.connection() as conn:
            conn.putrequest("POST", "/exchange")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", "20")
            conn.endheaders(b'{}')
            conn.sock.shutdown(socket.SHUT_WR)
            response = conn.getresponse()
            self.problem((response.status, response.getheader("Content-Type"),
                          json.loads(response.read())), "malformed-envelope")

    def test_only_exchange_post_and_loopback_bind(self):
        self.assertEqual(self.send(path="/other")[0], 404)
        self.assertEqual(self.send(path="/exchange?x=1")[0], 404)
        self.assertEqual(self.send(method="GET")[0], 501)
        for host in ("0.0.0.0", "192.0.2.1", "localhost"):
            with self.assertRaises(ValueError):
                mock.MockServer((host, 0))


if __name__ == "__main__":
    unittest.main()
