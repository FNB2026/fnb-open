# Public Artifact Validation Tools

License: Apache-2.0. See [`LICENSE-CODE.md`](../LICENSE-CODE.md).

Run:

```bash
python3 -m pip install --require-hashes --requirement tools/requirements-validation.lock
python3 tools/validate-public-artifacts.py
```

`requirements-validation.in` declares the direct dependency. The generated lock
file pins every transitive dependency and accepted distribution hash so local and
GitHub Actions validation use the same JSON Schema behavior.
