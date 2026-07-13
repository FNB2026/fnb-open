# v0.1 Draft Changelog

The v0.1 protocol remains unstable. This changelog makes draft-breaking changes
visible during public review.

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
