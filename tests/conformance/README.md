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
