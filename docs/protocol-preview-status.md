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
  machine-readable compatibility-report format it emits, now covering
  third-party implementations as well as the release bundle
- Declaration-only TypeScript protocol bindings under `bindings/`, generated from
  the frozen schemas by `tools/generate-bindings.py` (not an SDK runtime)
- Deterministic synthetic fixture worlds under `tests/fixtures/generated/`,
  produced by `tools/fnb-fixtures.py` from a scenario and a seed alone
- An implementation adapter contract (v1.0) that lets an implementation in any
  language be classified by the official runner
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

Met since, without changing any frozen byte:

- Generate type definitions from the public protocol artifacts only
  (declaration-only TypeScript bindings, regenerated and diff-checked in CI)
- Publish synthetic fixture worlds that a third party can reproduce from a
  scenario and a seed, instead of needing real data
- Let a third party's implementation, in any language, be judged by the official
  runner through adapter contract 1.0

Still open:

1. Keep schema, example, cross-reference, and negative-fixture validation green
   (a continuing gate rather than a one-time milestone)
2. Publish a deliberately narrow protocol-object exchange OpenAPI preview and
   local mock server
3. Generate transport SDK surfaces only from public protocol artifacts, once the
   object-exchange binding is frozen, without connecting them to private product
   services

The shipped runner now evaluates third-party implementations as well as the
published release bundle: `fnb-conformance test-implementation --adapter <path>`
drives an executable adapter through contract 1.0 and emits a compatibility
report with `subject.kind: implementation`. Expected verdicts live only in the
runner and are never sent to the adapter, and the runner verifies the release
identity of its own case suite before it certifies anyone else.

What the runner still does not do: it defines no HTTP surface, no transport
binding, and no client. The public protocol states what is valid, invalid, and
which relationships must hold; it does not define how private product features
work, and no shipped command asks an implementation to generate final user-owned
objects.

Private product changes are not copied into this preview while they remain
uncommitted, unreviewed, or implementation-specific. Authentication, workers,
ledger, storage, IM/WebSocket, administration, and deployment remain outside the
first OpenAPI preview.

The governing RFCs are Accepted and the exact artifact set plus digests are now
frozen by `v0.1.0-preview.1`. The schemas remain **pre-release**: the freeze pins
this preview's bytes, it does not promise stability for later v0.1 previews.
