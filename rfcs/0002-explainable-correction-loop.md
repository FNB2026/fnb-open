# RFC-0002: Explainable Correction Loop

## Status

Accepted — Steward decision recorded 2026-09-04 after the second public review
through [PR #15](https://github.com/FNB2026/fnb-open/pull/15). The first
Steward decision was recorded 2026-07-26 after
[public review #5](https://github.com/FNB2026/fnb-open/discussions/5).

## Summary

Require AI-derived proposals to expose evidence and provide confirm, reject,
replace, and redact correction operations.

## Motivation

Confidence alone is not an explanation. Users need to see why a proposal exists
and must be able to correct it without erasing the audit trail.

## Design

AIInference records purpose, structured model identity, input references, output
summary, confidence, model-record status, and a separate user-confirmation
status. Every persisted inference includes an Explanation with a human-readable
rationale and at least one evidence reference resolvable through its inputs.
CorrectionPatch records the actor, target, operation, reason, timestamp, and
optional before/after values.

Corrections append new state transitions; they do not rewrite historical
inference records in place.

### Downstream invalidation

A CorrectionPatch with operation `reject`, `replace`, or `redact` invalidates
every persisted derived object whose normative creation inputs include the
corrected target. Existing derived objects are never silently rewritten:
replacement produces new derived object identities after the correction is
applied.

Each affected object receives one append-only InvalidationRecord per propagation
run. Direct records use `trigger_type: correction_patch`. A transitive record
uses `trigger_type: parent_invalidation`; its `trigger_id` is the immediately
preceding record's `idempotency_key`, and its `parent_invalidation_id` retains
the trace reference to that record. The stable parent key, rather than an
implementation-generated record identifier, keeps transitive idempotency
reproducible across implementations.

Processing is deterministic and breadth-first:

1. enumerate direct dependants in ascending `(target_type, target_id)` order;
2. emit one record per direct dependant with `resulting_state: invalidated`;
3. for every later depth, enumerate candidate dependants of records emitted at
   the preceding depth, sort candidates by `(target_type, target_id,
   parent_idempotency_key)`, and emit only the first candidate for each target;
4. never emit a later record for a target already emitted during the run; repeat
   until no active dependant remains.

This ordering selects a stable predecessor where a derived object has multiple
upstream paths. The state transition and unique key must be persisted atomically
before another candidate may claim that target.

Implementations must treat the `idempotency_key` as unique. It is the lowercase
SHA-256 of this UTF-8 string:

```text
trigger_type|trigger_id|target_type|target_id|resulting_state
```

Replaying the same trigger therefore returns the existing record rather than
creating another transition. A failure during propagation must be retried from
the first missing idempotency key; an implementation must not report the
correction as fully propagated while an affected dependant remains active.

### Deletion-safe audit minimum

CorrectionPatch and InvalidationRecord are identifiable audit records. They are
not exempt from a valid redaction or deletion request. If applicable law or a
documented security or dispute purpose requires limited retention, an
implementation may replace an identifiable record with an AuditTombstone. It
may also retain nothing when no valid basis exists.

The tombstone contains only a new audit-record identifier, action class, target
object type, coarse event date, outcome, enumerated retention basis, and a
mandatory purge date. It must not retain actor or target identifiers, source
references, free-text reasons, before/after values, content, evidence, model
metadata, network data, device data, or a reversible or pseudonymous subject
key. `audit_id` must be newly generated and opaque; it must not be derived from,
encode, or be reversible to a removed identifier. The purge date cannot precede
the event date and is a maximum, not a minimum, retention period. Retention
basis is limited to a statutory obligation, an active security incident, or an
active dispute; the implementation must have a documented basis at the time of
retention, but that documentation is not part of the tombstone.

An AuditTombstone proves only that a class of governance action occurred. It is
not authorization to resolve deleted content and cannot be used as model input.

## Data Sovereignty Impact

The affected user remains the authority over confirmation, rejection, rewrite,
and redaction of derived personal data.

## Privacy Impact

Evidence references must not grant access to evidence the viewer could not
otherwise access.

## AI Explainability Impact

This RFC makes model identity, evidence, limitations, and correction first-class.

## Compatibility

This is additive to the v0.1 draft schemas.

## Alternatives

A single free-text feedback field was rejected because it cannot express or
audit precise state transitions.

## Second Review Checklist

- [x] Define implementation-neutral propagation semantics for downstream
  derived objects, including representation, traversal, and idempotency.
- [x] Define the minimum deletion-safe audit metadata that may remain after a
  redaction or deletion request.
- [x] Add public schemas plus positive and negative conformance fixtures.
- [x] Complete a second public review and record a Steward decision.

Private implementation experiments are not normative until these requirements
are represented in the public schemas, fixtures, and validator.

## Steward Decision — 2026-09-04

**Accepted.** The second public review was made available through
[PR #15](https://github.com/FNB2026/fnb-open/pull/15), with scoped public
invitations to independent JSON Schema and data-protection practitioners. No
formal review or substantive public feedback was received. That absence did not
itself decide the RFC: under RFC-0000, the minimum discussion period elapsed and
the Steward completed a final adversarial review before this decision.

The final review found and resolved three acceptance blockers: redact
corrections now have a conforming invalidation reason; transitive idempotency
uses a stable parent key rather than an arbitrary record ID; and retention bases
are narrowed to statutory obligations, active security incidents, and active
disputes. This decision accepts only the implementation-neutral schemas,
fixtures, validator semantics, and requirements in this RFC. It does not accept
or publish private product implementation behavior.
