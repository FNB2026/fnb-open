# Object Exchange TypeScript SDK `0.1.0-preview.1` — release notes (candidate)

Status: **PREPARED CANDIDATE — NOT PUBLISHED.**

This document is authored for the release-preparation candidate. No tag, GitHub
Release, registry publication or release credential exists yet. Do not read it as
an announcement that a release has happened.

## What this is

A GitHub Preview candidate of the Object Exchange TypeScript SDK. It is an
installable ESM tarball plus an external evidence bundle, intended for path **A**
(GitHub Preview first). It is not published to npm and asserts no npm identity;
the package keeps `private: true` and the non-official workspace name
`fnb-object-exchange-sdk-workspace`.

## Compatibility pair

| Item | Value |
| --- | --- |
| Object Exchange wire | `1.0` |
| Protocol release | `v0.1.0-preview.1` |
| Package version | `0.1.0-preview.1` |
| Candidate tag | `object-exchange-ts-sdk-v0.1.0-preview.1` |
| Runtime | Node.js 22, ESM, native `fetch` |

Frozen upstream dependencies (transport tag, schema tag, declaration snapshot)
are unchanged by this preparation.

## Installation and verification

```bash
npm install /path/to/fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz
```

Consumers must verify the tarball and evidence hashes in `artifact-digests.json`
before use, and read the bundled `README.md` for the API and limits. The archive
is exactly the reviewed 28-path allowlist; extra, missing, duplicate, symlinked
or traversal members are rejected by the release tooling.

## Runtime support

- Supported: Node.js 22 (Maintenance LTS), ESM only, native `fetch`.
- Node.js 22 scheduled EOL is **2027-04-30**; a separate newer-LTS migration is
  required before then and is not covered by this release.
- No browser, CommonJS or Node 24/26 support is claimed. Node.js Linux CI
  compatibility does not prove every Node 22 patch or operating system.

## Verification performed by this preparation

- Closed 28-path package allowlist and archive member validation (regular files,
  safe modes, no duplicates/traversal/symlinks) plus strict tar framing checks
  that fail closed on truncation, bad padding or trailing data.
- Same-workspace pack determinism, and separately an independent clean-checkout
  reproducibility check (`scripts/release/repro-check.mjs`) comparing two
  detached checkouts by tarball SHA-256 and member bytes.
- Offline tarball install, ESM runtime, NodeNext declaration and synthetic Mock
  exchange checks; zero runtime npm dependencies and no install scripts.
- External SPDX 2.3 SBOM for the actual archive (validated against the vendored
  official schema), external provenance bound to the candidate commit and
  toolchain, and a self-excluding digest manifest verified as a closed set.
- The pre-existing 26-test SDK suite plus the release-preparation tests, and the
  Python transports suite in ordinary and `-O` modes.

Exact counts, hashes, the candidate commit and any not-run items are recorded in
the release-preparation report and the independent review, not asserted here.

## Limitations and known issues

- `accepted` is a validation result only: it means the exchange was well-formed
  and in range, not that anything was stored, applied, authorized or durable.
- Timeout is cooperative: timers do not preempt CPU-bound work.
- The injected-`fetch` boundary is trusted code, not an operating-system sandbox.
- Byte caps measure visible bytes; non-identity `Content-Encoding` is rejected.
- No production, security-certification or service-availability guarantee.

## Separate npm gate (path B)

Publishing to npm is a different, separately reviewed and explicitly authorized
decision. It requires an approved package name/scope, ownership and trademark
rights, maintainers, OIDC trusted-publisher configuration, registry provenance,
a preview dist-tag (never `latest`), and removal of `private: true` in a distinct
reviewed candidate. Removing `private: true` is a technical prerequisite and is
**not** by itself publication authority.

## License

Apache-2.0. See the bundled `LICENSE-APACHE-2.0.txt` and `NOTICE.md`. FNB names
and marks remain reserved.
