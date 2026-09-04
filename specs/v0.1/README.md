# FNB Protocol Schemas v0.1

Status: **Draft**

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

These JSON Schemas describe a small, implementation-neutral public surface. They
are derived from FNB's public domain model, not exported from the private product
API. A schema's presence does not promise endpoint availability or wire
compatibility with private builds.

The first draft covers Actor, Asset, Memory, FlowEvent, Node, BlockDraft, Block,
Relationship, AIInference, Correction/Patch, downstream invalidation, and
data-minimized audit tombstones. All examples are synthetic.

Breaking changes are allowed while the version remains `v0.1`; proposed changes
should use the public RFC process.

## Canonical identifiers and releases

Draft schema identifiers resolve from the public `FNB2026/fnb-open` repository:

```text
https://raw.githubusercontent.com/FNB2026/fnb-open/main/specs/v0.1/<schema-file>
```

The mutable `main` location is intentional while v0.1 is under review. Before an
accepted release, the repository will create an immutable Git tag, publish a
versioned manifest of schema digests, and freeze identifiers for that accepted
version. Accepted schema content will never be replaced in place.

## Validation

Install the pinned validation dependency and run the public conformance baseline:

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/validate-public-artifacts.py
```

The validator meta-validates every schema and canonical identifier, checks the
end-to-end synthetic chain, enforces its cross-object references, and proves that
both valid and invalid fixtures behave as expected. This is a reference-chain
baseline, not yet a third-party compatibility certification suite.
