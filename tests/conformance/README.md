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
