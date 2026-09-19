# Protocol Preview Status

FNB's public protocol remains a **v0.1 pre-release**. Its governing RFC review
is complete and the accepted artifact set is frozen at the immutable preview tag
`v0.1.0-preview.1`. The preview is intentionally smaller than the private
product implementation.

## Tagged release record

- Tag: `v0.1.0-preview.1` (annotated and signed; GitHub verification reports
  `verified`, reason `valid`)
- Tag object: `f492754744d74ed3459c4ce361108ba8c8a04acc`
- Target commit: `2f7226c1cba688aba3b130f901379cfe79488ae7` (merge of PR #17,
  2026-09-19)
- Frozen artifact set: the 14 schemas under `specs/v0.1/`, recorded byte-exactly
  in `specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json`

The tag is an immutable publication boundary and must never be moved, reused, or
retargeted. Any protocol change after this freeze requires a new version, a new
tag, and a new digest manifest.

## Published in this preview

- The 14 implementation-neutral JSON Schemas under `specs/v0.1/`, frozen at tag
  `v0.1.0-preview.1`
- The byte-exact SHA-256 schema digest manifest for that frozen set
- A synthetic FlowEvent → Node → AIInference → BlockDraft → Correction → Block chain
- The accepted RFCs covering confirmation (RFC-0001), explainability and
  deterministic invalidation (RFC-0002), and source provenance with portable
  permissions (RFC-0003)
- Positive, schema-negative, object-semantic-negative, and cross-object negative
  conformance fixtures under `tests/conformance/`
- An independent conformance runner (`tools/fnb-conformance.py`) and the
  machine-readable compatibility-report format it emits
- Public validation tooling with hash-pinned dependencies

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

Met by the `v0.1.0-preview.1` freeze on 2026-09-19:

- Freeze the accepted v0.1 artifact set with an immutable preview Git tag and a
  versioned schema-digest manifest
- Publish a conformance runner that completes over synthetic fixtures with no
  product-service or network dependency

Still open:

1. Keep schema, example, cross-reference, and negative-fixture validation green
   (a continuing gate rather than a one-time milestone)
2. Publish a deliberately narrow protocol-object exchange OpenAPI preview and
   local mock server
3. Generate type definitions or SDK surfaces only from public protocol
   artifacts, without connecting them to private product services

The shipped runner verifies the published release bundle. It does not yet
evaluate a third-party implementation, so `subject.kind: implementation` in the
compatibility-report format is permitted by the schema but is not yet produced
by any shipped command.

Private product changes are not copied into this preview while they remain
uncommitted, unreviewed, or implementation-specific. Authentication, workers,
ledger, storage, IM/WebSocket, administration, and deployment remain outside the
first OpenAPI preview.

The governing RFCs are Accepted and the exact artifact set plus digests are now
frozen by `v0.1.0-preview.1`. The schemas remain **pre-release**: the freeze pins
this preview's bytes, it does not promise stability for later v0.1 previews.
