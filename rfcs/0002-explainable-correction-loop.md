# RFC-0002: Explainable Correction Loop

## Status

Revision — the first Steward decision was recorded 2026-07-26 after
[public review #5](https://github.com/FNB2026/fnb-open/discussions/5).
This revision proposes downstream invalidation and deletion-safe audit
semantics for a second public review; it is not Accepted until that review
closes with a new Steward decision.

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

Each affected object receives one append-only InvalidationRecord. Direct
records use `trigger_type: correction_patch`; transitive records use
`trigger_type: parent_invalidation` and identify the immediately preceding
InvalidationRecord. Processing is deterministic:

1. enumerate direct dependants in ascending `(target_type, target_id)` order;
2. emit one record per dependant with `resulting_state: invalidated`;
3. repeat for each newly invalidated dependant until no active dependant
   remains.

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
key. The purge date cannot precede the event date and is a maximum, not a
minimum, retention period.

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
- [ ] Complete a second public review and record a Steward decision.

Private implementation experiments are not normative until these requirements
are represented in the public schemas, fixtures, and validator.
