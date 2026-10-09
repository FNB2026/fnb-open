# TypeScript SDK Release Boundary — Planning Only

Status as of 2026-10-10: **DRAFT / READY FOR INDEPENDENT PLANNING REVIEW**.

| Stage | Current decision |
| --- | --- |
| SDK implementation | CLOSED / ESTABLISHED |
| SDK release boundary | REVIEWED / PLANNING REQUIRED; this proposal is not approved yet |
| SDK publication | BLOCKED / NOT AUTHORIZED |

This PR adds only this plan and the [decision/gate table](typescript-sdk-release-boundary-decisions.md).
It does not implement release tooling, revise SDK functionality or documentation,
create tags/releases/packages/credentials, or change published upstream assets.
Planning approval alone must not execute either publication path.

## 1. Evidence baseline and scope

Implementation #30 was independently approved at
`512fff02f24a09f02858198561e120dbd1444a5c` and merged as
`b458ecfff002b8a7ae82d20dc5334b08cc44ec28`. Its main
[CI 37960487755](https://github.com/FNB2026/fnb-open/actions/runs/37960487755)
passed all three jobs. The [closure record](https://github.com/FNB2026/fnb-open/pull/30#issuecomment-6085134629)
is authoritative; historical implementation/review ledgers are not rewritten.
The [approved SDK plan](typescript-sdk-preview-plan.md) and
[implementation evidence](typescript-sdk-review-evidence.md) remain unchanged.

Immutable dependencies remain Object Exchange wire `1.0`, transport tag
`object-exchange-v1.0.0-preview.1` targeting
`6e9e0f7678859375dcbdf1535f30749ede836bfd`, schema tag
`v0.1.0-preview.1` targeting `2f7226c1cba688aba3b130f901379cfe79488ae7`,
and declaration snapshot `0728b46a6db55a272bcad6e05745d86628632c96`.
The SDK generator verifies local manifests and declaration hashes; it does not
fetch sender-supplied schema URLs. Mock #28 remains CLOSED / ESTABLISHED.

The release exposes only the established exchange client and declaration types.
`accepted` is validation, not storage, application, authorization or production
service assurance. No auth, accounts, private backend/database, retry/CRUD,
telemetry, browser support, Go SDK or expanded protocol semantics are included.

## 2. Two independent publication paths

**A — GitHub SDK Preview first.** Proposed artifact version `0.1.0-preview.1`,
tag `object-exchange-ts-sdk-v0.1.0-preview.1`, GitHub prerelease (not stable/latest
endorsement). Deliver a verified installable tarball plus the external evidence
bundle below. No npm identity, account or registry permission is required.

For A, retain package `private: true` and the current
`fnb-object-exchange-sdk-workspace` name as an explicitly nonofficial internal
tarball package label. Local tarball installation/import examples must use that
actual name; downloading from GitHub does not make it an npm registry package.
The external tarball filename is proposed as
`fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz`. Renaming the archive must not
rewrite package bytes. Existing exports remain `.` (ESM/types) and `./protocol`
(types only), zero runtime dependencies, no lifecycle installation scripts.

**B — npm Public Preview later.** Separately approve the official name/scope,
ownership/trademark rights, maintainers, public access, initial package bootstrap,
OIDC trust mapping and protected release workflow/environment, registry provenance,
and a preview dist-tag (not `latest`). In the separately reviewed npm release
candidate, remove `private: true` or set it to `false`: this is a technical
prerequisite because [npm refuses to publish private packages](https://docs.npmjs.com/cli/configuring-npm/package-json/).
It is not sufficient publication authorization; all B-path review, identity,
permissions and explicit approval gates still apply. A retains `private: true`.
Changing package identity requires a newly reviewed package, SBOM/provenance,
consumer tests and distinct SDK artifact version/tag; never relabel or replace A.
The registry version and dist-tag mapping need their own approved decision.
Do not assume credentials or initial trusted-publisher setup already exist.

Before B, recheck the official [trusted publishing](https://docs.npmjs.com/trusted-publishers/)
and [provenance](https://docs.npmjs.com/generating-provenance-statements/) requirements.
No OIDC configuration, token creation, login, namespace reservation or npm publish
belongs to this planning PR. GitHub digest/source evidence is not registry provenance.
Treat published name/version pairs as non-replaceable; deprecation/withdrawal and
dist-tag rollback are governance responses, not recovery of leaked content or a
license to reuse versions.

## 3. Closed package file inventory

The following exact **28 paths**, relative to the tarball's `package/` root,
are the proposed release allowlist. It matches a read-only offline pack dry-run
of the implementation workspace; it is not a freshly validated release artifact.
Future preparation must compare actual archive members to this set, not just
the permissive package `files` patterns. All entries are regular files; reject
duplicates, symlinks/hardlinks, absolute/traversal paths and unexpected modes.

```text
LICENSE-APACHE-2.0.txt
NOTICE.md
README.md
package.json
provenance.json
sbom.spdx.json
dist/index.js
dist/index.d.ts
dist/json.js
dist/json.d.ts
dist/protocol.js
dist/protocol.d.ts
dist/generated/wire.js
dist/generated/wire.d.ts
dist/generated/protocol/actor.d.ts
dist/generated/protocol/ai-inference.d.ts
dist/generated/protocol/asset.d.ts
dist/generated/protocol/audit-tombstone.d.ts
dist/generated/protocol/block-draft.d.ts
dist/generated/protocol/block.d.ts
dist/generated/protocol/correction-patch.d.ts
dist/generated/protocol/flow-event.d.ts
dist/generated/protocol/invalidation-record.d.ts
dist/generated/protocol/memory.d.ts
dist/generated/protocol/node.d.ts
dist/generated/protocol/permission-snapshot.d.ts
dist/generated/protocol/relationship.d.ts
dist/generated/protocol/source-state-change.d.ts
```

No tests, generation scripts, source maps, node_modules, development lockfiles,
credentials, private materials or production fixtures in the installable archive.
Build tools/locks remain auditable in the tagged repository and external evidence.
Internal parser/wire files are required implementation modules, not extra exports.
The archival extensionless protocol index is not installed; 14 domain declarations
retain their source byte hashes and the reviewed ESM facade remains separate.
Any change to this closed list requires an explicit reviewed plan revision.

## 4. License, metadata and evidence bundle

SDK code/declarations remain Apache-2.0. Preserve root license bytes, NOTICE,
upstream attributions and reserved FNB marks. Documentation follows the repository
path license; packaged SDK README/NOTICE follow the SDK license boundary.
CC0-1.0 on SPDX document metadata does not relicense referenced files/packages.

In a later preparation PR, update the consumer-facing SDK README and NOTICE from
unpublished/Draft language to the actually authorized GitHub Preview status and
tarball usage, support limits and no-npm identity. Do not edit historical ledgers.
Do not claim publication before it occurs. Review these changes and the generator
outputs as part of the new exact release-candidate commit; #30 remains closed.

Proposed external release assets (no assets created by this PR):

| Asset | Required content |
| --- | --- |
| `fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz` | Exact reviewed 28-member installable package |
| `release-provenance.json` | Repo/commit, dependency tags/targets/manifests, declaration hashes, package identity/version, generator/build workflow run, exact OS/architecture/Node/npm/TS/Python/dependency locks, commands and tests; no local paths, credentials or private inputs |
| `release-sbom.spdx.json` | SPDX 2.3 package/file inventory for the actual tarball, file SHA-256 and license records; distinguish bundled runtime files from external Node runtime and dev/build dependencies |
| `RELEASE-NOTES.md` | Preview status, compatibility pair, installation/verification, support dates, limitations, known issues and separate npm gate |
| `LICENSE-APACHE-2.0.txt`, `NOTICE.md` | Byte-identical copies of the packaged license and notice |
| `artifact-digests.json` | Closed six-asset set above with filename, byte length and SHA-256, plus the closed 28-member package inventory with per-file size/hash |

`artifact-digests.json` excludes itself: no self-digest or self-referential commit
hash. It and external provenance/SBOM are built **after** the final source commit
is known, outside the tracked tree. Embedded `provenance.json` remains upstream
source lineage; embedded `sbom.spdx.json` remains the labelled development-lock
inventory. Neither is mislabeled a signed release attestation. External SBOM
must validate against the chosen official SPDX schema and match the archive,
including the distinction between dev inventory and shipped runtime contents.

## 5. Reproducibility, integrity and immutable publication

Preparation must freeze an exact candidate source commit (not assumed to equal
the implementation merge), clean independent checkout, OS/toolchain versions,
hash-locked Python requirements and npm integrity lock. Provision development
dependencies without install scripts; record optional-platform selection and
network activity. Artifact generation/tests must not use private services or
fetch remote schemas. No claim that dependency provisioning is network-free.

Two separate clean build/pack environments using the same declared toolchain
must produce byte-identical tarballs and identical package inventories. Record
both hashes; a mismatch blocks release, not a justification to select one build.
This is reproducibility in the declared environment, not all operating systems.
Offline local tarball consumers must exercise ESM, NodeNext declarations and
synthetic exchange through the established Mock; packaging is not publication.

Manifest, provenance, SBOM and notes must be reviewed with the candidate SHA and
actual hashes. Signed annotated tag is the default; signing-key fingerprint and
trusted verification source must be independently approved, not learned only
from the downloadable bundle. Bind the manifest SHA-256 in the signed tag message.
The tag targets the final reviewed source commit. This avoids hash cycles between
source commit, external provenance and tag object.

If signing cannot be established, stop. An ordinary annotated tag requires a
separate explicit exception approval with the reduced authenticity guarantee
recorded; no automatic downgrade. A checksum detects byte drift, not publisher
identity. GitHub hosted/source-generated archives are not the approved SDK tarball.

Preparation must verify and record that GitHub Immutable Releases is enabled for
the actual repository; do not infer it from tag signing or no-overwrite policy.
See [enforcement settings](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes).
This is a future preparation gate, not permission to change settings now.
If unavailable, stop for a justified, separately approved reduced-guarantee
exception; voluntary restrictions are not equivalent platform protection.

Only after publication-specific authorization: recheck candidate CI/protection,
absent/unoccupied candidate tag/release, expected parent/dependency tags, then
create the approved signed tag and a Draft Release. Verify that all **seven**
intended uploads (six evidence assets plus `artifact-digests.json`) match the
approved names/bytes/hashes before publishing the Draft as a prerelease. Recheck
immutability settings immediately before publication. No force/repoint/overwrite. Re-read
remote tag object, peeled target and signature, download every published asset
and compare exact set/length/hashes; verify tag-bound manifest and package member
hashes before consumer use. Independently confirm published `immutable: true`
and verify GitHub's release attestation against the expected tag, source commit
and uploaded assets, retaining verification evidence. Missing/false immutability
or unverifiable attestation blocks establishment unless the exact reduced
guarantee was explicitly approved beforehand; never silently downgrade.

GitHub's [immutable-release attestation](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
is platform-generated metadata, separate from the six authored assets and
self-excluding manifest. Do not add it to that manifest or feed it back into
provenance/tag hashes. It complements, not replaces, signed-tag and digest checks.
Release title/body and prerelease/latest flags are not frozen by this protection;
the uploaded `RELEASE-NOTES.md` remains the digest-bound notes of record.
Failure leaves publication unestablished and requires
an incident/withdrawal decision; correction uses a new artifact version/tag, not
replacement of published bytes. No automatic deletion of evidence.

## 6. Runtime support and future migration

First preview supports **Node.js 22, ESM, native fetch**, wire `1.0`, schema
`v0.1.0-preview.1`. Node 22 is in Maintenance LTS on this planning date; the
official [schedule](https://github.com/nodejs/Release/blob/main/schedule.json)
plans EOL for **2027-04-30**. Recheck dates/security advisories before execution.
The existing 22.22.2 CI proves compatibility at that patch, not that it is the
current security patch. Preparation must select a supported secure Node 22 patch,
pin it and the build tools, then rerun the full acceptance matrix. Unresolved
toolchain vulnerabilities or runtime EOL block publication.

Release notes must disclose tested patch/platforms, support range and deadline,
native-fetch decoded-byte accounting, parser number/Unicode limits, synchronous
timeout limitation, trusted injected-fetch boundary, and lack of production or
security-certification guarantees. Do not promise every Node 22 patch/OS works
solely from Linux CI. Arrange a separate newer-LTS migration/test proposal before
Node 22 EOL; do not silently broaden this release to Node 24/26, browsers or CJS.

## 7. Acceptance and authorization order

1. Independent review of this docs-only proposal; still no publication authority.
2. Separately authorized release preparation PR: consumer docs, reproducible
   tooling, manifest/SBOM validation, security checks, tag policy and artifact tests.
3. Independent review of candidate commit, complete files, actual artifact hashes,
   provenance, licenses, fresh security/runtime state and exact-head CI.
4. Explicit approval scoped to path A, exact source SHA, version/tag, manifest
   digest and six-asset evidence set. Only then execute publication and verify it.
5. Record established release evidence. Path B requires separate decisions,
   preparation/review and explicit npm authorization; A never implies B.

See the decision table for executable future gates. Completion of this PR is
**SDK RELEASE BOUNDARY PLANNING READY FOR REVIEW**, not SDK RELEASED. All
candidate filenames/versions/mechanisms here are proposed until independent
planning approval; no SHA-256 value is invented before real preparation.
