# SPDX-License-Identifier: Apache-2.0
"""Test-only process for the unchanged established Mock; synthetic inputs only."""
import argparse
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("sdk_test_mock", ROOT / "tools/object-exchange-mock.py")
mock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)
parser = argparse.ArgumentParser()
parser.add_argument("--mode", default="normal")
args = parser.parse_args()
with tempfile.TemporaryDirectory() as temporary:
    root = ROOT
    if args.mode in ("missing-schema", "corrupt-schema", "corrupt-manifest"):
        root = Path(temporary)
        for name in ("specs", "tools"):
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        schema = root / "specs/v0.1/actor.schema.json"
        if args.mode == "missing-schema":
            schema.unlink()
        elif args.mode == "corrupt-schema":
            schema.write_text("{}", encoding="utf-8")
        else:
            (root / "specs/openapi/object-exchange/v1/artifact-digests.json").write_text("{}", encoding="utf-8")
    with mock.MockServer(root=root, max_bytes=100 if args.mode == "bytes" else 1048576,
                         max_objects=1 if args.mode == "objects" else 256) as server:
        if args.mode == "internal":
            def broken(*args, **kwargs):
                raise RuntimeError("test-only unavailable judge")
            server.evaluator.probe.judge = broken
        print(json.dumps({"port": server.server_port}), flush=True)
        server.serve_forever()
