# v0.1 Draft Changelog

The v0.1 protocol remains pre-release. This changelog records reviewed protocol
changes and immutable preview publication boundaries.

## 2026-09-19 — v0.1.0-preview.1 freeze candidate

- Froze all 14 protocol schema `$id` values to the immutable
  `v0.1.0-preview.1` tag namespace rather than mutable `main`.
- Added a byte-exact SHA-256 schema digest manifest for the preview.
- Added a machine-readable compatibility report format and an independent
  `fnb-conformance` CLI that verifies release integrity before running the
  public synthetic conformance suite.
- Kept the release surface protocol-only: no private product commit mapping,
  service endpoint, authentication implementation, storage, worker, IM, or
  deployment behavior is included.

## 2026-09-19 — RFC-0003 accepted

- Added implementation-neutral `PermissionSnapshot` and `SourceStateChange`
  objects without exposing ACLs, credentials, sessions, or storage topology.
- Defined source redaction, deletion, staleness, and withdrawn permission as
  triggers for RFC-0002 invalidation; `active` alone does not invalidate.
- Added positive and object-semantic negative fixtures for snapshot expiry and
  source-state transition invariants, including a validator-enforced 25-pair
  portable transition matrix.
- Clarified that permission restoration does not reactivate invalidated derived
  objects and that a permission-withdrawal SourceStateChange supplies the
  `permission_change` trigger identifier.
- Marked the v0.1 permission values as preview vocabulary rather than a legal
  conclusion or a claim of DPV/DPV-AI equivalence.

## 2026-09-04 — RFC-0002 accepted

- Added `InvalidationRecord` for deterministic, append-only propagation from a
  correction, source change, permission change, or parent invalidation.
- Defined a reproducible SHA-256 idempotency key over the canonical trigger and
  target tuple, including a stable parent key for transitive propagation.
- Defined breadth-first deduplication so one propagation run emits one record
  per affected target even when multiple upstream paths converge.
- Added `AuditTombstone` as the maximum data-minimized audit shape that may
  replace identifiable correction/deletion records when a valid retention
  basis exists; narrowed retention bases to statutory obligations, active
  security incidents, and active disputes.
- Added positive, schema-negative, and semantic-negative conformance fixtures
  for reason/trigger compatibility, redaction, idempotency, parent linkage,
  direct-reference exclusion, and bounded retention.

## 2026-07-26 — First review decision

- Completed the first public v0.1 review window.
- Accepted RFC-0001 with individually attributable decisions and an explicit
  minimum rejection record.
- Moved RFC-0002 and RFC-0003 to Revision until downstream invalidation,
  deletion-safe audit metadata, portable permission snapshots, and
  source-invalidation semantics are represented in public artifacts.
- Kept private implementation experiments non-normative and deferred the
  immutable tag, digest manifest, OpenAPI preview, and SDK generation until the
  remaining protocol semantics are reviewed.

## 2026-07-13 — Reproducible publication gate

- Canonically formatted all public schemas with two-space JSON indentation.
- Added a CI gate requiring every schema-changing pull request to update this
  changelog. This records draft-breaking changes without claiming backward
  compatibility before v0.1 is accepted.

## 2026-07-13 — Protocol invariants

- Replaced Relationship's global status/label with participant-specific
  assertions and required at least one evidence item.
- Required every persisted AIInference to include structured model identity and
  a non-empty Explanation, separating inference status from user confirmation.
- Required Blocks to retain the confirming actor, event, operation, and time;
  AI-derived rewrites also retain their Draft and Correction identifiers.
- Added owner, actor, type, state, correction-result, evidence-resolution, and
  temporal checks to the reference chain.
- Added negative fixtures for evidence-free Relationships, unexplained
  inferences, and rejected Drafts that incorrectly produce Blocks.
- Replaced placeholder schema identifiers with resolvable identifiers controlled
  by the public FNB2026 repository and documented the immutable-release gate.

## 2026-07-13 — Conformance baseline

- Split Memory user-confirmation `status` from retention `lifecycle_state`.
- Standardized the proposed Memory state name as `candidate` rather than `suggested`.
- Added `Block.creation_mode` and require `draft_id` for `ai_derived` Blocks.
- Added executable schema, example, cross-reference, and negative-fixture checks.

These changes tighten the existing sovereignty rules; they do not claim wire
compatibility with the private product implementation.
