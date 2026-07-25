# RFC-0002: Explainable Correction Loop

## Status

Revision — Steward decision recorded 2026-07-26 after
[public review #5](https://github.com/FNB2026/fnb-open/discussions/5);
downstream invalidation and deletion-safe audit semantics require another
reviewed revision before acceptance

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

## Revision Requirements

- Define implementation-neutral propagation semantics for downstream derived
  objects, including how invalidation is represented and audited.
- Define the minimum deletion-safe audit metadata that may remain after a
  redaction or deletion request.
- Add positive and negative conformance fixtures for the selected semantics.

Private implementation experiments are not normative until these requirements
are represented in the public schemas, fixtures, and validator.
