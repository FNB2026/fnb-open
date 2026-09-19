# RFC-0003: Source Provenance and Permission Snapshots

## Status

Accepted — Steward decision recorded 2026-09-19 after the second public review
through [PR #16](https://github.com/FNB2026/fnb-open/pull/16). The first
Steward decision was recorded 2026-07-26 after
[public review #5](https://github.com/FNB2026/fnb-open/discussions/5).

## Summary

Require derived memories and protocol events to preserve source references and
the permission context used when they were created.

## Motivation

A memory without provenance cannot be reliably explained, corrected, or
invalidated when its source changes.

## Design

FlowEvent carries a `source_ref` and may identify a permission snapshot. Memory
contains one or more MemorySource entries with source type and object ID. Derived
objects must not broaden the visibility of their sources.

### PermissionSnapshot

`PermissionSnapshot` records the portable facts that made a particular source
use permissible when a derived object was created: its source reference,
subject scope, allowed actions, visibility scope, basis, capture time, and an
optional expiry. It is neither an authentication credential nor an export of an
implementation's ACL, session, token, identity graph, or storage topology.

The snapshot answers "why was this source usable then?" It does not grant
current access. Implementations must evaluate current authority before resolving
the source or reusing a derived object.

The v0.1 `basis`, `allowed_actions`, and subject/visibility values are
implementation-neutral preview vocabulary. They are not a legal determination,
do not by themselves establish a lawful basis or authorization, and do not
claim equivalence or conformance with DPV, DPV-AI, or another privacy vocabulary.
A later mapping or vocabulary revision may replace or qualify these values
without making private product policy normative.

### SourceStateChange and invalidation

`SourceStateChange` records only a source reference, prior and new portable
state, a constrained reason code, and its effective time. Its states are
`active`, `stale`, `redacted`, `deleted`, and `permission_withdrawn`.

The portable state machine is deliberately narrow. All state pairs not listed
below are forbidden, including self-transitions and every transition from
`deleted`.

| Previous state | Allowed next state | Required reason code |
| --- | --- | --- |
| `active` | `stale`, `redacted`, `deleted`, `permission_withdrawn` | `source_stale`, `source_redacted`, `source_deleted`, `permission_withdrawn` |
| `stale` | `active`, `redacted`, `deleted`, `permission_withdrawn` | `source_restored`, `source_redacted`, `source_deleted`, `permission_withdrawn` |
| `redacted` | `deleted` | `source_deleted` |
| `deleted` | none (terminal) | n/a |
| `permission_withdrawn` | `active`, `redacted`, `deleted` | `permission_restored`, `source_redacted`, `source_deleted` |

`source_restored` means a previously stale source became usable again.
`permission_restored` means authority changed; it does not assert that source
content itself was restored. A redacted source cannot become active again;
deletion may still supersede redaction. Restoration never reverses an existing
`InvalidationRecord` or automatically reactivates a derived object. Reuse or
re-derivation requires current authority evaluation and a new conforming state
transition under the applicable RFCs.

RFC-0002 is the shared execution protocol; this RFC does not create a second
invalidation mechanism. After provenance and current-permission evaluation:

- `redacted` MUST emit an `InvalidationRecord` with `trigger_type:
  source_change`, `reason_code: source_redacted`, and `resulting_state:
  invalidated`.
- `deleted` MUST emit the same shape with `reason_code: source_deleted` and
  `resulting_state: invalidated`.
- `permission_withdrawn` MUST emit an `InvalidationRecord` with `trigger_type:
  permission_change`, `reason_code: permission_withdrawn`, and
  `resulting_state: invalidated`.
- `stale` MUST emit an `InvalidationRecord` with `trigger_type: source_change`,
  `reason_code: source_stale`, and either `invalidated` or `review_required`.
- `active` MUST NOT by itself emit an invalidation record.

The direct record's trigger identifier is the relevant source-state or
permission-change event. When `new_state` is `permission_withdrawn`, the
`SourceStateChange.source_change_id` is the event identifier carried as
`InvalidationRecord.trigger_id` even though the trigger type is
`permission_change`. All downstream traversal, target deduplication, parent
linkage, and idempotency follow RFC-0002.

This RFC defines semantics only; authentication internals and storage topology
remain outside the public protocol.

## Data Sovereignty Impact

Users can identify where a derived claim came from and withdraw or correct its
source.

## Privacy Impact

Source references are identifiers, not authorization grants. Implementations
must check current access before resolving them.

## AI Explainability Impact

Inference evidence must resolve through the same permission-aware provenance
rules.

## Compatibility

This formalizes fields already present in the v0.1 draft schemas.

## Alternatives

Embedding source text directly in every derived object was rejected because it
duplicates sensitive data and weakens revocation.

## Revision Requirements

- [x] Define a portable permission snapshot that does not expose authentication
  or storage internals.
- [x] Distinguish source redaction, deletion, staleness, and invalidation
  without broadening access to retained provenance.
- [x] Reuse RFC-0002 deterministic propagation and add positive and negative
  object-level conformance fixtures.
- [x] Complete a second public review and record a Steward decision.

Private implementation status names and cascade behavior are non-normative
until they are represented in the public schemas, fixtures, and validator.


## Steward Decision — 2026-09-19

**Accepted.** The second public review was available through
[PR #16](https://github.com/FNB2026/fnb-open/pull/16) for more than the minimum
seven-day discussion period. No formal review or PR-local substantive feedback
was recorded. That silence did not decide the RFC: the Steward completed a final
adversarial review before acceptance.

The final review resolved three ambiguity and safety concerns before this
decision: the permission-withdrawal trigger identifier is now explicit;
restoration cannot silently reactivate already-invalidated derived objects; and
the v0.1 permission vocabulary is explicitly a preview vocabulary rather than a
legal conclusion or a claim of DPV/DPV-AI equivalence. The existing conformance
suite already enforces snapshot-expiry semantics, the complete source-state
transition matrix, and source-state-to-RFC-0002 invalidation behavior.

This decision accepts only the implementation-neutral RFC semantics, JSON
Schemas, synthetic fixtures, and public validator behavior. It does not accept,
publish, or make normative any private authentication, ACL, product API,
storage, worker, IM/WebSocket, migration, deployment, or production behavior.
