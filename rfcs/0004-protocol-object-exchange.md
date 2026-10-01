# RFC-0004: Protocol Object Exchange Transport Binding

## Status

Revision — the first public comment window on
[PR #25](https://github.com/FNB2026/fnb-open/pull/25) has completed. The
2026-10-01 final review requires further revision before acceptance; see the
Steward Decision and Revision Requirements below. This RFC is not Accepted.
The review follows [RFC-0000](./0000-rfc-process.md).

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
- The request body is an `ObjectExchangeEnvelope`; a completed judgement returns
  an `ObjectExchangeReceipt`, while transport/evaluation errors return Problem
  Details as specified below.
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
  ],
  "validation_contexts": []
}
```

- `transport_version` versions this binding.
- `protocol_release` names the frozen protocol release the objects are written
  against.
- `exchange_id` correlates a request with its receipt. This binding gives it no
  authenticated identity, credential, or idempotency meaning; senders SHOULD NOT
  place personal data in it.
- `objects` is a non-empty list. Each entry carries one object and the identity
  of the schema it claims to satisfy.
- `validation_contexts` is an array of explicit, complete chain descriptions,
  defined below. An empty array permits standalone-object exchange; it does not
  claim that an unsubmitted history or graph was validated.

The envelope MUST be a JSON object with exactly these five members. The three
version/correlation fields MUST be non-empty strings; whitespace is significant
and MUST NOT be trimmed or case-folded. Every `objects` entry MUST have exactly
`schema` (a non-empty string) and `object` (a JSON object). Context shapes are
specified below. Unknown envelope, entry, or context members are envelope errors.
Unknown members *inside* a protocol object are judged by its frozen schema,
not by the envelope grammar.

Bodies MUST be UTF-8 JSON, with no duplicate member names at any nesting level
and no non-JSON numeric literals such as `NaN` or `Infinity`. A receiver MUST
reject these ambiguities rather than use a parser's first/last-value preference.
`application/json` with no parameters, or with only `charset=utf-8`, is supported
(media type and charset matching are case-insensitive). Other media types,
parameters, or non-identity content encodings receive `415`. An absent
`Content-Encoding` or `identity` is supported. Invalid UTF-8 or JSON receives
`400`; a well-formed `object: {}` reaches protocol validation and is rejected,
not treated as unreadable JSON.

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

Both outcomes MUST use HTTP `200` and `Content-Type: application/json`. A receipt
MUST contain exactly the four members shown above. Its three correlation/version
strings MUST equal the request's decoded strings exactly; the receiver MUST NOT
substitute its preferred version, normalise the exchange ID, or issue a receipt
for an unsupported version. An HTTP success alone is not protocol acceptance:
clients MUST inspect `status` and verify all three echoed strings.

### What `accepted` means, and what it does not

`accepted` means exactly this: every submitted object passes its frozen schema
and public object-level rules, every direct co-presence check enumerated below
passes, and every declared validation context passes the corresponding public
chain rules. Duplicate identities and unresolved context roles are rejected.

This is a deliberately bounded **exchange-validation profile**, not a claim
that all possible relationships in a flat list or an external history were
checked. Full chain checks require an explicit context. Receivers MUST NOT
infer missing contexts, select historical snapshots by proximity or recency,
or strengthen this profile using private product policy. This narrowing of
the earlier implicit whole-graph promise is a substantive review item.

`accepted` does **not** mean that anything was stored, persisted, applied,
durably retained, or made visible to anyone. It says nothing about the
correctness of an AI inference, nothing about permission policy in a product, and
nothing about a user's intent.

Two consequences follow directly:

- **No partial acceptance in the first version.** Partial acceptance immediately
  implies product transaction semantics — which objects were written, which were
  not, whether a rollback happened, what a retry does. Those are product
  decisions, and the protocol has no business specifying them.
- **No idempotency key in the first version.** Because `accepted` makes no
  statement about writes or side effects, this binding defines no
  protocol-level transaction to deduplicate.
  `exchange_id` exists to correlate a request with its receipt, not to make
  delivery exactly-once.

### Transport-level failures

A transport-level failure is reported as an HTTP error with a Problem Details
(`application/problem+json`) body. A receipt MUST NOT be returned for it: a
receipt is a statement about objects, and the receiver cannot make a statement
about material it could not read or does not claim to support. Keeping the two
channels separate is the point.

The following mapping is normative for binding `1.0`. Each problem `type` is
the exact absolute URI formed by appending its suffix to
`https://www.fnbapp.net/problems/object-exchange/1.0/`. These are proposed stable
identifiers, not a claim that documentation endpoints are already deployed.
Their definitions MUST be included in the immutable transport publication;
consumers MUST NOT fetch them as part of validation.

| Condition | HTTP status | Type suffix | Title |
| --- | --- | --- | --- |
| Invalid UTF-8/JSON or envelope grammar | `400` | `malformed-envelope` | Malformed exchange envelope |
| Unsupported media type, parameters, or content encoding | `415` | `unsupported-media-type` | Unsupported exchange representation |
| Receiver byte or object-count limit exceeded | `413` | `payload-too-large` | Exchange payload too large |
| Unsupported `transport_version` | `400` | `unsupported-transport-version` | Unsupported transport version |
| Unsupported `protocol_release` | `400` | `unsupported-protocol-release` | Unsupported protocol release |
| Receiver cannot reliably evaluate a supported release | `500` | `evaluation-failure` | Exchange evaluation unavailable |

Problem bodies MUST contain string `type`, string `title`, and integer `status`;
the latter MUST equal the actual HTTP status. Receivers MUST use the type and
title in this table. An optional string `detail` MAY provide a generic
explanation, but MUST NOT echo object contents, identifiers, request bodies,
local paths, secrets, or stack traces. Binding `1.0` emits no other problem
members, including no receipt fields or per-object errors. Clients identify
problems by `type`, not by parsing human-readable text, and ignore unrecognised
extension members as required by
[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html).

Receivers check representation, JSON parsing, envelope grammar, transport
support, and protocol-release support in that order, then evaluate the supported
material. The first failed stage determines the response. Capacity enforcement
MAY abort earlier with `413`; object-count limits can be checked after decoding
`objects`. An internal exception, timeout, unavailable validator, or a missing
or corrupt local release manifest/schema set MUST produce `evaluation-failure`,
never an `accepted` or `rejected` receipt. The receiver MUST verify the supported
release's exact schema set and byte-exact digest manifest before evaluation;
verified local immutable material MAY be cached. Schema identifiers are resolved
against that local set, never by fetching a sender-provided URL.

These rules apply to requests reaching `POST /exchange`. Routing, TLS, proxies,
and infrastructure may fail before the binding is reached; their errors or a
missing response are not receipts. This RFC adds no other routes or methods.
Clients SHOULD send `Accept: application/json, application/problem+json`; the
binding uses the two defined representations without content negotiation. HTTP
codes retain their meanings under
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html); `400` for an unsupported
binding or protocol version is not HTTP `505` (HTTP-version support).

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

This binding does **not** require general closure under object references.
An absent external reference is not itself a rejection. Explicit context roles,
however, MUST all resolve inside this envelope: a declared full-chain check
cannot silently degrade into a standalone-object check. No receiver-private
storage, network lookup, or implicit fixture is part of the judgement.

### Deterministic exchange-validation profile

For `protocol_release: v0.1.0-preview.1`, receivers MUST apply the following
algorithm. A future release needs a published release-specific profile; a
receiver MUST NOT reuse this profile under a new release label automatically.

1. Validate every object's schema identity against the declared release, then
   its frozen schema (including formats) and public object-level rules. These
   include inference evidence membership, relationship participant attribution,
   invalidation key derivation, tombstone chronology, snapshot expiry, and the
   source-state transition matrix. Any failure produces a `rejected` receipt.
2. Index objects by `(canonical schema $id, identity field value)` using exact
   decoded string equality. The identity-field table below is exhaustive. A
   repeated pair MUST reject the bundle, even if both objects are identical.
   Receivers MUST NOT deduplicate, merge, or select the first/last occurrence.
   Equal identifiers under different schemas are different typed identities.
3. Apply every direct co-presence check in the table below, regardless of whether
   a context mentions those objects. A missing target skips that direct check
   only; it does not satisfy a context that requires the target. No unlisted
   inference from an ambiguous reference is permitted.
4. Resolve and validate every explicit context. Each role selects exactly one
   typed identity, never the first object of that schema or a positional guess.
   Every role is required and MUST resolve. Run all contexts, including when
   the same object participates in more than one; failure of any rejects the
   whole bundle. No objects or contexts have to be generated by the receiver.
5. Return `accepted` only if all preceding checks completed successfully.

Each schema below means its exact canonical `$id` under the declared release's
`specs/v0.1/` prefix, not the abbreviated filename on the wire.

| Schema filename | Identity field |
| --- | --- |
| `actor.schema.json` | `actor_id` |
| `ai-inference.schema.json` | `inference_id` |
| `asset.schema.json` | `asset_id` |
| `audit-tombstone.schema.json` | `audit_id` |
| `block-draft.schema.json` | `draft_id` |
| `block.schema.json` | `block_id` |
| `correction-patch.schema.json` | `correction_id` |
| `flow-event.schema.json` | `event_id` |
| `invalidation-record.schema.json` | `invalidation_id` |
| `memory.schema.json` | `memory_id` |
| `node.schema.json` | `node_id` |
| `permission-snapshot.schema.json` | `permission_snapshot_id` |
| `relationship.schema.json` | `relationship_id` |
| `source-state-change.schema.json` | `source_change_id` |

| Direct reference selector | Checks when both typed objects are present |
| --- | --- |
| Block `draft_id` → BlockDraft `draft_id` | Equal `owner_id`, `block_type`, and ordered `source_node_ids`; draft status is `confirmed` or `rewritten`; Block `confirmed_by_actor_id` equals its owner; confirmed draft requires `confirmation_operation: confirm`, rewritten draft requires `rewrite`. |
| Block `correction_id` → CorrectionPatch `correction_id`, for a Block with `confirmation_operation: rewrite` and `draft_id` | Correction targets that `block_draft`, is by the Block owner, uses `replace` at `/proposed_summary`, and has `after` equal to Block `summary`; Block confirmation is not earlier than the correction. |
| InvalidationRecord `parent_invalidation_id` → InvalidationRecord `invalidation_id`, when `trigger_type: parent_invalidation` | Parent occurs earlier in `objects`; child `trigger_id` equals parent `idempotency_key`. |
| InvalidationRecord `trigger_id` → SourceStateChange `source_change_id`, when `trigger_type` is `source_change` or `permission_change` | Apply the RFC-0003 state-to-trigger/reason/result mapping below. |

For the last row: `redacted` requires `source_change / source_redacted /
invalidated`; `deleted` requires `source_change / source_deleted / invalidated`;
`permission_withdrawn` requires `permission_change / permission_withdrawn /
invalidated`; `stale` requires `source_change / source_stale` and either
`invalidated` or `review_required`. An `active` change MUST NOT have such a
linked invalidation. The slash-separated values are respectively trigger type,
reason code, and resulting state, not new object fields.

These are applications of existing public rules to explicitly identified
co-present objects, not permission grants, generation algorithms, or a claim of
exhaustive graph validation. In particular, `source_ref` alone does not choose
a historical PermissionSnapshot; `confirmation_event_id` is not assumed to
identify the FlowEvent used to generate a draft. Other references remain
external unless a context names their roles.

### Explicit validation contexts

Each `validation_contexts` element MUST be an object with exactly `kind` and
`roles`. `kind` MUST be one of the three names below; `roles` MUST have exactly
the listed members. A role value is a non-empty string containing the selected
object's identity field value. The role name supplies its schema, so a sender
cannot substitute a different type with the same identifier. `records` alone
is a non-empty array of non-empty strings, without repeated identifiers.
Unknown kinds, extra/missing roles, or incorrectly typed role values are
`malformed-envelope`; well-formed selectors whose objects are absent are
protocol-invalid and receive a `rejected` receipt.

| Kind | Required roles (each role → schema filename stem) |
| --- | --- |
| `protocol_chain` | `flow_event` → flow-event; `node` → node; `ai_inference` → ai-inference; `block_draft` → block-draft; `correction` → correction-patch; `block` → block |
| `source_state_chain` | `permission_snapshot` → permission-snapshot; `source_state_change` → source-state-change; `invalidation` → invalidation-record |
| `invalidation_chain` | `records` → ordered array of invalidation-record identities |

For example, a context entry can be
`{"kind":"invalidation_chain","roles":{"records":["fnb_inv_root","fnb_inv_child"]}}`.
These illustrative selectors supply no object contents or expected verdict.
For each context, the receiver materialises the existing named public chain
shape and applies that chain's frozen public rules. The rules are codified in
`validate_protocol_chain_instance`, `validate_source_state_chain_instance`, and
`validate_invalidation_chain_instance` in
[the release-pinned public validator](https://github.com/FNB2026/fnb-open/blob/v0.1.0-preview.1/tools/validate-public-artifacts.py). Independent
implementations reproduce the rules; executing Python is not required.

For a `protocol_chain`, Node sources include the selected FlowEvent; inference
inputs include that event and Node; the draft selects the inference; and the
Block selects the draft. Draft and Block owners, types, and ordered source Node
lists match, the correction targets the draft ID and is by its owner, and the
Block is owner-confirmed. Draft status is `confirmed` or `rewritten`, never
`pending` or `rejected`. Confirmed requires Block operation `confirm`; rewritten
requires `rewrite`, the selected correction's ID, `replace` at
`/proposed_summary`, and correction `after` equal to Block `summary`. Block
confirmation time is not earlier than correction creation time, which is not
earlier than the selected FlowEvent time. Datetime comparison uses instants,
not lexical string ordering. Arrays compare in order and JSON values compare
structurally, with object member order insignificant; strings compare exactly.
JSON numbers compare by mathematical value, without lossy floating-point
coercion. A receiver unable to evaluate a permitted value reliably MUST fail
evaluation rather than issue a potentially false receipt.

For a `source_state_chain`, the selected snapshot and change have equal
`source_ref`, the selected invalidation's `trigger_id` equals that change's ID,
and the state-to-invalidation mapping above holds. An `active` change cannot
form this three-object invalidation context. A standalone active change remains
allowed. No snapshot is selected implicitly from the other objects.

An invalidation context's `records` MUST preserve the relative order of those
records in `objects`. Parents MUST precede children; missing parent records,
repeated target `(target_type, target_id)` within that context, and invalid
parent-key linkage reject it under RFC-0002. Receivers MUST NOT sort a bad
submission into a good one. Distinct contexts may represent distinct historical
propagation runs and may invalidate the same target; this binding does not infer
run membership across them. Cycles cannot pass the earlier-parent requirement.
Other chain contexts use role selection rather than envelope order; the public
chronology checks still apply to their timestamps.

Multiple independent chains use multiple contexts. Objects may be interleaved;
ID-based role selection keeps the result independent of accidental array
position (except the explicit invalidation ordering rule). Standalone objects
need no context, and there is no obligation to declare every conceivable chain.
Omitting a context limits what was checked; it cannot bypass the mandatory
object and direct co-presence checks. A receipt has no context-coverage report
and MUST NOT be advertised as proof of complete lineage or historical closure.

### One implementation of the judgement

A receiver's acceptance judgement must follow the same rules the public
conformance suite codifies: schema validity plus the object-level and
cross-object invariants, using the same frozen schemas from the same release.
Independent implementations may implement these rules in their own languages;
the public suite supplies conformance evidence, not a required runtime
dependency. The release-specific exchange profile above defines selection and
coverage; it does not replace the official implementation compatibility report.
Future OpenAPI and mock tests MUST cover both that profile and the HTTP contract
before transport publication; existing repository CI does not test this new
wire contract merely by passing the older conformance suite.

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
- The envelope introduces no authenticated sender identity, credential, or
  account-system reference. The objects inside it can still carry actor and
  owner identifiers, identifying content, and sensitive provenance. A bundle
  can therefore be attributable to a person; the transport provides no
  anonymity guarantee.
- Because `accepted` explicitly excludes persistence, a receipt cannot be
  mistaken for evidence that user data was stored anywhere.
- The absence of an idempotency key and of partial acceptance keeps the protocol
  out of decisions about what a receiver retains; those remain product decisions
  under the receiver's own data-sovereignty obligations.
- Objects remain governed by the provenance and permission objects already in the
  protocol; the transport does not weaken or reinterpret them.

## Privacy Impact

- No account, authentication, or session mechanism is defined by this binding.
  Exchanged objects and transport logs can nevertheless contain identifying
  state. Protocol validity and an `accepted` receipt provide no authorization
  to disclose the material. A PermissionSnapshot remains point-in-time evidence
  under RFC-0003, not a credential or current-access grant.
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
6. **An idempotency key in v1.** Rejected. `accepted` specifies no write or
   side-effect guarantee, so this binding defines no protocol-level transaction
   to deduplicate.
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

1. **The mechanism for the transport publication boundary.** A dedicated
   transport tag, a digest manifest over transport artifacts, or reuse of the
   protocol release machinery? This RFC fixes the requirement and leaves the
   mechanism to the OpenAPI preview.
2. **What a future transport version may add.** Partial acceptance or a
   per-object status, if ever, would need a demonstrated need and a fresh RFC.
   Confirm that deferring them is acceptable rather than leaving them unstated.

## Revision Requirements

The following requirements must be resolved in the RFC before an OpenAPI
document can faithfully encode the binding. They are review requirements, not
newly accepted wire semantics.

- [x] **Complete the wire response contract in the revised proposal.** Specify the HTTP status and media
      type for both receipt outcomes, require the receipt to correlate with the
      request's exchange and versions, and resolve the status codes and `type`
      vocabulary for unsupported transport and protocol versions. Specify the
      envelope's required field types and treatment of unknown fields so that
      an OpenAPI schema does not choose those rules itself. Problem Details
      must follow [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), including
      consistency between its `status` and the HTTP status. HTTP status choices
      must respect [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html).
- [x] **Define deterministic bundle judgement in the revised proposal.** Specify how schema identities
      and object references select the applicable checks from a flat `objects`
      list, including multiple independent chains, repeated or conflicting
      object identities, and ordering of invalidation records. Resolve the
      boundary between allowed external references and checks that require
      co-present objects. The result must not depend on a receiver's private
      storage, arbitrary object pairing, or network resolution of references.
      Alternatively, narrow the promised acceptance semantics explicitly and
      review that scope change before acceptance.
- [x] **Correct identity and side-effect claims.** Objects can identify people;
      the absence of authentication fields supplies no anonymity or transfer
      authorization. A receipt supplies no persistence guarantee, which does
      not prohibit a product from having side effects outside this binding.
- [ ] **Expose the substantive revision for public review.** The above wire
      choices and bundle judgement rules must be available for review before
      the next Steward decision. Record the revision commit and review window
      rather than treating the initial comment period as review of choices
      that had not yet been specified.

Checked items record proposal completion, not Steward acceptance or executable
transport-test evidence. The new fifth envelope member, bounded acceptance
profile, direct checks, and explicit contexts all require public review.

The publication mechanism may remain an implementation-stage choice only if
it fulfils the immutable boundary requirement already stated here. Deferring
partial outcomes and per-object statuses to a future RFC is acceptable for this
scope and is not an acceptance blocker.

### Adversarial review cases

These are expected outcomes of the revised proposal, not newly implemented
fixtures or transport-test results. Assume supported versions, intact local
release material, and no capacity limit exceeded unless stated otherwise.

| Submission or condition | Required result |
| --- | --- |
| Schema-valid BlockDraft and its linked Block have different owners, no full chain context | `200`, `rejected`: mandatory direct check cannot be omitted. |
| Two valid complete chains interleaved, each selected by its own context | `200`, `accepted`: no first-object pairing. |
| Same typed object identity appears twice, identical or conflicting values | `200`, `rejected`: no deduplication or winner selection. |
| Co-present parent invalidation appears after its child | `200`, `rejected`: no receiver-side reordering. |
| Parent precedes child in objects but context records reverses them | `200`, `rejected`: context must preserve relative order. |
| Standalone child has an external parent, contexts empty | `200`, `accepted` if object-level rules pass; no complete propagation claim. |
| Context requires a parent or another role not in the envelope | `200`, `rejected`: declared contexts require their own closure. |
| Multiple snapshots share source_ref; context selects one consistent snapshot | Judge only that explicit context, not a guessed newest snapshot. |
| Independent invalidation contexts repeat a target with distinct record identities | Allowed if each context passes; one-run target uniqueness is context-local. |
| Unknown canonical schema string within a supported release | `200`, `rejected`, never unsupported-release. |
| Empty contexts and unrelated valid standalone objects | `200`, `accepted`, without exhaustive graph or lineage assurance. |
| Unknown context kind, missing role, extra envelope member, or object is not a JSON object | `400`, `malformed-envelope`. |
| Missing/unsupported transport or protocol version | Missing is `400` malformed; unsupported non-empty string is `400` with its distinct version type. |
| Corrupt supported release material or evaluation crash | `500`, `evaluation-failure`, never a receipt. |
| Receipt has a different exchange_id or versions | Client MUST reject it as uncorrelated, irrespective of `status`. |
| Duplicate JSON member anywhere, invalid UTF-8, or NaN | `400`, `malformed-envelope`, not parser-dependent protocol judgement. |

### Renewed public review

The normative completion on 2026-10-01 is a new proposal, not a retroactive
acceptance of the earlier text. It MUST be published on PR #25 with its exact
commit SHA and UTC publication timestamp. A renewed minimum seven-day review
starts at that publication, not at the original PR creation time. Its earliest
decision time is publication plus seven days; the PR publication record supplies
both timestamps without a self-referential commit hash in this file. Any further
substantive revision MUST identify what changed and renew the review window.

Review must explicitly cover the five-member envelope and the narrowed
acceptance/coverage claim, not just the Problem Details names. After the renewed
window, a final adversarial review and a new auditable Steward Decision are
required. Until then the RFC remains Revision, this PR remains unmerged, and no
OpenAPI, mock, generated SDK, or normative validation code is introduced.

## Steward Decision — 2026-10-01

**Revision required; not Accepted.** The first comment window began when
[PR #25](https://github.com/FNB2026/fnb-open/pull/25) opened at
2026-09-23 05:05:54 UTC and met the seven-day minimum at
2026-09-30 05:05:54 UTC. No PR-local comments or formal reviews were recorded at
the final review. That absence is not acceptance. The reviewed proposal was
commit `d31703f1514c7f3fa985333bbf5988f6ec6f4989`.

The final adversarial review found two blocking gaps: an incomplete HTTP/error
contract, and an unspecified projection from arbitrary exchange bundles to
cross-object checks. The current public validator accepts named, structured
protocol, source-state, and invalidation chains; it does not define that
projection for an arbitrary flat exchange list. Green repository CI therefore
does not establish that independent receivers can produce the same receipt for
every bundle allowed by this proposal.

The identity and side-effect claims have been corrected in this revision. The
scope and immutable publication requirement remain suitable, but acceptance
requires completion and review of the outstanding Revision Requirements. The
next step is a revised normative proposal on this PR, followed by a recorded
Steward decision. OpenAPI implementation and transport publication remain
gated on acceptance.
