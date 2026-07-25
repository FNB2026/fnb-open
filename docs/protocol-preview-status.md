# Protocol Preview Status

FNB's public protocol preview remains a **v0.1 Draft**, with its first review
window completed. It is intentionally smaller than the private product
implementation.

## Published in this preview

- Implementation-neutral JSON Schemas under `specs/v0.1/`
- A synthetic FlowEvent → Node → AIInference → BlockDraft → Correction → Block chain
- Initial RFCs covering confirmation, explainability, and source provenance

## Deliberately excluded

- Authentication internals and worker credentials
- Administrative and private product endpoints
- Production storage, ledger, deployment, and network topology
- Real user data or examples derived from real conversations
- Unimplemented research objects presented as stable protocol contracts

## First review outcome

The first review opened on 2026-07-13 and completed on 2026-07-26:

- RFC-0001 is **Accepted** for individually attributable BlockDraft decisions.
- RFC-0002 is in **Revision** with a concrete downstream invalidation and
  deletion-safe audit proposal prepared for a second public review.
- RFC-0003 is in **Revision** pending portable permission snapshots and
  source-invalidation semantics.

The absence of external comments does not turn unresolved questions into stable
protocol contracts. The Steward decision records accepted scope explicitly and
keeps unresolved semantics in Revision.

## Next gates

1. Keep schema, example, cross-reference, and negative-fixture validation green
2. Complete reviewed revisions of RFC-0002 and RFC-0003
3. Freeze accepted schema identifiers with an immutable Git tag and publish a
   versioned digest manifest
4. Publish a deliberately narrow, schema-first OpenAPI preview
5. Generate a TypeScript SDK preview from the reviewed OpenAPI and public schemas

Private product changes are not copied into this preview while they remain
uncommitted, unreviewed, or implementation-specific. Authentication, workers,
ledger, storage, IM/WebSocket, administration, and deployment remain outside the
first OpenAPI preview.

Draft schemas may change incompatibly until their governing RFCs are Accepted
and an immutable release freezes their identifiers and digests.
