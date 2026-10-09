# Object Exchange OpenAPI Preview

License: Apache-2.0. This directory implements the accepted
[RFC-0004](../../../../rfcs/0004-protocol-object-exchange.md); it introduces no
new protocol semantics or private product surface.

`openapi.yaml` is an OpenAPI 3.1.0 document in JSON-compatible YAML 1.2 syntax.
It describes only `POST /exchange`, without a production server URL or an
authentication scheme. Network deployments require TLS; local loopback/mock
use may use HTTP. No receiver, mock server, or transport SDK is supplied here.

The five-member envelope's schema validates **wire grammar**, not domain
validity. In particular, an unknown schema ID or a schema-invalid JSON object
is still a readable envelope and receives `200` with `status: rejected`.
Do not attach the 14 domain schemas as a request `oneOf`: that would turn
protocol rejection into a `400`. Component references expose all 14 exact
canonical schema IDs without copying frozen definitions. Version strings are
also grammatically non-empty, not enums, so unsupported-version errors remain
distinct from malformed envelopes.

JSON Schema cannot express duplicate JSON member detection, media/encoding
processing, local release integrity, cross-object checks, stage precedence, or
exact request-to-receipt correlation. The document records these obligations
in descriptions and `x-fnb-wire-requirements`; RFC-0004 remains authoritative.

## Offline checks

Install the existing hashed validation dependencies, then run:

```bash
python3 tools/object-exchange-contract.py
python3 -m unittest discover -s tests/conformance/transport -p 'test_*.py' -v
```

The contract probe is a **test-side evaluator**, not an FNB reference
implementation, a network service, or an implementation certification runner.
It uses only verified local schemas, existing public rules, and public synthetic
worlds. Tests check wire shapes against OpenAPI and mutate synthetic material
for independent expected outcomes. No private repository, production data,
product API, or network retrieval participates in these checks. No compatibility
report or claim of third-party interoperability is issued.

Tests cover schema-invalid versus malformed input, typed identity collisions,
mandatory direct checks without contexts, explicit role closure, interleaved
chains, external standalone references, historical snapshot selection, parent
ordering, context-local target uniqueness, version failures, capacity, media,
strict JSON, exact correlation, and fail-closed internal/integrity errors.
They are offline contract tests, not live HTTP framing/TLS tests. A later mock
must be built strictly from this contract plus public synthetic worlds.

## Immutable publication boundary

Wire version: `1.0`. Artifact preview: `1.0.0-preview.1`. Protocol release:
`v0.1.0-preview.1`. These three versions are not interchangeable.

The selected publication mechanism is a **separate annotated or signed tag**,
`object-exchange-v1.0.0-preview.1`, plus `artifact-digests.json`. The manifest
lists the exact byte lengths and SHA-256 digests of the OpenAPI document,
this guide, the accepted RFC, the contract probe, its tests, and the vendored
OpenAPI structural schema, together with both imported public rule/release
helpers, the hashed validation dependency lock, and the protocol digest manifest. This pins the probe's judgement
dependencies, not just its entry point. The manifest is pinned by the same tag and does not
hash itself. Protocol schemas remain pinned by their existing, unchanged tag
and digest manifest. Normative changes after publication require a new transport
version and a new immutable boundary; tooling-only revisions cannot silently
replace a published artifact preview.

**This preview is not published until that tag actually exists.** A future
tag name in OpenAPI or a digest file on mutable `main` is not publication.
Only select a merged commit after CI and review, rerun the offline checks, and
then create/push the real tag without moving the protocol tag. No tag is created
by the checker and no GitHub release is implied.

The vendored structural schema at
`tests/conformance/transport/openapi-3.1.schema.json` comes from the OpenAPI
Initiative's dated schema `https://spec.openapis.org/oas/3.1/schema/2022-10-07`.
Source: OpenAPI Initiative; the OpenAPI specification is Apache-2.0. The upstream
schema checks document structure, **not embedded schema correctness**; our
checks separately validate every component's Draft 2020-12 schema and resolve
all domain references against verified local frozen material. The vendored
bytes are included in the artifact manifest so CI needs no schema download.
