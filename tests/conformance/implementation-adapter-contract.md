# FNB Implementation Conformance Adapter Contract v1.0

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

This contract lets an independent FNB implementation — in any language — be
tested by the official conformance runner. The runner owns the expected answers;
the adapter only classifies the protocol material it is given.

```text
Language-neutral executable adapter.
One JSON request per process.
Operations: describe, validate only.
Official runner owns expected answers.
Reuse compatibility-report 1.0 unchanged.
```

## Why validation, not generation

The public protocol states what is **valid**, what is **invalid**, and which
relationships must hold. It does not define generation of final user-owned
objects: those are non-normative product behaviours. So contract v1.0 deliberately
exposes only `describe` and `validate`.

An adapter is **not** asked to produce a `Memory`, a `Block`, or a whole world.
Doing so would quietly promote private product algorithms into the public
protocol. Generation-shaped operations such as `derive_invalidation` may appear
in a later contract version, and only where the public protocol already defines a
single deterministic answer.

## Process model

One request per process. The runner starts the adapter with the request on
stdin and reads one JSON object from stdout:

```python
subprocess.run([adapter_path], input=request_json, capture_output=True,
               text=True, timeout=10, shell=False)
```

One process per request means:

- no hidden cross-case state;
- crashes and timeouts are attributed to exactly one case;
- no framing, session, reset, or concurrency protocol is needed;
- Rust, Go, TypeScript, and Python adapters are all equally straightforward.

The adapter must be a directly executable file (a shebang plus the executable
bit). On a platform that cannot launch files that way, ship a small native
launcher. The runner never uses a shell.

### Adapter failure (fail-closed)

Any of the following fails the whole run as an **adapter failure**, never as a
classification:

- process exit code is not 0;
- the process exceeds the timeout;
- stdout is not exactly one UTF-8 JSON object;
- the response is not an object, or has keys outside the contract;
- `contract_version` is not `"1.0"`;
- `request_id` does not match the request;
- `status` is present but not `"ok"`;
- `accepted` is missing or is not a boolean;
- `describe` declares it does not support the requested protocol release.

Logs, banners, and progress output belong on **stderr**. Anything on stdout
other than the single response object is a failure.

### Runner errors are not verdicts

Before the adapter is contacted at all, the runner establishes that the claim it
is about to make is well formed:

```text
verify_manifest → verify_schema_digests → case suite supports this release
→ public conformance preflight → describe → validate × N → implementation report
```

Each of these is a **runner error**: the run stops, nothing is written to
`--report`, and no statement about the implementation is made. They are not
implementation failures.

- **Release identity.** The manifest is verified as a release manifest and its
  schema bytes and digests are checked before its `protocol_release` is trusted.
  A hand-written manifest cannot have one release's cases reported under another
  release's name.
- **Case suite release.** The case suite is written against exactly one release,
  declared as `IMPLEMENTATION_CASE_RELEASE` in the runner. A mismatch is an
  error, so a future preview must add its own case suite rather than letting this
  one stand in for it.
- **Public conformance preflight.** The official judge must be self-consistent
  about its own schemas, fixtures, and worlds before it certifies anyone else.
  An unsound judge has no standing to issue a compatibility report.

Only after all of that does an adapter interaction failure become an
**adapter failure**, which *does* produce a report with `status: "fail"` and a
failed `adapter-contract` check.

## Operation: describe

Request:

```json
{
  "contract_version": "1.0",
  "operation": "describe",
  "protocol_release": "v0.1.0-preview.1",
  "request_id": "describe"
}
```

Response:

```json
{
  "contract_version": "1.0",
  "request_id": "describe",
  "status": "ok",
  "implementation": { "name": "example-fnb-rust", "version": "0.1.0" },
  "supported_protocol_releases": ["v0.1.0-preview.1"]
}
```

`implementation.name` and `implementation.version` appear in the compatibility
report. **Do not put a local filesystem path there** — it is not portable and it
leaks the author's machine layout.

## Operation: validate

The runner sends protocol material and no expected answer. The adapter replies
with its own verdict.

Object case:

```json
{
  "contract_version": "1.0",
  "operation": "validate",
  "protocol_release": "v0.1.0-preview.1",
  "request_id": "case-6f1a0d3c9b47e582",
  "case": {
    "kind": "object",
    "schema": "actor.schema.json",
    "instance": { "...": "..." }
  }
}
```

Chain case:

```json
{
  "contract_version": "1.0",
  "operation": "validate",
  "protocol_release": "v0.1.0-preview.1",
  "request_id": "case-2b8e77c41a90fd63",
  "case": { "kind": "source_state_chain", "instance": { "...": "..." } }
}
```

Response:

```json
{
  "contract_version": "1.0",
  "request_id": "case-2b8e77c41a90fd63",
  "status": "ok",
  "accepted": false
}
```

### `request_id` is opaque and carries no verdict

A `request_id` is `case-` followed by 16 lowercase hex characters, derived from
the case's origin. It never contains a source path, a case name, or any word that
hints at the expected outcome.

This matters: an identifier like `tests/conformance/v0.1/invalid/foo.json` would
hand the answer to the adapter, and `valid` / `invalid` cannot appear inside a
hex string, so the shape is a structural guarantee rather than a convention. The
runner asserts the shape before sending anything. The human-readable source of a
case appears only in the runner-side report, never on the wire.

### Case kinds in v1.0

| `case.kind` | `case.instance` | Meaning |
| --- | --- | --- |
| `object` | one protocol object, with `case.schema` naming its frozen schema | the object must satisfy that schema **and** the object-level invariants |
| `protocol_chain` | `{ "flow_event": …, "node": …, "ai_inference": …, "block_draft": …, "correction": …, "block": … }` | the cross-object chain must be consistent |
| `invalidation_chain` | `{ "records": [ … ] }` | propagation must be ordered, linked, and deduplicated as the protocol requires |
| `source_state_chain` | `{ "permission_snapshot": …, "source_state_change": …, "invalidation": … }` | the change must be a legal transition and the invalidation must match it |

`accepted` means "the protocol accepts this material": schema validity for
`object`, and schema validity plus the relevant cross-object invariants for the
chain kinds. An adapter that only checks JSON Schema will fail the chain and
semantic cases — that is intended.

## Where the cases come from

The runner reuses the repository's existing test assets; no new semantic
fixtures are introduced by this contract:

```text
tests/conformance/v0.1/valid/                     expect accepted
tests/conformance/v0.1/invalid/                   expect rejected
tests/conformance/v0.1/invalid-semantics/         expect rejected
tests/conformance/v0.1/invalid-chains/            expect rejected
tests/conformance/v0.1/valid-invalidation-chains/ expect accepted
tests/conformance/v0.1/invalid-invalidation-chains/ expect rejected
tests/conformance/v0.1/valid-source-state-chains/ expect accepted
tests/conformance/v0.1/invalid-source-state-chains/ expect rejected
examples/synthetic-protocol-chain.json            expect accepted
tests/fixtures/generated/*.json                   expect accepted
```

Expected outcomes live only in the runner. They are never sent to the adapter,
so an adapter cannot simply echo a supplied answer.

## Running it

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/fnb-conformance.py test-implementation --adapter ./my-fnb-adapter
python3 tools/fnb-conformance.py test-implementation --adapter ./my-fnb-adapter --json
```

The output is a **compatibility report format 1.0** document with
`subject.kind: "implementation"`. In that report, `runner.version` versions the
**tooling** independently of the protocol it verifies, while `protocol_release`
names the release under test; a runner change is never reported as a protocol
change. That format is unchanged by this contract and
its schema is frozen at the `v0.1.0-preview.1` tag: this contract reuses it and
must not modify it. Tightening of which `subject` fields are required for a
given `kind` (for example requiring `name` and `version` for `implementation`, or
`manifest` for `release_bundle`) is enforced by the runner, not by the schema.

A report records the implementation's `name` and `version` only — never a local
path.

## Scope, and what a pass means

The conformance contract provides no network or product-service dependency.
Network isolation of the tested implementation is outside the certification
scope: the runner cannot reliably confine an arbitrary third-party executable.

A passing report is evidence for the checks reported. It is not product
certification, security certification, or legal compliance. It says the
implementation classified the public protocol material the way the protocol
requires — nothing more.
