# RFC-0003: Source Provenance and Permission Snapshots

## Status

Discussion — [public review #5](https://github.com/FNB2026/fnb-open/discussions/5),
opened 2026-07-13; decision no earlier than 2026-07-20

## Summary

Require derived memories and protocol events to preserve source references and
the permission context used when they were created.

## Motivation

A memory without provenance cannot be reliably explained, corrected, or
invalidated when its source changes.

## Design

FlowEvent carries a `source_ref` and may identify a permission snapshot. Memory
contains one or more MemorySource entries with source type and object ID. Derived
objects must not broaden the visibility of their sources. Implementations should
invalidate or review derived objects when a required source is redacted or loses
permission.

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

## Open Questions

- How should a portable permission snapshot be represented?
- When should source invalidation redact versus merely mark a derived object stale?
