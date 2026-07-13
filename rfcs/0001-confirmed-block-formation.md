# RFC-0001: Confirmed Block Formation

## Status

Discussion — [public review #5](https://github.com/FNB2026/fnb-open/discussions/5),
opened 2026-07-13; decision no earlier than 2026-07-20

## Summary

Define the public FlowEvent → Node → BlockDraft → Block path and require an
explicit user decision before an AI proposal becomes a confirmed Block.

## Motivation

AI may organize evidence, but it must not silently convert an interpretation
into user-owned truth.

## Design

1. A FlowEvent preserves actor, time, source, and permission context.
2. One or more events produce candidate Nodes.
3. Confirmed Nodes may support an AIInference and BlockDraft.
4. The owner confirms, rejects, or rewrites the draft.
5. Only confirmation or an explicit rewrite creates a Block.

Every Block retains its source Node identifiers. An AI-derived Block must retain
the identifier of the BlockDraft that the user confirmed or rewrote. Rejection
remains auditable and does not create a Block.

## Data Sovereignty Impact

The owner controls the transition from proposal to durable Block.

## Privacy Impact

Implementations must apply the source permission snapshot when producing and
displaying derived objects.

## AI Explainability Impact

AI-created drafts must reference an AIInference and its evidence.

## Compatibility

This is the first public draft and may change during v0.1 review.

## Alternatives

Automatic Block creation was rejected because it turns model output into fact
without user agency.

## Open Questions

- Should low-risk local-only drafts support batched confirmation?
- What minimum rejection record is required for conformance?
