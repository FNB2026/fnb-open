# Public Protocol Conformance Fixtures

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

Each fixture names a v0.1 schema and contains one synthetic instance:

- `valid/` instances must pass that schema.
- `invalid/` instances must fail that schema and protect a protocol invariant.
- `invalid-semantics/` instances pass JSON Schema but must fail object-level
  invariants such as participant membership and evidence resolution.
- `invalid-chains/` objects pass their individual schemas but must fail
  cross-object protocol semantics.
- `valid-invalidation-chains/` records form a valid direct-to-transitive
  invalidation sequence.
- `invalid-invalidation-chains/` records pass their individual schemas but
  violate propagation ordering or uniqueness.
- `valid-source-state-chains/` ties a portable permission snapshot and source
  change to its required RFC-0002 invalidation.
- `invalid-source-state-chains/` exercises forbidden source-state to
  invalidation mappings.

The invalid fixtures prove that durable Memories and Relationships require
provenance, AIInference requires explanation, AI-derived Blocks cannot bypass a
user-governed BlockDraft, rejected Drafts cannot produce Blocks, invalidation
records have deterministic trigger/target semantics, and deletion-safe audit
tombstones cannot retain direct object references beyond their purge bound.
Permission snapshots must not expire at capture, and source-state changes must
be actual transitions rather than no-op records.


## Compatibility reports and release verification

`compatibility-report.schema.json` defines the machine-readable result envelope
for public conformance checks. The format can describe a frozen release bundle
or, in later tooling, a third-party implementation. A `pass` applies only to
the listed checks and is not a product, security, privacy, or legal
certification.

For `v0.1.0-preview.1`, run:

```bash
python3 tools/fnb-conformance.py verify-release \
  --root . \
  --manifest specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json \
  --json
```

The runner has no network or product-service dependency. It verifies the exact
public schema set and digests before invoking the repository's synthetic
reference conformance suite.

## Third-party implementation conformance

[`implementation-adapter-contract.md`](./implementation-adapter-contract.md)
defines adapter contract v1.0: a language-neutral executable that reads one JSON
request from stdin and writes one JSON response to stdout, one process per
request, with `describe` and `validate` operations only. The runner owns the
expected answers and never sends them, so an adapter cannot echo a supplied
verdict. Contract v1.0 deliberately does not ask an adapter to *generate* final
user-owned objects, because the public protocol does not define a single
normative answer for those.

```bash
python3 tools/fnb-conformance.py test-implementation --adapter ./my-fnb-adapter
```

The cases are the assets already in this directory, plus
`examples/synthetic-protocol-chain.json` and the generated worlds under
`tests/fixtures/generated/`. The output is a compatibility report format 1.0 with
`subject.kind: "implementation"`; that format is frozen at the
`v0.1.0-preview.1` tag and this contract reuses it unchanged.

Under `adapters/`, two helpers exist for CI only, not as deliverables:
`reference-adapter.py` is a contract test double that answers through the
repository validator (it is not an FNB implementation and not a conformance
authority), and `faulty-adapter.py` accepts everything so the suite can prove the
runner detects an incorrect implementation.
