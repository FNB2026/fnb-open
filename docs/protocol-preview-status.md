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

1. Public review of names, identifiers, and lifecycle states
2. Schema validation and cross-file conformance fixtures
3. A deliberately narrow OpenAPI preview
4. TypeScript SDK preview generated from accepted public schemas

Draft schemas may change incompatibly until an RFC promotes them to a stable
version.
