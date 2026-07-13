# FNB Protocol Schemas v0.1

Status: **Draft**

License: Apache-2.0. See [`LICENSE-CODE.md`](../../LICENSE-CODE.md).

These JSON Schemas describe a small, implementation-neutral public surface. They
are derived from FNB's public domain model, not exported from the private product
API. A schema's presence does not promise endpoint availability or wire
compatibility with private builds.

The first draft covers Actor, Asset, Memory, FlowEvent, Node, BlockDraft, Block,
Relationship, AIInference, and Correction/Patch. All examples are synthetic.

Breaking changes are allowed while the version remains `v0.1`; proposed changes
should use the public RFC process.

## Validation

Install the pinned validation dependency and run the public conformance baseline:

```bash
python3 -m pip install --requirement tools/requirements-validation.txt
python3 tools/validate-public-artifacts.py
```

The validator meta-validates every schema, checks the end-to-end synthetic chain,
enforces its cross-object references, and proves that both valid and invalid
fixtures behave as expected.
