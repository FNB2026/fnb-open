# Protocol Preview Status

FNB's public protocol remains a **v0.1 pre-release**. Its governing RFC review
is complete, but no immutable preview tag has been cut yet. It is intentionally
smaller than the private product implementation.

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

## Review outcome

The first review opened on 2026-07-13 and completed on 2026-07-26:

- RFC-0001 is **Accepted** for individually attributable BlockDraft decisions.
- RFC-0002 is **Accepted** after its second public review and a 2026-09-04
  Steward decision. It defines deterministic invalidation and deletion-safe
  audit retention without making product implementation normative.
- RFC-0003 is **Accepted** after its second public review and a 2026-09-19
  Steward decision. It defines portable permission snapshots and source-state
  invalidation semantics without making authentication or product policy
  normative.

The absence of external comments did not itself accept RFC-0002 or RFC-0003.
Each Steward decision records a final adversarial review and the accepted public
scope explicitly.

## Next gates

1. Keep schema, example, cross-reference, and negative-fixture validation green
2. Freeze the accepted v0.1 artifact set with an immutable preview Git tag and a
   versioned schema-digest manifest
3. Publish an independently runnable conformance CLI over synthetic fixtures
4. Publish a deliberately narrow protocol-object exchange OpenAPI preview and
   local mock server
5. Generate type definitions or SDK surfaces only from public protocol
   artifacts, without connecting them to private product services

Private product changes are not copied into this preview while they remain
uncommitted, unreviewed, or implementation-specific. Authentication, workers,
ledger, storage, IM/WebSocket, administration, and deployment remain outside the
first OpenAPI preview.

The governing RFCs are Accepted, but the schemas remain pre-release until an
immutable preview tag freezes the exact artifact set and digests.
