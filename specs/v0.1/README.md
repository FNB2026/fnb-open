# FNB Protocol Schemas v0.1

Status: **Pre-release — frozen at the immutable `v0.1.0-preview.1` tag**

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

These JSON Schemas describe a small, implementation-neutral public surface. They
are derived from FNB's public domain model, not exported from the private product
API. A schema's presence does not promise endpoint availability or wire
compatibility with private builds.

The first draft covers Actor, Asset, Memory, FlowEvent, Node, BlockDraft, Block,
Relationship, AIInference, Correction/Patch, PermissionSnapshot,
SourceStateChange, downstream invalidation, and data-minimized audit tombstones.
All examples are synthetic.

The governing v0.1 RFCs are accepted. `v0.1.0-preview.1` is an immutable protocol
preview, not a stability promise for later v0.1 previews. Any change to frozen
content requires a new tag and digest manifest.

## Canonical identifiers and releases

The preview schema identifiers resolve through the immutable release tag:

```text
https://raw.githubusercontent.com/FNB2026/fnb-open/v0.1.0-preview.1/specs/v0.1/<schema-file>
```

The exact 14-file set, byte lengths, and SHA-256 digests are recorded in
[`releases/v0.1.0-preview.1/schema-digests.json`](./releases/v0.1.0-preview.1/schema-digests.json).
The freeze was published as [PR #17](https://github.com/FNB2026/fnb-open/pull/17):
merge commit `2f7226c1cba688aba3b130f901379cfe79488ae7` on `main` is tagged
`v0.1.0-preview.1` (annotated tag object
`f492754744d74ed3459c4ce361108ba8c8a04acc`). That tag must never be retargeted.

## Validation

Install the pinned validation dependency and run the release verifier:

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/fnb-conformance.py verify-release \
  --root . \
  --manifest specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json
```

The CLI first proves that the checkout contains exactly the 14 manifest schemas
with matching byte lengths and SHA-256 digests. It then runs the public reference
validator over schema metadata, synthetic examples, cross-object semantics, and
positive/negative fixtures. The resulting compatibility report follows
[`tests/conformance/compatibility-report.schema.json`](../../tests/conformance/compatibility-report.schema.json).

A pass is evidence for the checks reported. It is not product certification,
security certification, legal compliance, or compatibility with a private FNB
service.
