#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent entry point for FNB public protocol conformance checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


RUNNER_NAME = "fnb-conformance"
RUNNER_VERSION = "0.1.0-preview.1"
DEFAULT_MANIFEST = Path(
    "specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json"
)
REPORT_SCHEMA = Path("tests/conformance/compatibility-report.schema.json")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check(check_id: str, passed: bool, summary: str) -> dict[str, str]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "summary": summary,
    }


def verify_manifest(root: Path, manifest_path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, check("manifest", False, f"manifest could not be read: {exc}")

    required = {
        "manifest_version",
        "protocol_release",
        "protocol_status",
        "algorithm",
        "schema_root",
        "schema_count",
        "schemas",
    }
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        return manifest if isinstance(manifest, dict) else {}, check(
            "manifest", False, "manifest is missing required release metadata"
        )
    if manifest["manifest_version"] != "1.0":
        return manifest, check("manifest", False, "unsupported manifest_version")
    if manifest["algorithm"] != "sha256":
        return manifest, check("manifest", False, "only sha256 manifests are supported")
    if manifest["protocol_status"] != "preview":
        return manifest, check("manifest", False, "protocol_status must be preview")
    if not isinstance(manifest["protocol_release"], str) or not manifest["protocol_release"]:
        return manifest, check("manifest", False, "protocol_release must be non-empty")
    if not isinstance(manifest["schema_root"], str) or not manifest["schema_root"]:
        return manifest, check("manifest", False, "schema_root must be non-empty")
    if not isinstance(manifest["schemas"], list) or not manifest["schemas"]:
        return manifest, check("manifest", False, "schemas must be a non-empty array")
    if (
        not isinstance(manifest["schema_count"], int)
        or isinstance(manifest["schema_count"], bool)
        or manifest["schema_count"] != len(manifest["schemas"])
    ):
        return manifest, check("manifest", False, "schema_count does not match schemas")

    seen: set[str] = set()
    for entry in manifest["schemas"]:
        if not isinstance(entry, dict):
            return manifest, check("manifest", False, "schema entries must be objects")
        if set(entry) != {"path", "bytes", "sha256"}:
            return manifest, check(
                "manifest", False, "each schema entry must contain path, bytes, and sha256"
            )
        path = entry["path"]
        size = entry["bytes"]
        digest = entry["sha256"]
        if not isinstance(path, str) or not path:
            return manifest, check("manifest", False, "schema path must be non-empty")
        if path in seen:
            return manifest, check("manifest", False, f"duplicate schema path: {path}")
        seen.add(path)
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            return manifest, check("manifest", False, f"invalid byte count for {path}")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            return manifest, check("manifest", False, f"invalid sha256 for {path}")

    return manifest, check(
        "manifest",
        True,
        f"release manifest declares {manifest['schema_count']} protocol schemas",
    )


def verify_schema_digests(
    root: Path, manifest: dict[str, Any]
) -> dict[str, str]:
    if not manifest or "schemas" not in manifest or "schema_root" not in manifest:
        return check("schema-digests", False, "manifest metadata is not valid")

    schema_root = root / manifest["schema_root"]
    try:
        actual_paths = {
            path.relative_to(root).as_posix()
            for path in schema_root.glob("*.schema.json")
            if path.is_file()
        }
    except (OSError, ValueError) as exc:
        return check("schema-digests", False, f"schema set could not be scanned: {exc}")

    declared_paths = {entry["path"] for entry in manifest["schemas"]}
    if actual_paths != declared_paths:
        missing = sorted(declared_paths - actual_paths)
        extra = sorted(actual_paths - declared_paths)
        parts = []
        if missing:
            parts.append("missing: " + ", ".join(missing))
        if extra:
            parts.append("undeclared: " + ", ".join(extra))
        return check(
            "schema-digests",
            False,
            "schema set differs from manifest" + (": " + "; ".join(parts) if parts else ""),
        )

    root_resolved = root.resolve()
    for entry in manifest["schemas"]:
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root_resolved):
            return check("schema-digests", False, f"path escapes repository root: {entry['path']}")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            return check("schema-digests", False, f"could not read {entry['path']}: {exc}")
        if len(payload) != entry["bytes"]:
            return check(
                "schema-digests",
                False,
                f"byte length mismatch for {entry['path']}",
            )
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            return check(
                "schema-digests",
                False,
                f"sha256 mismatch for {entry['path']}",
            )

    return check(
        "schema-digests",
        True,
        f"all {len(declared_paths)} schema digests match the release manifest",
    )


def run_public_conformance(root: Path) -> dict[str, str]:
    validator = root / "tools/validate-public-artifacts.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(validator)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return check("public-conformance", False, f"validator could not run: {exc}")

    output = (completed.stdout + "\n" + completed.stderr).strip()
    summary = output.splitlines()[-1] if output else "validator returned no output"
    if completed.returncode != 0:
        return check("public-conformance", False, summary)
    return check("public-conformance", True, summary)


def validate_report(root: Path, report: dict[str, Any]) -> None:
    schema = load_json(root / REPORT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(report),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        where = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise AssertionError(f"compatibility report is invalid at {where}: {first.message}")


def render_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(
        f"{report['protocol_release']}: {report['status']} "
        f"({report['runner']['name']} {report['runner']['version']})"
    )
    for item in report["checks"]:
        print(f"- {item['status'].upper()}: {item['id']} — {item['summary']}")


def verify_release(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path

    manifest, manifest_check = verify_manifest(root, manifest_path)
    checks = [manifest_check]
    digest_check = verify_schema_digests(root, manifest)
    checks.append(digest_check)

    if digest_check["status"] == "pass":
        checks.append(run_public_conformance(root))
    else:
        checks.append(
            {
                "id": "public-conformance",
                "status": "skip",
                "summary": "not run because release integrity verification failed",
            }
        )

    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    try:
        display_manifest = manifest_path.relative_to(root).as_posix()
    except ValueError:
        display_manifest = str(manifest_path)

    report = {
        "format_version": "1.0",
        "protocol_release": manifest.get("protocol_release", "unknown"),
        "runner": {
            "name": RUNNER_NAME,
            "version": RUNNER_VERSION,
        },
        "subject": {
            "kind": "release_bundle",
            "manifest": display_manifest,
        },
        "status": status,
        "checks": checks,
    }

    try:
        validate_report(root, report)
    except (OSError, json.JSONDecodeError, AssertionError) as exc:
        print(f"conformance runner error: {exc}", file=sys.stderr)
        return 1

    if args.report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = Path.cwd() / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    render_report(report, args.json)
    return 0 if status == "pass" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=RUNNER_NAME,
        description=(
            "Verify FNB public protocol release integrity and run the public "
            "conformance suite. This tool does not connect to an FNB product service."
        ),
    )
    parser.add_argument("--version", action="version", version=RUNNER_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser(
        "verify-release",
        help="verify the schema digest manifest and public conformance fixtures",
    )
    verify.add_argument("--root", default=".", help="repository checkout root")
    verify.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="release schema digest manifest relative to --root",
    )
    verify.add_argument(
        "--json",
        action="store_true",
        help="print the compatibility report as JSON",
    )
    verify.add_argument(
        "--report",
        help="write the compatibility report JSON to this path",
    )
    verify.set_defaults(func=verify_release)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
