# Architecture Overview

FNB is a **local-first personal memory operating system** organized around four layers.

## Layer 0: Storage & Identity

- PostgreSQL with UUIDv7 primary keys
- Public FNB ID for external identity
- Content hashing for integrity verification
- Version hashing for change tracking
- Ledger-based audit log (planned)

## Layer 1: Domain Model

The core object model is built around:

```
Flow — continuous event stream / runtime
  └── Event — atomic operation record
      └── Node — stable actor, entity, or message
          └── Block — aggregated state, knowledge, or asset
```

Supporting objects:

- **Memory** — curated, scored, source-tracked artifacts
- **Asset** — file/media with variants and processing jobs
- **Relationship** — evidence-backed connections between actors
- **Permission** — role-based access with policy overrides
- **AuditLog** — append-only operation history

## Layer 2: AI & Inference

- **AIInference** — structured record of every model judgment (model, input, output, confidence, evidence)
- **Explanation** — human-readable rationale for AI decisions
- **Correction/Patch** — user-controlled fix mechanism with full audit
- **BlockDraft** — AI-generated proposals that require user confirmation (planned)

## Layer 3: Application

- **IM** — real-time messaging as relationship data generator
- **Import** — chat, Markdown, photo import pipelines
- **Web console** — operator and administration interface
- **Mobile app** — iOS/Android user application

## Design Principles

1. **Local-first** — all core functions work offline; cloud is optional sync
2. **User-owned** — data belongs to the user, not the platform
3. **Auditable** — every operation leaves a trace
4. **Explainable** — every AI judgment has a human-readable rationale
5. **Correctable** — users can confirm, reject, or rewrite any AI-generated content
6. **Extensible** — plugin architecture for import, export, storage, and AI adapters
