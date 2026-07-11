# FNB Public Release Boundary

This file defines what is public today, what may become public later, and what
must never be published. The current `fnb-open` repository is a public
documentation and protocol-draft repository; it is not the official product
source-code release.

## Public Now

- Manifesto (EN + ZH)
- Domain model documentation
- Protocol drafts
- Synthetic examples (no real data)
- Community governance (CoC, Contributing, Governance, Security)
- Public roadmap
- Draft JSON Schemas for implementation-neutral domain objects
- Synthetic end-to-end protocol chains
- Draft RFCs for public discussion

## Planned Public Later (Phase 2+)

- Additional JSON Schema definitions and versioned conformance rules
- OpenAPI preview (public API surface only)
- TypeScript SDK
- Go SDK
- Mock server with synthetic data
- Synthetic importer
- Plugin starter

## Not Public Before Beta Readiness

- Official Go backend implementation
- Official mobile app (iOS/Android)
- Official web console
- App authentication internals
- Worker credential internals
- Storage sync production implementation
- Ledger / Credit production logic
- Real user data import pipeline
- Real deployment scripts
- Real CI/CD configurations with secrets

## Never Public

- Real user data of any kind
- Real chat logs, conversations, or messages
- Real photos, images, audio recordings, or videos
- Real contact lists or relationship graphs
- Real private keys or signing keys
- Production secrets, API keys, or tokens
- Private infrastructure topology or network maps
- Internal review documents with real data references
