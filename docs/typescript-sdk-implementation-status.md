# TypeScript SDK Preview — Implementation Draft Ledger

SDK planning: **FROZEN / APPROVED (PLANNING ONLY)**. Independent review of
planning HEAD `81373428d03fa857b42b32eaff9e12b893621486` was recorded in
[PR #29 review](https://github.com/FNB2026/fnb-open/pull/29#issuecomment-6080921759).
It merged as `ff5d8906fb24b513bb641fdbd2f087c327bc101e`; main CI
`37931032960` passed. The approved [plan](typescript-sdk-preview-plan.md) and
[decisions/matrix](typescript-sdk-preview-decisions.md) are unchanged snapshots.

This separate implementation PR is **DRAFT / IMPLEMENTATION STARTED**, not
approved for merge, SDK release, or npm publication. Mock #28 remains CLOSED /
ESTABLISHED and its files are unchanged. No Go SDK or private integration.

The endpoint revision and four-gate reproducible evidence are documented in
[revision evidence](typescript-sdk-review-evidence.md). These developer tests
do not close the independent review gates listed below.

## Change boundary

New explicitly Apache-2.0 `sdk/typescript/` workspace, one additive Node 22 CI
job and this ledger. No upstream schemas/RFC/OpenAPI/manifest/lock/bindings,
approved planning content, or published tag changes. Package name is private
workspace-only, not an approved official npm namespace.

Generated: wire types/metadata, byte-identical domain declaration snapshots,
explicit ESM type facade, source provenance and a development-lock SPDX
inventory. Handwritten: bounded JSON safety layer, thin fetch/correlation client,
tests, build finalizer and local documentation. No second domain validator.
`npm pack`/offline installation test does not publish anything.

## A01–A40 evidence mapping

Rows below map to named groups in `sdk/typescript/tests/*.test.mjs` or existing
baseline commands. PASS means automated development evidence only, not
independent approval. Local Node 25 results are diagnostics; exact Node 22.22.2
native fetch evidence must come from the new SDK CI job before acceptance.

| IDs | Automated evidence | Remaining acceptance boundary |
| --- | --- | --- |
| A01–A06 | Established Mock native-fetch synthetic interoperability; four worlds, interleaved independent chains, invalid objects, absent roles, duplicate IDs, bad dates/direct links, exact Unicode echoes | Exact supported-runtime CI and independent review |
| A07–A08 | Both accepted/rejected correlation-field mutations and receipt shape negatives | Independent response-boundary review |
| A09–A12 | All six Problems, tuple/detail mutations, ignored extensions, nested duplicate extension | Independent consumer/emitter semantics review |
| A13–A17 | Actual native HTTP statuses, hostile JSON/media/encoding; native gzip decoding tested while visible gzip rejected | Independent native-fetch behavior review; no raw hidden-header claim |
| A18–A20 | Non-JSON/lossy input corpus, prototype-sensitive records and parser depth/token/UTF-8/numeric limits | Independent handwritten parser/resource audit NOT COMPLETE |
| A21–A23 | Separate Mock processes: lower byte/object caps, internal failure, missing/corrupt schema/manifest, no site-packages | Public fault copies only, not repairs to #28 |
| A24–A25 | Six Problem response cases and unsupported local versions/grammar before dispatch | Negative response harness separate from public send API |
| A26–A27 | Real native Content-Length, URL/headers rejection and redirect no-replay | Independent endpoint/fetch policy review |
| A28–A31 | Stalled headers/body, disconnect/truncation, incremental cap, pre-abort, body abort, late ignored success, listener/reader cleanup | Additional hostile-scheduler/deadline audit required; tests alone are not race approval |
| A32–A34 | Concurrent/out-of-order/swapped responses, detached request snapshot, invalid/failing injected fetch | Independent per-call state/lifecycle review |
| A35 | Generator checks/two repeated renders, declaration digests; unsupported wire keyword/ref negatives | Provenance review and immutable dependency checks |
| A36 | Source type expectations plus offline installed ESM/NodeNext consumer | Supported Node/TS CI evidence required |
| A37 | Zero-runtime-dependency/lock/lifecycle/static import audit; loopback-only test targets, no schema retrieval | Independent supply-chain/runtime audit still required; not OS sandbox proof |
| A38 | Repeated local build/pack bytes, explicit licenses/provenance/SPDX inventory, offline local tarball install | Inventory/provenance audit and release security review NOT COMPLETE |
| A39 | Existing Python 31 offline + 20 Mock tests, ordinary and -O; frozen manifest/generator checks | CI/guard evidence, no baseline modification |
| A40 | New exact-head SDK CI and existing hygiene/bindings jobs | Merged-main SDK CI and independent implementation approval NOT COMPLETE; Draft must not merge now |

## Hard review gates still open

1. Independent hostile-input review of the recursive JSON parser: grammar,
   escaped/literal duplicate keys, Unicode, integer overflow, depth/token/byte
   limits, prototype-sensitive names and the string-token-only JSON.parse usage.
2. Independent abort/deadline review: first cause, once-only settlement, late
   fetch/body completion, cleanup and synchronous checkpoint limitations.
3. Node 22 native fetch review: Content-Length, visible Content-Encoding versus
   transparently decoded bytes, bounded streams, redirect and truncation behavior.
4. Independent generated metadata/provenance, license/inventory/dependency and
   clean consumer review. Package/toolchain security status must be rechecked
   before any future release; workspace SPDX is not a release attestation.

Exact implementation HEAD, complete diff and CI run are recorded in the Draft
PR, avoiding a self-referential commit SHA inside this file. Do not use green
tests or number of test groups to mark these independent gates approved.
SDK release/tag, npm namespace/provenance publication, browser/other runtimes,
and Go SDK remain separately unauthorized. No change to either frozen tag.
