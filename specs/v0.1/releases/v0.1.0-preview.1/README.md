# v0.1.0-preview.1 protocol freeze

This directory describes the first tagged FNB public protocol preview. It
freezes the public protocol surface only; it is not an FNB product release.

## Included scope

The release bundle consists of:

- the 14 implementation-neutral JSON Schemas in `specs/v0.1/*.schema.json`;
- the synthetic examples and conformance fixtures in the same tagged tree;
- the public validation and conformance tools in the same tagged tree.

It does **not** include or identify a private product build, private repository
commit, production API, authentication implementation, worker, IM/WebSocket
implementation, storage topology, migration system, deployment, or real data.

## Integrity

`schema-digests.json` records the byte length and SHA-256 digest of every
protocol schema in this preview. The manifest is exact-set checked: an added,
removed, or modified schema causes verification to fail.

## Publication record

The freeze was published as PR #17 and landed on `main` as merge commit
`2f7226c1cba688aba3b130f901379cfe79488ae7`. That commit is tagged exactly
`v0.1.0-preview.1`, an annotated signed tag whose tag object is
`f492754744d74ed3459c4ce361108ba8c8a04acc`; GitHub verification reports
`verified` with reason `valid`.

That tag is an immutable publication boundary and must never be moved or reused.
Any later protocol change requires a new version, tag, and manifest.

## Independent verification

From a checkout of the release tag:

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/fnb-conformance.py verify-release \
  --root . \
  --manifest specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json
```

Use `--json` for a machine-readable compatibility report or
`--report <path>` to save that report.

A passing report means the checked public bundle matches this digest manifest
and passes the public reference conformance suite. It is evidence of protocol
conformance for the checks reported; it is not product certification, security
certification, legal compliance, or compatibility with a private FNB service.
