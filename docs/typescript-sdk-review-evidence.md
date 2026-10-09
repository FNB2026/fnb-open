# TypeScript SDK — Revision Evidence for Independent Review

Status: **DEVELOPER EVIDENCE / INDEPENDENT REVIEW OPEN**. This supplements
[PR #30 revision request](https://github.com/FNB2026/fnb-open/pull/30#issuecomment-6082628168)
and the [implementation ledger](typescript-sdk-implementation-status.md).
It is not independent approval, a parser security certification, or permission
to merge/publish. Exact HEAD and supported-runtime CI are recorded in the PR.
Only SDK endpoint validation, SDK tests and review documentation change here.
Frozen protocol assets, planning decisions, Mock #28 and published tags do not.

## Endpoint correction — D08 / A26

The regression test first failed against the previous implementation for
`http://127.0.0.01/exchange`. The corrected HTTP boundary inspects the original
host: exactly four decimal octets, each `0–255`, no leading zero except `0`
itself, first octet `127`, and exact equality to the parsed hostname. This
rejects leading-zero/octal, hexadecimal, integer, abbreviated and encoded host
spellings before trusting URL normalization. Canonical `127.0.0.1`,
`127.0.0.2`, octet boundaries and explicit ports remain accepted. HTTPS policy
is unchanged. See `sdk/typescript/tests/endpoint.test.mjs`.

## Four review gates — reproducible evidence, not closure

| Gate | Added or strengthened evidence | Limits / independent reviewer task |
| --- | --- | --- |
| Strict JSON parser | `parser.test.mjs`: decoded-key collisions (escaped/literal, nested, Unicode, prototype-sensitive), exact byte/depth/token limits, malformed UTF-8 and number boundaries; 512 deterministic valid cases and 512 duplicate mutations | Review recursive implementation and resource accounting, not test count. No exhaustive fuzzing claim. Only scalar string tokens use JSON.parse. |
| Abort / timeout races | `races.test.mjs`: controlled timeout-first and cancel-first; queued EOF before deadline/cancellation; receipt/rejection committed first; once-only settlement, late-body cancellation, removed listener and cleared timer | Fake timers control callbacks while promises execute real microtasks. Existing native HTTP tests cover actual stalled streams. This is not proof of every scheduler ordering. |
| Native fetch | `native-fetch.test.mjs`: actual loopback HTTP gzip response, retained encoding/length headers but decoded body; decoded bytes exceed cap although compressed bytes fit; chunked over-budget stream and premature EOF | Supported evidence must run on pinned Node 22.22.2 CI. Local Node 25 is diagnostic only. SDK budgets fetch-visible decoded bytes, not raw compressed bytes or hidden transport buffers. |
| Inventory / provenance / package | `package.test.mjs`: lock inventory names/versions/URLs, unique SPDX IDs and relation references, deterministic lock-derived namespace; root license equality; packed/installed 14 domain declarations match source hashes; license/NOTICE/provenance/inventory survive packing byte-for-byte | SPDX is a development lock inventory (including uninstalled optional platforms), not a signed release SBOM or attestation. Namespace hashes sorted parsed lock content, not original file bytes. Independent SPDX/license/provenance and future toolchain security review remain required. |

Parser policy deliberately distinguishes invalid raw UTF-8 from JSON Unicode
escapes: JSON escaped unpaired UTF-16 surrogates are accepted, decoded key
equality is case-sensitive and does not perform Unicode normalization. Integers
outside the JavaScript safe-integer range and nonfinite values are rejected;
fractional values retain JavaScript Number semantics, not arbitrary precision.
Independent review should check these explicit policies against the approved
plan rather than assume broader Unicode or numeric guarantees.

Race tests require a single final outcome. An EOF already queued is not yet an
accepted receipt: cancellation/deadline may win before validation commits.
Conversely an already committed receipt is not rewritten by a later abort.
Thrown network exception text is not exposed as a result. Synchronous parsing
cannot be interrupted mid-instruction; bounds and post-parse checkpoints remain
the protection, not a claimed preemptive timer.

Native fetch transparently decompresses gzip in the tested runtime. A visible
nonidentity encoding under the size cap is rejected as `invalid-response`;
an over-cap decoded stream returns `response-limit` before semantic acceptance.
A valid-looking JSON prefix is never accepted when the declared body truncates.
No change to the frozen transport or Mock Server is needed.

## Reproduction

From repository root, select the hash-locked Python environment in
`FNB_TEST_PYTHON` (the public requirements lock and `--require-hashes` remain the
dependency authority). Install the SDK development lock without lifecycle
scripts. No npm publication is performed:

```bash
npm ci --prefix sdk/typescript --ignore-scripts
"$FNB_TEST_PYTHON" sdk/typescript/scripts/generate.py --check
npm run build --prefix sdk/typescript
npm run typecheck --prefix sdk/typescript
npm test --prefix sdk/typescript
"$FNB_TEST_PYTHON" tools/object-exchange-contract.py
"$FNB_TEST_PYTHON" -m unittest discover -s tests/conformance/transport -p 'test_*.py'
"$FNB_TEST_PYTHON" -O -m unittest discover -s tests/conformance/transport -p 'test_*.py'
git diff --check
```

The SDK suite contains 26 named groups, including established Mock interaction
and offline pack/install checks. The unchanged Python baseline contains 31
offline contract tests and 20 live Mock tests (51 in each mode). Test counts are
navigation aids, not independent acceptance. All four review gates and merged
main acceptance remain open; PR #30 stays Draft pending independent final review.
