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
# The runner is versioned independently of the protocol release it verifies: a
# tooling change must not be reported as a protocol change, and vice versa. The
# release under test is carried separately, as protocol_release in the report.
RUNNER_VERSION = "0.2.0"
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


def runner_error(message: str) -> int:
    """Report a runner-side failure and return an exit code.

    This is deliberately distinct from an adapter failure: no report is written,
    because nothing was established about the implementation under test. A
    mis-specified release, a failed identity check, or an unsound official judge
    are all runner errors.
    """
    print(f"conformance runner error: {message}", file=sys.stderr)
    return 1


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


# --- implementation conformance (adapter contract 1.0) ---------------------

CONTRACT_VERSION = "1.0"
ADAPTER_TIMEOUT_SECONDS = 10
# The implementation conformance case suite is written against exactly one
# protocol release. A newer release must ship its own case suite, and an older
# suite must never stand in for it, so a mismatch is a runner error rather than a
# verdict about the adapter.
IMPLEMENTATION_CASE_RELEASE = "v0.1.0-preview.1"
ADAPTER_VALIDATE_KEYS = {"contract_version", "request_id", "status", "accepted"}
ADAPTER_DESCRIBE_KEYS = {
    "contract_version",
    "request_id",
    "status",
    "implementation",
    "supported_protocol_releases",
}
WORLD_DIR = Path("tests/fixtures/generated")

# (directory, case kind, expected verdict, check bucket)
CASE_SOURCES = (
    ("tests/conformance/v0.1/valid", "object", True, "valid-objects"),
    ("tests/conformance/v0.1/invalid", "object", False, "invalid-objects"),
    ("tests/conformance/v0.1/invalid-semantics", "object", False, "semantic-negatives"),
    ("tests/conformance/v0.1/invalid-chains", "protocol_chain", False, "cross-object-chains"),
    (
        "tests/conformance/v0.1/valid-invalidation-chains",
        "invalidation_chain",
        True,
        "cross-object-chains",
    ),
    (
        "tests/conformance/v0.1/invalid-invalidation-chains",
        "invalidation_chain",
        False,
        "cross-object-chains",
    ),
    (
        "tests/conformance/v0.1/valid-source-state-chains",
        "source_state_chain",
        True,
        "cross-object-chains",
    ),
    (
        "tests/conformance/v0.1/invalid-source-state-chains",
        "source_state_chain",
        False,
        "cross-object-chains",
    ),
)
CHECK_ORDER = (
    "adapter-contract",
    "valid-objects",
    "invalid-objects",
    "semantic-negatives",
    "cross-object-chains",
)


def collect_cases(root: Path) -> list[dict[str, Any]]:
    """Build cases from the existing public test assets.

    Expected outcomes stay on this side: they are never put in the request, so an
    adapter cannot echo an answer it was handed.
    """
    cases: list[dict[str, Any]] = []
    for relative, kind, expected, bucket in CASE_SOURCES:
        for path in sorted((root / relative).glob("*.json")):
            payload = load_json(path)
            if kind == "object":
                case = {
                    "kind": "object",
                    "schema": payload["schema"],
                    "instance": payload["instance"],
                }
            else:
                case = {"kind": kind, "instance": payload}
            cases.append(
                {
                    "id": path.relative_to(root).as_posix(),
                    "case": case,
                    "expected": expected,
                    "bucket": bucket,
                }
            )

    example = root / "examples" / "synthetic-protocol-chain.json"
    if not example.is_file():
        raise AssertionError("examples/synthetic-protocol-chain.json is required as a case source")
    cases.append(
        {
            "id": "examples/synthetic-protocol-chain.json",
            "case": {"kind": "protocol_chain", "instance": load_json(example)},
            "expected": True,
            "bucket": "cross-object-chains",
        }
    )

    for path in sorted((root / WORLD_DIR).glob("*.json")):
        world = load_json(path)
        objects = world["objects"]
        for index, descriptor in enumerate(world["validation"]):
            kind = descriptor["kind"]
            if kind == "invalidation_chain":
                instance: dict[str, Any] = {
                    "records": [objects[name] for name in descriptor["records"]]
                }
            else:
                instance = {role: objects[name] for role, name in descriptor["members"].items()}
            cases.append(
                {
                    "id": f"{path.relative_to(root).as_posix()}#{kind}[{index}]",
                    "case": {"kind": kind, "instance": instance},
                    "expected": True,
                    "bucket": "cross-object-chains",
                }
            )

    # An opaque request id derived from the case origin. A source path would hand
    # the expected verdict to the adapter, since the fixture directories are
    # named valid/ and invalid/. Lowercase hex cannot contain those words, so the
    # check below is a structural guarantee rather than a convention.
    for item in cases:
        digest = hashlib.sha256(item["id"].encode("utf-8")).hexdigest()[:16]
        item["request_id"] = f"case-{digest}"
        token = item["request_id"][len("case-") :]
        if len(token) != 16 or any(ch not in "0123456789abcdef" for ch in token):
            raise AssertionError(f"case request id must be opaque: {item['request_id']!r}")
    return cases


def invoke_adapter(
    adapter: Path, request: dict[str, Any], expected_keys: set[str]
) -> tuple[dict[str, Any] | None, str | None]:
    """Run the adapter once and return (response, error).

    Every deviation from the contract is an adapter failure, never a verdict.
    """
    try:
        completed = subprocess.run(
            [str(adapter)],
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=ADAPTER_TIMEOUT_SECONDS,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return None, f"adapter exceeded the {ADAPTER_TIMEOUT_SECONDS}s timeout"
    except UnicodeDecodeError:
        return None, "stdout was not valid UTF-8"
    except OSError as error:
        return None, f"adapter could not be started: {error}"

    if completed.returncode != 0:
        return None, f"adapter exited with code {completed.returncode}"
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return None, f"stdout must be exactly one JSON object: {error}"
    if not isinstance(response, dict):
        return None, "stdout must contain one JSON object"
    if set(response) != expected_keys:
        return None, f"response keys must be exactly {sorted(expected_keys)}"
    if response["contract_version"] != CONTRACT_VERSION:
        return None, f"contract_version must be {CONTRACT_VERSION}"
    if response["request_id"] != request["request_id"]:
        return None, "request_id does not match the request"
    if response["status"] != "ok":
        return None, f'status must be "ok", got {response["status"]!r}'
    return response, None


def describe_or_fail(
    adapter: Path, protocol_release: str
) -> tuple[dict[str, Any] | None, str | None]:
    request = {
        "contract_version": CONTRACT_VERSION,
        "operation": "describe",
        "protocol_release": protocol_release,
        "request_id": "describe",
    }
    response, error = invoke_adapter(adapter, request, ADAPTER_DESCRIBE_KEYS)
    if error:
        return None, error
    implementation = response["implementation"]
    if not isinstance(implementation, dict) or set(implementation) != {"name", "version"}:
        return None, "implementation must contain exactly name and version"
    for field in ("name", "version"):
        value = implementation[field]
        if not isinstance(value, str) or not value:
            return None, f"implementation.{field} must be a non-empty string"
    supported = response["supported_protocol_releases"]
    if not isinstance(supported, list) or protocol_release not in supported:
        return None, f"adapter does not declare support for {protocol_release}"
    return implementation, None


def build_implementation_report(
    protocol_release: str,
    implementation: dict[str, Any] | None,
    results: list[dict[str, Any]],
    handshake_error: str | None,
) -> dict[str, Any]:
    subject: dict[str, Any] = {"kind": "implementation"}
    if implementation is not None:
        subject["name"] = implementation["name"]
        subject["version"] = implementation["version"]

    checks: list[dict[str, str]] = []
    if handshake_error is not None:
        checks.append(
            {
                "id": "adapter-contract",
                "status": "fail",
                "summary": f"adapter contract {CONTRACT_VERSION} handshake failed: {handshake_error}",
            }
        )
        for check_id in CHECK_ORDER[1:]:
            checks.append(
                {
                    "id": check_id,
                    "status": "skip",
                    "summary": "not run because the adapter contract handshake failed",
                }
            )
    else:
        checks.append(
            {
                "id": "adapter-contract",
                "status": "pass",
                "summary": f"adapter contract {CONTRACT_VERSION} handshake passed",
            }
        )
        for check_id in CHECK_ORDER[1:]:
            bucket = [item for item in results if item["bucket"] == check_id]
            if not bucket:
                raise AssertionError(f"no cases collected for check {check_id!r}")
            failures = [item for item in bucket if not item["ok"]]
            total = len(bucket)
            if failures:
                first = failures[0]
                reason = first["error"] or "verdict did not match the protocol"
                checks.append(
                    {
                        "id": check_id,
                        "status": "fail",
                        "summary": (
                            f"{total - len(failures)}/{total} cases classified correctly; "
                            f"first mismatch: {first['id']} "
                            f"(expected {'accept' if first['expected'] else 'reject'})"
                            f" — {reason}"
                        ),
                    }
                )
            else:
                checks.append(
                    {
                        "id": check_id,
                        "status": "pass",
                        "summary": f"{total} cases classified correctly",
                    }
                )

    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    if status == "pass" and ("name" not in subject or "version" not in subject):
        raise AssertionError("a passing implementation report must record name and version")
    return {
        "format_version": "1.0",
        "protocol_release": protocol_release,
        "runner": {"name": RUNNER_NAME, "version": RUNNER_VERSION},
        "subject": subject,
        "status": status,
        "checks": checks,
    }


def test_implementation(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path

    # Release identity first. The case suite below is a fixed set of frozen
    # artifacts, so the release named in the report must be proven, not merely
    # read out of an unverified file: otherwise a hand-written manifest could
    # have v0.1.0-preview.1 cases reported under an arbitrary release name.
    manifest, manifest_check = verify_manifest(root, manifest_path)
    if manifest_check["status"] != "pass":
        return runner_error(f"manifest is not a valid release manifest: {manifest_check['summary']}")
    digest_check = verify_schema_digests(root, manifest)
    if digest_check["status"] != "pass":
        return runner_error(f"release integrity check failed: {digest_check['summary']}")

    protocol_release = manifest.get("protocol_release")
    if protocol_release != IMPLEMENTATION_CASE_RELEASE:
        return runner_error(
            f"the implementation case suite covers {IMPLEMENTATION_CASE_RELEASE}, "
            f"not {protocol_release!r}. Add a case suite for the new release instead of "
            "letting this one stand in for it."
        )

    # The official judge must be self-consistent before it certifies anyone else.
    # This is a runner error, not an implementation verdict.
    preflight = run_public_conformance(root)
    if preflight["status"] != "pass":
        return runner_error(f"public conformance preflight failed: {preflight['summary']}")

    adapter = Path(args.adapter)
    if not adapter.is_absolute():
        adapter = Path.cwd() / adapter
    if not adapter.is_file():
        print(f"conformance runner error: adapter not found: {adapter}", file=sys.stderr)
        return 1

    implementation, handshake_error = describe_or_fail(adapter, protocol_release)
    results: list[dict[str, Any]] = []
    if handshake_error is None:
        for item in collect_cases(root):
            request = {
                "contract_version": CONTRACT_VERSION,
                "operation": "validate",
                "protocol_release": protocol_release,
                "request_id": item["request_id"],
                "case": item["case"],
            }
            response, error = invoke_adapter(adapter, request, ADAPTER_VALIDATE_KEYS)
            if error is None and not isinstance(response["accepted"], bool):
                error = "accepted must be a boolean"
            results.append(
                {
                    "id": item["id"],
                    "bucket": item["bucket"],
                    "expected": item["expected"],
                    "error": error,
                    "ok": error is None and response["accepted"] == item["expected"],
                }
            )

    report = build_implementation_report(
        protocol_release, implementation, results, handshake_error
    )
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
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    render_report(report, args.json)
    if report["status"] != "pass" and handshake_error is not None:
        print(f"adapter failure: {handshake_error}", file=sys.stderr)
    return 0 if report["status"] == "pass" else 1


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

    implementation = subparsers.add_parser(
        "test-implementation",
        help=(
            "test a third-party implementation through the adapter contract and "
            "emit an implementation compatibility report"
        ),
    )
    implementation.add_argument(
        "--adapter",
        required=True,
        help="path to an executable adapter implementing contract 1.0",
    )
    implementation.add_argument("--root", default=".", help="repository checkout root")
    implementation.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="release manifest used to select the protocol release under test",
    )
    implementation.add_argument(
        "--json",
        action="store_true",
        help="print the compatibility report as JSON",
    )
    implementation.add_argument(
        "--report",
        help="write the compatibility report JSON to this path",
    )
    implementation.set_defaults(func=test_implementation)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
