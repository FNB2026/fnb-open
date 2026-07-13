# Public Protocol Conformance Fixtures

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

Each fixture names a v0.1 schema and contains one synthetic instance:

- `valid/` instances must pass that schema.
- `invalid/` instances must fail that schema and protect a protocol invariant.

The invalid fixtures currently prove that durable Memories require provenance
and that AI-derived Blocks cannot bypass a user-governed BlockDraft.
