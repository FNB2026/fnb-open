# RFC-0004: Protocol Object Exchange Transport Binding

## Status

Draft — revised during the public comment window after review on
[PR #25](https://github.com/FNB2026/fnb-open/pull/25). Not accepted. The RFC
process requires a minimum 7-day comment window before a Steward decision
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

- an exchange envelope — a new protocol-level artifact;
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

- HTTP, `Content-Type: application/json`.
- Network deployments MUST use HTTPS/TLS. Local loopback and mock use MAY use
  plain HTTP, so that a local mock server is not born in violation of this
  binding.
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
    {
      "schema": "https://raw.githubusercontent.com/FNB2026/fnb-open/v0.1.0-preview.1/specs/v0.1/memory.schema.json",
      "object": { }
    }
  ]
}
```

- `transport_version` versions this binding.
- `protocol_release` names the frozen protocol release the objects are written
  against.
- `exchange_id` correlates a request with its receipt. It carries no user
  identity, no credential, and no idempotency meaning.
- `objects` is a non-empty list. Each entry carries one object and the identity
  of the schema it claims to satisfy.

### Identity of exchanged material

Two different kinds of reference appear in an exchange, and they must not be
conflated:

- **Schema identity.** Each envelope item MUST identify its schema by the exact
  canonical `$id` of the declared protocol release — for example
  `https://raw.githubusercontent.com/FNB2026/fnb-open/v0.1.0-preview.1/specs/v0.1/memory.schema.json`.
  A sender MUST NOT inline a copied, trimmed, or variant schema, and MUST NOT
  invent a local schema name that only the sender understands.
- **Object identity.** Object-to-object references inside protocol objects
  (`node_id`, `event_id`, `memory_id`, `source_ref`, and the like) retain their
  normal protocol identifiers and semantics. They are not schema identifiers, and
  this binding does not reinterpret them.

Pointing at the canonical `$id` is what makes "the same protocol release" a
verifiable claim rather than a label: the release tag pins the bytes.

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
outcome and no reason field: a bundle is accepted or rejected as a whole, and
nothing more. A machine-readable rejection reason is deliberately excluded,
because a receipt that explained which object failed would quickly become a
second conformance report, competing with the official runner for authority over
what "invalid" means.

### What `accepted` means, and what it does not

`accepted` means exactly this: the submitted protocol objects satisfy their
frozen schemas, and the cross-object protocol semantics that apply to the bundle
hold.

`accepted` does **not** mean that anything was stored, persisted, applied,
durably retained, or made visible to anyone. It says nothing about the
correctness of an AI inference, nothing about permission policy in a product, and
nothing about a user's intent.

Two consequences follow directly:

- **No partial acceptance in the first version.** Partial acceptance immediately
  implies product transaction semantics — which objects were written, which were
  not, whether a rollback happened, what a retry does. Those are product
  decisions, and the protocol has no business specifying them.
- **No idempotency key in the first version.** Because `accepted` carries no write
  and no side effect, there is no protocol-level transaction to deduplicate.
  `exchange_id` exists to correlate a request with its receipt, not to make
  delivery exactly-once.

### Transport-level failures

A transport-level failure is reported as an HTTP error with a Problem Details
(`application/problem+json`) body. A receipt MUST NOT be returned for it: a
receipt is a statement about objects, and the receiver cannot make a statement
about material it could not read or does not claim to support. Keeping the two
channels separate is the point.

Proposed first-version mapping:

| Condition | Status |
| --- | --- |
| Malformed JSON, or an envelope that does not match this binding | `400` |
| Unsupported `Content-Type` | `415` |
| Payload larger than the receiver accepts | `413` |
| `transport_version` not implemented by the receiver | `4xx` (see Open Questions) |
| `protocol_release` not implemented by the receiver | `4xx` (see Open Questions) |

Unsupported `transport_version` and unsupported `protocol_release` are both
transport-level failures: in neither case can the receiver judge the objects.

A receiver that declares support for a `protocol_release` declares support for
**every** schema frozen in that release. There is therefore no "supported release
but unsupported object kind" state, and no separate status for it: an unknown or
unexpected schema in a declared release is simply **protocol-invalid**, that is, a
`rejected` receipt. Only a whole unsupported release is a transport failure.

This binding sets no fixed bundle size or object-count limit. A receiver MAY
impose its own limit and report it as a transport-level failure; fixed limits are
deployment capacity, not FNB object semantics.

### No required closure over object references

This binding does **not** require a bundle to be closed under object-to-object
references. A receiver judges the material it is given, and co-presence is
required only where a normative cross-object invariant itself requires two
objects to appear together. Requiring general closure would make single-object
exchange nearly impossible and would move bundle-composition policy into the
protocol.

### One implementation of the judgement

A receiver's acceptance judgement must be the same judgement the public
conformance suite already codifies: schema validity plus the object-level and
cross-object invariants, using the same frozen schemas from the same release.
Protocol semantics are implemented once, in the public suite; the transport
carries the material and reports the outcome.

### Versioning and the publication boundary

`transport_version` and `protocol_release` are versioned independently. A change
to the transport must not be reported as a change to the protocol, and a new
protocol release must not silently change the transport.

A `transport_version` must be as durable as a protocol release. This repository
already treats the protocol release as an immutable publication boundary — tag,
canonical `$id`s, and a byte-exact digest manifest. A transport binding must not
fall back to a weaker standard:

> Once a transport binding version is published, its normative transport
> artifacts MUST NOT be replaced in place. Any normative change requires a new
> transport version and a new immutable publication boundary.

The mechanism for that boundary is deliberately not fixed by this RFC: a
dedicated transport tag, a digest manifest over transport artifacts, or reuse of
the protocol release machinery are all acceptable. What is fixed here is the
requirement, so that a later OpenAPI preview cannot land on mutable `main` while
calling itself `1.0`.

### Where the OpenAPI will live

If this RFC is accepted, the OpenAPI preview should be published under `specs/`,
proposed as:

```text
specs/openapi/object-exchange/v1/openapi.yaml
```

`specs/` is already covered by the authoritative license matrix as Apache-2.0, so
a new path under it does not raise a fresh licensing question of the kind an
unlisted new directory would. Publishing the file is not the same as publishing
the version: the publication boundary in the previous section still applies.

## Data Sovereignty Impact

Positive, and deliberately limited:

- The binding is receiver-side and opt-in. It defines no client, no discovery, no
  service registry, and no implicit sharing.
- The envelope carries no identity, no credential, and no account reference, so a
  transported bundle cannot by itself be attributed to a person.
- Because `accepted` explicitly excludes persistence, a receipt cannot be
  mistaken for evidence that user data was stored anywhere.
- The absence of an idempotency key and of partial acceptance keeps the protocol
  out of decisions about what a receiver retains; those remain product decisions
  under the receiver's own data-sovereignty obligations.
- Objects remain governed by the provenance and permission objects already in the
  protocol; the transport does not weaken or reinterpret them.

## Privacy Impact

- No accounts, no authentication, and no session concept are in scope, so the
  binding defines no place to accumulate identifying state.
- The receipt contains no object content and no per-object detail, so it is not a
  side channel for data the sender did not already have. Problem Details bodies
  must likewise not echo object content — a failure message about a malformed
  envelope must not quote the envelope.
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
- The envelope and receipt are transport-level artifacts, not domain objects, and
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
4. **A per-object status list in the receipt.** Rejected for v1, for the same
   reason as partial acceptance: it is a conformance report in disguise.
5. **A machine-readable rejection reason in v1.** Rejected. It would compete with
   the official runner for authority over what "invalid" means.
6. **An idempotency key in v1.** Rejected. `accepted` implies no write, so there is
   no protocol-level transaction to deduplicate.
7. **Requiring bundle closure over object references.** Rejected. It would make
   single-object exchange nearly impossible and move composition policy into the
   protocol.
8. **A separate status for unsupported object kinds.** Rejected. A receiver that
   declares a release declares all of it; partial implementation is an incomplete
   implementation, and an unknown schema is protocol-invalid.
9. **One endpoint per object type.** Rejected. That describes a product API
   surface and invites endpoint design to drift into the protocol.
10. **A fixed protocol-level bundle limit.** Rejected. Capacity belongs to
    deployments; a receiver that must limit reports it as a transport failure.
11. **Realtime or streaming first.** Rejected as premature; messaging is a product
    concern.
12. **Reuse the implementation adapter contract as the transport.** Rejected. That
    contract is a process-local black-box interface for testing, not a network
    binding; conflating them would make the test harness a protocol dependency.

## Open Questions

1. **Problem Details vocabulary.** Which `type` URIs identify the transport-level
   failures above, and should unsupported `transport_version` and unsupported
   `protocol_release` be distinguishable by `type`? The status codes for those
   two are still to be pinned.
2. **The mechanism for the transport publication boundary.** A dedicated
   transport tag, a digest manifest over transport artifacts, or reuse of the
   protocol release machinery? This RFC fixes the requirement and leaves the
   mechanism to the OpenAPI preview.
3. **What a future transport version may add.** Partial acceptance or a
   per-object status, if ever, would need a demonstrated need and a fresh RFC.
   Confirm that deferring them is acceptable rather than leaving them unstated.
