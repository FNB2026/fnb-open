# Public Protocol Conformance Fixtures

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

Each fixture names a v0.1 schema and contains one synthetic instance:

- `valid/` instances must pass that schema.
- `invalid/` instances must fail that schema and protect a protocol invariant.
- `invalid-semantics/` instances pass JSON Schema but must fail object-level
  invariants such as participant membership and evidence resolution.
- `invalid-chains/` objects pass their individual schemas but must fail
  cross-object protocol semantics.

The invalid fixtures prove that durable Memories and Relationships require
provenance, AIInference requires explanation, AI-derived Blocks cannot bypass a
user-governed BlockDraft, and rejected Drafts cannot produce Blocks.
