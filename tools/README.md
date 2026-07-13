# Public Artifact Validation Tools

License: Apache-2.0. See [`LICENSE-CODE.md`](../LICENSE-CODE.md).

Run:

```bash
python3 -m pip install --requirement tools/requirements-validation.txt
python3 tools/validate-public-artifacts.py
```

The dependency is pinned so local and GitHub Actions validation use the same
JSON Schema behavior.
