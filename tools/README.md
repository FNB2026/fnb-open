# Public Artifact Validation Tools

License: Apache-2.0. See [`LICENSE-CODE.md`](../LICENSE-CODE.md).

## Release and conformance

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/validate-public-artifacts.py
python3 tools/fnb-conformance.py verify-release \
  --root . \
  --manifest specs/v0.1/releases/v0.1.0-preview.1/schema-digests.json
```

`fnb-conformance.py` verifies the frozen release bundle (exact schema set, byte
lengths, SHA-256 digests) before running the public synthetic conformance suite,
and emits a compatibility report. It has no network or product-service
dependency.

`requirements-validation.in` declares the direct dependency. The generated lock
file pins every transitive dependency and accepted distribution hash so local and
GitHub Actions validation use the same JSON Schema behavior.

## Generated bindings

```bash
python3 tools/generate-bindings.py            # write bindings/
python3 tools/generate-bindings.py --check    # fail if committed bindings are stale
```

`generate-bindings.py` is standard-library only, so it adds no supply-chain
surface to the Python validation environment. It reads the frozen release
manifest, verifies every schema byte length, SHA-256 digest, and `$id`
namespace, and fails closed on any unsupported JSON Schema keyword. See
[`bindings/README.md`](../bindings/README.md).
