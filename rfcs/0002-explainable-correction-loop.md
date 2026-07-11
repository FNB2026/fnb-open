# RFC-0002: Explainable Correction Loop

## Status

Draft

## Summary

Require AI-derived proposals to expose evidence and provide confirm, reject,
replace, and redact correction operations.

## Motivation

Confidence alone is not an explanation. Users need to see why a proposal exists
and must be able to correct it without erasing the audit trail.

## Design

AIInference records purpose, model identity, input references, output summary,
confidence, and lifecycle status. Explanation records a human-readable rationale,
evidence references, and known limitations. CorrectionPatch records the actor,
target, operation, reason, timestamp, and optional before/after values.

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

## Open Questions

- How should corrections propagate to downstream derived objects?
- Which redaction metadata may remain visible after deletion requests?
