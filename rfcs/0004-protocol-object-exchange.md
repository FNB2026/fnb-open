# RFC-0004: Protocol Object Exchange Transport Binding

## Status

Draft — open for public discussion. Not accepted. The RFC process requires a
minimum 7-day comment window before a Steward decision
(see [RFC-0000](./0000-rfc-process.md)).

## Summary

Define a deliberately narrow transport binding for moving FNB protocol objects
between independent implementations: HTTP plus JSON, one request shape, one
response shape, and one explicit statement of what "accepted" means.

This RFC defines **exchange semantics only**. It introduces no product
behaviour, no authentication, and no other product surface. It does not define
an FNB service.

## Motivation

The repository can now do three things it could not before: it publishes frozen
schemas, it generates bindings from them, and it can judge a third-party
implementation through the official conformance runner. What it still cannot do
is let two independent implementations exchange objects with a shared, published
meaning for the outcome.

That step needs normative content, not just a document format:

- an exchange envelope — a new protocol-level object;
- a receipt — a second one;
- and a definition of what accepting or rejecting a bundle *means*.

Under [RFC-0000](./0000-rfc-process.md), new or modified protocol objects and
significant architectural changes require an RFC. Writing the envelope and the
receipt directly into an OpenAPI document would make that YAML the place where
protocol semantics are decided, bypassing review. So the semantics are settled
here first, and a later OpenAPI preview is expected to implement this RFC
without adding any.

There is no existing OpenAPI, Swagger, or exchange transport in this repository,
so the binding can start from governance semantics rather than from history.

## Design

### Scope

In scope: how a batch of protocol objects is transmitted, how the receiving side
reports protocol-level acceptance, and how the two sides agree on versions.

Out of scope, explicitly: authentication, sessions, tokens, accounts, ACL
implementation, storage, database schema, transactions, rollback, synchronisation
strategy, messaging or realtime transports, workers, ledger or credit logic,
administration, deployment, and any FNB private backend route. Nothing in this
binding describes how FNB products work.

### Transport

- HTTP over TLS, `Content-Type: application/json`.
- One endpoint for the first version: `POST /exchange`.
- The request body is an `ObjectExchangeEnvelope`; the response body is an
  `ObjectExchangeReceipt`.
- The binding is implementation-neutral: it specifies the wire shape and the
  meaning of the outcome, not any particular server.

### Envelope

```json
{
  "transport_version": "1.0",
  "protocol_release": "v0.1.0-preview.1",
  "exchange_id": "fnb_exchange_...",
  "objects": [
    { "schema": "memory.schema.json", "object": { } }
  ]
}
```

- `transport_version` versions this binding.
- `protocol_release` names the frozen protocol release the objects are written
  against.
- `exchange_id` correlates a request with its receipt. It carries no user
  identity and no credential.
- `objects` is a non-empty list. Each entry names a frozen schema by its
  canonical file name and carries one object.
- Object references inside the objects must use the frozen canonical schema
  identifiers under the release's tag namespace. A sender must not inline a
  copied or variant schema.

### Receipt

```json
{
  "transport_version": "1.0",
  "protocol_release": "v0.1.0-preview.1",
  "exchange_id": "fnb_exchange_...",
  "status": "accepted"
}
```

`status` is `accepted` or `rejected`. The first version defines no partial
outcome: a bundle is accepted or rejected as a whole.

### What `accepted` means, and what it does not

`accepted` means exactly this: the submitted protocol objects satisfy their
frozen schemas, and the cross-object protocol semantics that apply to the bundle
hold.

`accepted` does **not** mean that anything was stored, persisted, applied,
durably retained, or made visible to anyone. It says nothing about correctness of
an AI inference, nothing about permission policy in a product, and nothing about
a user's intent.

The reason partial acceptance is excluded from the first version is that it
immediately implies product transaction semantics — which objects were written,
which were not, whether a rollback happened, what a retry does. Those are product
decisions, and the protocol has no business specifying them.

### One implementation of the judgement

A receiver's acceptance judgement must be the same judgement the public
conformance suite already codifies: schema validity plus the object-level and
cross-object invariants, using the same frozen schemas from the same release.
Protocol semantics are implemented once, in the public suite; the transport
carries the material and reports the outcome.

### Versioning

`transport_version` and `protocol_release` are versioned independently. A change
to the transport must not be reported as a change to the protocol, and a new
protocol release must not silently change the transport.

A request whose `protocol_release` the receiver does not implement, or whose
`transport_version` the receiver does not implement, is a **transport-level
failure**, not a protocol rejection: the receiver cannot make a statement about
objects it cannot read. Such a request fails before any object is judged, and the
receipt shape above is not the right way to report it (see Open Questions).

### Where the OpenAPI will live

If this RFC is accepted, the OpenAPI preview should be published under `specs/`,
proposed as:

```text
specs/openapi/object-exchange/v1/openapi.yaml
```

`specs/` is already covered by the authoritative license matrix as Apache-2.0, so
a new path under it does not raise a fresh licensing question of the kind an
unlisted new directory would.

## Data Sovereignty Impact

Positive, and deliberately limited:

- The binding is receiver-side and opt-in. It defines no client, no discovery, no
  service registry, and no implicit sharing.
- The envelope carries no identity, no credential, and no account reference, so a
  transported bundle cannot by itself be attributed to a person.
- Because `accepted` explicitly excludes persistence, a receipt cannot be
  mistaken for evidence that user data was stored anywhere.
- Objects remain governed by the provenance and permission objects already in the
  protocol; the transport does not weaken or reinterpret them.

## Privacy Impact

- No accounts, no authentication, and no session concept are in scope, so the
  binding defines no place to accumulate identifying state.
- The receipt contains no object content and no per-object detail in the first
  version, so it is not a side channel for data the sender did not already have.
- This RFC does not require or forbid request logging. Whether a receiver keeps
  transport logs is a product decision, outside this binding.

## AI Explainability Impact

Neutral to slightly protective. `AIInference` objects already carry model
identity, evidence references, and a human-readable explanation, and those
obligations travel with the objects. A receipt is about protocol acceptability
only: `accepted` must not be read as "the AI was right", and it does not replace
user confirmation of an AI proposal.

## Compatibility

- Additive. No frozen schema changes, no change to any accepted RFC, and no
  change to the release bundle or its digest manifest.
- The envelope and receipt are transport-level objects, not domain objects, and
  are deliberately not added to `specs/v0.1/`.
- If accepted, the OpenAPI preview is expected to implement this RFC exactly. It
  must not introduce new semantics; anything it needs beyond this text requires a
  further RFC.
- A transport binding that arrived before this RFC would have broken backward
  compatibility in the worst way: by making an implementation detail the de facto
  protocol.

## Alternatives

1. **Write the OpenAPI preview directly, without an RFC.** Rejected. It would let
   a document format define protocol semantics without review, which is exactly
   what the RFC process exists to prevent.
2. **A bare list of objects, with no envelope.** Rejected. No version agreement,
   no correlation, and no place to record the protocol release being used.
3. **Partial acceptance in v1.** Rejected. It drags product transaction semantics
   into the protocol.
4. **One endpoint per object type.** Rejected. That describes a product API
   surface and invites endpoint design to drift into the protocol.
5. **Realtime or streaming first.** Rejected as premature; messaging is a product
   concern.
6. **Reuse the implementation adapter contract as the transport.** Rejected. That
   contract is a process-local black-box interface for testing, not a network
   binding; conflating them would make the test harness a protocol dependency.

## Open Questions

1. **How is a transport-level failure reported?** The proposal above is that an
   unsupported `transport_version` or `protocol_release`, or a malformed
   envelope, fails at the transport layer rather than producing a receipt. Should
   that be an HTTP status, a documented error body, or both?
2. **Should a receipt ever carry a reason?** The first version carries only a
   status. A machine-readable rejection reason would help senders, but it risks
   becoming a de facto conformance report; if it is added, which vocabulary?
3. **Is an idempotency key needed on the envelope?** Retries are a transport
   concern, but a duplicate delivery could be judged twice.
4. **Bundle size and object count limits.** Should the binding state limits, or
   leave them to implementations?
5. **Must object references resolve within the same bundle?** For example, does a
   `Memory` that cites a `Node` require that `Node` in the same exchange?
6. **Does `rejected` need to distinguish "protocol-invalid" from "unsupported
   content"?** These are different failures and may deserve different handling.
7. **Naming.** `ObjectExchangeEnvelope` and `ObjectExchangeReceipt` follow the
   repository's object naming style; confirm before they become frozen in a
   schema.
