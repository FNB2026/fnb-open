# TypeScript SDK Preview — Decisions and Acceptance Matrix

Planning only. Parent: [SDK plan](typescript-sdk-preview-plan.md).
License: CC BY-NC-SA 4.0 under the repository documentation matrix.
Decisions below are proposed for independent approval, not implemented features.

## Decision register

| ID | Proposed decision | Rationale / rejected alternative | Gate |
| --- | --- | --- | --- |
| D01 | One exchange operation; caller supplies ID/context; no retry | No product API, inferred chains, persistence or idempotency promise | Planning review |
| D02 | Separate receipt/problem/failure result kinds | 200 is not automatically accepted; negative verdict is not transport failure | Planning review |
| D03 | Exact per-call three-field correlation and closed receipt shape | Never trust late, unrelated or extra-member receipts | Planning review |
| D04 | Strict byte/UTF-8/duplicate-aware JSON response parser | JSON.parse/reviver cannot recover erased duplicates; replacement decoding hides invalid bytes | Parser review required later |
| D05 | Reject non-JSON/lossy input; ordinary fractional JS Numbers only | No implicit serializer coercion or arbitrary-precision promise | Planning review + numeric tests |
| D06 | Known problem base fields strict; unknown extensions ignored after strict parse | Consumer rule in RFC-0004/RFC 9457 differs from closed OpenAPI emitter schemas | Explicit adversarial review |
| D07 | Node 22 native fetch, ESM; trusted fetch injection only | Avoid untested browser/CORS/polyfill and dual-module promises | Exact runtime CI and package consumer tests later |
| D08 | Explicit HTTPS endpoint, HTTP numeric IPv4 loopback exception | No default production URL, credentials or redirect leakage | URL policy tests later |
| D09 | One deadline/abort scope through body validation, no replay | Header-only timeout and retry may hide unknown receiver outcome | Race/cleanup tests later |
| D10 | Generate wire declarations/metadata; handwrite transport safety layer | Generic generation defaults are not frozen-contract compatibility | Generator and parser independent review |
| D11 | Reuse byte-identical binding snapshot; no domain runtime judge | Bindings are static convenience, not a second conformance engine | Manifest/provenance/regeneration checks |
| D12 | Zero runtime dependencies target; separately locked dev toolchain | Minimize supply chain without waiving parser/security review | Dependency inventory and review before implementation acceptance |
| D13 | SDK version/tag independent; npm identity/publication undecided | Tooling release must not move upstream frozen boundaries | Separate release approval |
| D14 | Reuse established Mock; fault responses in a separate test-only harness | Do not reopen #28 or add fault routes to it | Test isolation review |
| D15 | No SDK implementation, Go work or npm publish in this PR | Planning approval and product delivery are different evidence levels | Docs-only diff guard |

No wire-level open question is introduced. Release blockers that remain for
later explicit decisions: npm namespace/ownership; final package file/export
list and licensing matrix change; exact security-supported build/test pins;
reviewed parser implementation (or separately approved dependency); supply-chain
provenance/publishing mechanism. These are not permission to start work now.
If independent planning review disagrees with D04/D06/D07, revise this plan before
implementation rather than silently changing its promises in code.

## Future executable harnesses

- **M**: launch unchanged public Python Mock from the merged base on an ephemeral
  IPv4 loopback port, using hash-locked dependencies and committed synthetic
  worlds. Native Node fetch sends real requests; all resources close in finally.
- **F**: separate test-only loopback response server sends deliberately faulty
  status/header/body bytes, delays or drops connections. Use no new Mock routes,
  private backend or production data. Requests and expected outcomes are public
  synthetic material. HTTP framing faults may be rejected by native fetch before
  SDK parsing; expected result remains failure, never a fabricated verdict.
- **U**: deterministic unit/type tests and trusted injected fetch for race control,
  no network. Expectations are authored independently of generated SDK output.
- **G**: clean generation/build/package checks pinned to upstream manifests and
  actual snapshots. No external network after provisioning except loopback M/F.

This matrix is an executable specification for the future implementation, not
scripts added or test results claimed in this PR. Each ID must later map to at
least one named automated test. M proves live receiver interoperability; F/U
prove hostile-response/error handling not observable from a well-behaved Mock.

| ID | Harness / synthetic case | Required assertion |
| --- | --- | --- |
| A01 | M: four existing generated worlds | 200 receipt accepted; exactly four fields; all three echoes identical |
| A02 | M: schema-invalid object `{}` and unknown schema ID | 200 receipt rejected, not local invalid-input or transport failure |
| A03 | M: multi-object/context worlds and interleaved independent chains | Roles carried unchanged; receiver's public result preserved; no inferred closure |
| A04 | M: context role points to absent object; duplicate typed identity | 200 rejected, not repaired by SDK |
| A05 | M: schema-valid shape with malformed datetime or direct-link inconsistency | 200 rejected; no SDK claim of domain conformance |
| A06 | M: Unicode/whitespace-containing exchange_id | Exact echo preserved, no normalization |
| A07 | F: accepted and rejected receipts with each echo field changed in turn | invalid-response for both statuses, never receipt |
| A08 | F: receipt missing/extra field, invalid verdict or empty string | invalid-response; no fallback acceptance |
| A09 | F: all six known type/status/title tuples, optional string detail | problem kind; observed HTTP status equals body status; no verdict |
| A10 | F: status/type/title mismatch, non-string detail, missing base field, unknown type | invalid-response; default diagnostics contain no body text |
| A11 | F: known problem with valid unrecognized nested extensions | Ignore/drop extensions while preserving known validated fields |
| A12 | F: duplicate keys even inside ignored problem extension | invalid-response, not tolerated by extension rule |
| A13 | F: 200 problem, 400 receipt, 201/204/401/403/404/429/502 and HTML gateway error | failure, never receipt/problem guessed from text or Response.ok |
| A14 | F: duplicate keys at each depth, escaped/literal duplicate key pairs | invalid-response before field extraction |
| A15 | F: invalid UTF-8, BOM, NaN/Infinity/-Infinity, trailing JSON, empty/non-object body | invalid-response, no replacement decoding |
| A16 | F: wrong/missing/multiple Content-Type, wrong charset/parameters | invalid-response; correct JSON/problem media and UTF-8 variants pass |
| A17 | F: absent/identity/Identity/IDENTITY versus gzip response encoding | Supported observable identity variants pass; non-identity fails; no hidden framing claim |
| A18 | U: cyclic/sparse/undefined/function/symbol/BigInt/nonfinite/unsafe integer/custom toJSON input | invalid-input before dispatch, no silent omission/coercion |
| A19 | U: ordinary JSON numbers, prototype-sensitive keys, escaped keys | Snapshot/serialization stable; no prototype mutation; declared Number limitation holds |
| A20 | U/F: response numeric overflow, malicious nesting/token counts | failure within documented bounds, no rounded-status acceptance or parser crash |
| A21 | M: receiver byte limit deliberately below a valid request | 413 payload-too-large problem, not receipt or automatic split/retry |
| A22 | M: receiver object cap below SDK-admitted batch | 413 problem after decoding, no batch repair |
| A23 | M: test-local evaluator failure, absent/corrupt schema/manifest and missing validator | 500 evaluation-failure problem; never receipt; no repair to established Mock code |
| A24 | F: malformed-envelope/media/version Problem Details | All 400/415 distinctions decoded from exact tuple; no loss of category |
| A25 | U: unsupported request version, invalid envelope shape | invalid-input before network; no implicit negotiation; A24 separately tests server errors |
| A26 | U/M: explicit URL validation and native-fetch Content-Length request | Valid loopback `/exchange` succeeds; credentials/query/fragment/other path/public HTTP fail before dispatch; no chunked body |
| A27 | F/U: redirect to another receiver; auth/custom header attempts | No redirected send or credential/custom product-header support; generic network/failure outcome |
| A28 | F: connection refused/disconnect/truncated body | network or invalid-response as appropriate to exposed fetch stage; no verdict |
| A29 | F/U: stalled headers and stalled body independently | timeout covers entire operation; reader/fetch cancelled and timers/listeners removed |
| A30 | U: pre-aborted signal, cancel during body, timeout/cancel race, late success | No pre-abort send; first terminal cause wins; exactly one result, no late receipt |
| A31 | U/F: response exceeds byte limit with misleading/absent Content-Length | Incremental cap enforced on delivered bytes; response-limit failure and reader cleanup |
| A32 | U/F: concurrent calls receive swapped/out-of-order replies | Correlation is per-call; swapped IDs fail, correctly correlated out-of-order results pass |
| A33 | U: mutate caller envelope after invocation | Sent bytes and echo comparison use detached original snapshot |
| A34 | U/G: trusted injected fetch absent/invalid capability or failure | Explicit configuration/internal failure; no global patch, hidden polyfill or swallowed error |
| A35 | G: frozen manifests/schema IDs and snapshot regeneration twice | Exact upstream identities/digests preserved; deterministic output; unsupported keyword fails generation |
| A36 | G: type expectation and ESM consumer tests | Compile against selected exact Node/TypeScript pins; runtime exports and declarations resolve without private paths |
| A37 | G: dependency/network/storage audit of SDK package | Only explicit receiver traffic; no schema/problem fetch, telemetry, storage, private imports, lifecycle hooks or undeclared dependencies |
| A38 | G: clean package build/pack/install repeat | Stable bytes or fully documented deterministic normalization; pack content, licenses, SBOM and digest provenance verified |
| A39 | G: baseline Python normal and -O suites | Existing 31 offline plus 20 Mock tests remain 51/51; no frozen asset changes or reopening #28 |
| A40 | G: exact-head and merged-main CI, independent review evidence | SDK implementation acceptance only after all mapped tests pass; publication still separately gated |

A23 uses separate test processes or in-memory fault injection/temporary copies
of public assets; never damage the checkout's frozen files. A24 uses F because
the public SDK intentionally cannot emit unsupported wire versions or invalid
serialization. No unsafe raw-send escape hatch is added to make negative tests
possible. Limits are arranged in tests so server and SDK failures are not
mistaken for each other (for example lower the Mock cap for A21/A22).

## Evidence ledger for this PR

| Layer | Current claim |
| --- | --- |
| Planning documents | Capability, policy decisions, matrix and release gates described |
| Repository hygiene CI | Must be green on exact documentation head before handoff |
| Existing baseline regression | Re-run evidence may confirm existing assets only |
| SDK runtime/type/generator/package tests | NOT IMPLEMENTED / NOT EXECUTED |
| Browser/other runtime interoperability | OUT OF SCOPE / NOT CLAIMED |
| Package/tag/npm release | NOT AUTHORIZED / NOT PUBLISHED |

Final review boundary: **SDK PLANNING READY FOR REVIEW**. Independent GPT review
may accept or request revision of this plan. Neither a docs-only CI pass nor a
planning merge would mean SDK IMPLEMENTED or npm publication approved.
