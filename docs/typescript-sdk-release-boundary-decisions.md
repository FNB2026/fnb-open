# TypeScript SDK Release Boundary — Decisions and Acceptance Gates

Status: **PROPOSED / PLANNING ONLY**. Read with the
[release boundary plan](typescript-sdk-release-boundary-plan.md).
Implementation is CLOSED / ESTABLISHED; publication is BLOCKED / NOT AUTHORIZED.
All decisions below await independent planning review. No release commands,
credentials, workflow changes or SDK code are delivered by this PR.

## Proposed decisions

| ID | Decision | Boundary / future evidence |
| --- | --- | --- |
| R01 | GitHub Preview before npm | Two separate approvals; no registry bootstrap for A |
| R02 | SDK `0.1.0-preview.1`; tag `object-exchange-ts-sdk-v0.1.0-preview.1` | Proposed in approved SDK plan; target is future reviewed release-candidate SHA |
| R03 | GitHub prerelease, not stable | No production service or private Alpha guarantee |
| R04 | Node 22 ESM/native fetch only | Secure supported patch pinned in preparation; EOL schedule disclosed |
| R05 | Wire `1.0`, schema `v0.1.0-preview.1` | Existing frozen transport/schema/bindings unchanged |
| R06 | Exactly 28 package paths | Exact allowlist in plan; fail on extra/missing/duplicate/unsafe members |
| R07 | Path A retains private workspace package label | Local tarball install only; no official npm name or registry identity implied |
| R08 | Preserve license, NOTICE and marks | Consumer README/NOTICE truth sync in later preparation, not historical ledger rewrite |
| R09 | Embedded development inventory distinct from release SPDX SBOM | External SBOM describes actual archive/files and separates build/runtime |
| R10 | External manifest and provenance after source commit | Six assets + 28-member inventory; manifest excludes itself; no hash cycles |
| R11 | Signed annotated SDK tag binds manifest digest | Approved key/fingerprint; no automatic unsigned fallback; no tag replacement |
| R12 | Two isolated declared-environment builds match bytes | Pin toolchain and dependency locks; offline consumer, no lifecycle scripts |
| R13 | Immutable Releases and public read-back required | Verify repository setting; Draft with all seven uploads, publish then verify immutable state/attestation, tag/signature and digests; unavailable protection needs separate reduced-guarantee approval |
| R14 | Failures/corrections use incident decision and new version | No force, silently replaced assets or assumed reversible npm publication |
| R15 | npm scope/ownership/OIDC/provenance/dist-tag independently approved | Separately reviewed B candidate must remove `private: true` or set false (necessary, not sufficient authority); A retains true; identity changes get new reviewed artifact; no `latest` preview |
| R16 | New LTS support requires separate tests/decision | No automatic widening engines or Node/browser/CJS claims |

## Future executable acceptance matrix

NOT RUN means not performed by this planning PR; earlier implementation test
results are baseline evidence only, not completion of release gates.

| Gate | Reproducible check / rejection condition | Applies to | Current state |
| --- | --- | --- | --- |
| G01 | Docs-only diff: exactly the two new planning docs; frozen paths and tags unchanged | Planning | Verify in this PR |
| G02 | Independent planning review records exact HEAD and all decisions | Planning | PENDING |
| G03 | Clean candidate checkout; source/dependency commits and byte manifests verified | A/B | NOT RUN |
| G04 | Runtime/compiler/npm/Python/tools pinned; supported/security status and license audit recorded; unresolved risk blocks | A/B | NOT RUN |
| G05 | Generator --check, build and typecheck; immutable declaration snapshot hashes | A/B | NOT RUN for release candidate |
| G06 | Full SDK matrix including strict parser/races/native HTTP; Python 51 tests ordinary and -O; three exact-head jobs green | A/B | Baseline passed; fresh candidate NOT RUN |
| G07 | Two clean same-toolchain packs identical SHA-256 and member bytes | A/B | NOT RUN for release candidate |
| G08 | Exact 28 regular-file paths, safe archive names/modes, no secrets/unexpected files; mutated extra/missing/path/duplicate fixtures rejected | A/B | NOT RUN |
| G09 | Offline tarball install, ESM runtime and NodeNext types, synthetic Mock exchange; no runtime deps/hooks | A/B | NOT RUN for release candidate |
| G10 | README/NOTICE and notes describe actual preview/package/runtime/support; no Draft or npm-identity misstatement | A/B | NOT RUN; consumer docs need preparation |
| G11 | Root and packed licenses equal; original 14 domain hashes and attributions retained | A/B | NOT RUN for release candidate |
| G12 | Embedded dev inventory labelled; external SPDX schema/file/license checks match actual archive; no signed-attestation claim | A/B | NOT RUN |
| G13 | Manifest exact six-asset set and 28-member inventory; altered bytes/length/hash/missing/extra entries fail | A/B | NOT RUN |
| G14 | External provenance binds final commit/toolchain/locks/build run and upstream sources; no private data/local paths; independent review | A/B | NOT RUN |
| G15 | Signing identity verified independently; manifest digest/tag target approved; unsigned exception separately approved if needed | A | UNDECIDED key / BLOCKED |
| G16 | Explicit authority binds version, candidate SHA, tag, manifest hash, evidence set and prerelease action | A | NOT AUTHORIZED |
| G17 | Verify repository Immutable Releases setting; absent candidate tag; all seven approved uploads verified in Draft before publish; published immutable flag and GitHub attestation verified independently alongside tag/signature/digests/main CI; unavailable protection requires prior explicit reduced-guarantee exception | A | NOT RUN / NOT AUTHORIZED |
| G18 | Official npm identity/ownership/access and initial setup approved; credential/OIDC permissions scoped, reviewer-protected job | B | UNDECIDED / NOT AUTHORIZED |
| G19 | Registry provenance eligibility/verification and trust configuration rechecked; failure blocks, no token fallback by inference | B | NOT RUN / NOT AUTHORIZED |
| G20 | Distinct npm candidate identity/version reviewed and `private: true` removed or false; required technical prerequisite never grants authority; preview dist-tag and irreversible-publication/incident policy approved | B | UNDECIDED / NOT AUTHORIZED |
| G21 | Explicit npm publish authority and downloaded registry tarball/provenance checks | B | NOT AUTHORIZED |
| G22 | New-LTS migration proposal before Node 22 EOL, full matrix on new runtime before support claim | Later | PLANNING REQUIRED |

## Approval boundaries still requiring human decisions

Planning review can approve the proposed path A mechanism and file inventory.
It cannot provide the future candidate SHA, real artifact hashes, signing key
identity, verified security/toolchain state or publication authority. Those
values are intentionally absent, not fabricated. Path B's package scope,
ownership, bootstrap/OIDC/provenance configuration and preview dist-tag must
remain separate decisions; `private: true` remains untouched here.
Platform release attestation is separate verification metadata, never an input
to the six-asset/self-excluding manifest. No immutability setting is changed here.

Deliver exact planning HEAD, complete diff, docs check and all three CI results
in the independent Draft PR. Do not merge before independent planning review.
No tag, GitHub Release, npm package or publishing credential is created even
if this planning CI passes.
