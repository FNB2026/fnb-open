# Object Exchange TypeScript SDK — unpublished workspace

License: Apache-2.0; see [NOTICE](NOTICE.md) and bundled license text.
Planning is **FROZEN / APPROVED**, merged as
`ff5d8906fb24b513bb641fdbd2f087c327bc101e` after independent review of #29; the
release boundary is approved and merged as
`5d1a45a8a65c532ad4d33704ff7bb726d7a599cf` after independent review of #31.

**This package is not published.** No tag, GitHub Release or registry publication
exists, and the workspace name is private and is not an approved npm identity.
The release-preparation candidate and its external evidence are described in
[RELEASE-NOTES.md](RELEASE-NOTES.md); preparing a candidate is not publishing it.

## Development

Use Node `22.23.3` (the selected supported Node 22 patch), TypeScript `7.0.2` and
the repository's hash-locked Python validation environment. Other local Node
versions provide diagnostic evidence only; native-fetch acceptance comes from the
Node 22 CI job.

```bash
python3 sdk/typescript/scripts/generate.py --check
npm ci --prefix sdk/typescript --ignore-scripts --no-audit --no-fund
npm run build --prefix sdk/typescript
npm run typecheck --prefix sdk/typescript
FNB_TEST_PYTHON=/absolute/path/to/hash-locked/python npm test --prefix sdk/typescript
```

Generation reads verified local immutable transport/schema manifests, checks
the existing bindings generator, copies byte-identical declarations and emits
wire types/metadata, provenance and a development-lock SPDX inventory. There is
no remote `$ref` retrieval. The frozen extensionless declaration index remains
an archival source snapshot; a generated SDK ESM type facade uses explicit
`.js` references without changing domain declaration bytes. The build copies
individual domain declarations into its private output tree.

Only `createExchangeClient({ endpoint, fetch?, timeoutMs?, limits? })` is a
runtime export factory; `exchange(envelope, { signal? })` sends one operation.
Additional public exports are declaration types and a configuration-error class,
not domain operations. The protocol subpath is type-only. No login, auth headers,
cookies, retry, CRUD, inferred roles, database, private backend or telemetry.

Endpoint must be an explicit absolute `/exchange` URL: HTTPS, or HTTP with a
numeric dotted IPv4 loopback literal. Credentials/query/fragment/other routes
are rejected. Only Node 22 ESM/native fetch is supported initially; injected
fetch is trusted code and must honor policy/signal/streams, not an OS sandbox.

Results discriminate `receipt` (accepted OR rejected), known transport `problem`,
and local/network `failure`. Receipts must match all three snapshot correlation
fields and their exact closed shape. No verdict means stored, applied, authorized
or historically complete. Problems validate exact type/title/HTTP-status tuple;
valid unknown extensions are ignored. Detail text is untrusted, not logged.
No default diagnostics expose bodies, identifiers, URLs, secrets or stack traces.

Request serialization rejects non-JSON/lossy/coercing values, accessors, cycles,
unsafe integer Numbers and class instances. Fractional JS Number semantics are
not arbitrary-precision JSON. The response parser detects duplicates before
object construction, uses fatal UTF-8, and compares decoded keys. JSON.parse is
used only to decode individual string tokens, never objects/documents. Parser
records have null prototypes, then known receipt/problem fields are projected
to ordinary public records. Independent parser review remains mandatory.

Default timeout is 10 seconds (allowed 1..60000 ms), covering fetch, reading and
validation checkpoints. Abort/timeout settle once; no late verdict. Timers do
not provide CPU preemption. Default limits: request 1 MiB/256 objects, response
64 KiB, depth 64 and 32768 tokens. Overrides only reduce these positive caps.
Fetch-visible byte caps do not measure compressed wire bytes; visible non-
identity Content-Encoding is rejected even if native fetch decompressed it.
No raw framing or hidden duplicate-header detection guarantee is asserted.

Tests use unchanged established Mock, synthetic worlds, a separate loopback
fault server and trusted injected responses. Local `npm pack` and offline
temporary-consumer install are tests, **not npm publication**. Package build
bytes, licenses/provenance/inventory and ESM/types resolution are exercised.

## Release preparation (candidate only)

The release tooling under [scripts/release](scripts/release) builds and verifies
the external evidence bundle for the GitHub Preview path: a closed 28-path
package allowlist, an external SPDX 2.3 SBOM for the actual archive, external
provenance bound to the candidate commit and toolchain, and a self-excluding
`artifact-digests.json` manifest. `verify` treats the asset set, the package
member set and the provenance identity as closed sets.

```bash
node sdk/typescript/scripts/release/evidence.mjs generate \
  --tarball <packed.tgz> --out <evidence-dir> --commit <sha> --created <iso>
node sdk/typescript/scripts/release/evidence.mjs verify --dir <evidence-dir>
python3 sdk/typescript/scripts/release/validate-sbom.py <evidence-dir>/release-sbom.spdx.json
# Independent clean-checkout reproducibility evidence (two detached checkouts):
FNB_TEST_PYTHON=<python> node sdk/typescript/scripts/release/repro-check.mjs --commit <sha>
```

Evidence is written outside the tracked tree, so the candidate source commit,
the external provenance and any future signed tag cannot form a hash cycle. The
tooling never creates a tag, Release, credential or registry publication.

`verifyTagBindingPolicy` is a read-only **policy preflight** over supplied
parameters only: it checks a declared tag message against a declared manifest
digest and approved-fingerprint list. It performs **no** cryptographic signature
verification and cannot establish authenticity; real publication must
independently verify the signed tag object and the trusted key identity.

The [implementation ledger](../../docs/typescript-sdk-implementation-status.md)
maps A01–A40 and names outstanding evidence/review gates. No tag, release, npm
publication or Go SDK action belongs to this Draft. Mock #28 remains closed;
the approved planning documents and frozen upstream assets remain unchanged.
