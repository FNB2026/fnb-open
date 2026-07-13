# v0.1 Draft Changelog

The v0.1 protocol remains unstable. This changelog makes draft-breaking changes
visible during public review.

## 2026-07-13 — Conformance baseline

- Split Memory user-confirmation `status` from retention `lifecycle_state`.
- Standardized the proposed Memory state name as `candidate` rather than `suggested`.
- Added `Block.creation_mode` and require `draft_id` for `ai_derived` Blocks.
- Added executable schema, example, cross-reference, and negative-fixture checks.

These changes tighten the existing sovereignty rules; they do not claim wire
compatibility with the private product implementation.
