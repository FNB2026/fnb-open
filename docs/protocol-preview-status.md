# Protocol Preview Status

FNB's public protocol preview is now in **v0.1 Draft**. It is intentionally
smaller than the private product implementation.

## Published in this preview

- Implementation-neutral JSON Schemas under `specs/v0.1/`
- A synthetic FlowEvent → Node → AIInference → BlockDraft → Correction → Block chain
- Initial RFCs covering confirmation, explainability, and source provenance

## Deliberately excluded

- Authentication internals and worker credentials
- Administrative and private product endpoints
- Production storage, ledger, deployment, and network topology
- Real user data or examples derived from real conversations
- Unimplemented research objects presented as stable protocol contracts

## Next gates

1. Complete [public review #5](https://github.com/FNB2026/fnb-open/discussions/5)
   of names, identifiers, lifecycle states, provenance, and invalidation semantics
2. Keep schema, example, cross-reference, and negative-fixture validation green
3. Revise or accept RFC-0001 through RFC-0003 after the review window
4. Publish a deliberately narrow OpenAPI preview
5. Generate a TypeScript SDK preview from reviewed public schemas

The current review opened on 2026-07-13 and cannot close before 2026-07-20.
Private product changes are not copied into this preview while they remain
uncommitted or implementation-specific.

Draft schemas may change incompatibly until an RFC promotes them to a stable
version.
