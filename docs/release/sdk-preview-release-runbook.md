# FNB Object Exchange TypeScript SDK Preview — Release Runbook

Status: **PLAN ONLY / NOT EXECUTED.** The SDK is **not released**. SDK publication is
**BLOCKED / NOT AUTHORIZED** (`publication_authorized = false`; `G16 = NOT AUTHORIZED`).
This document describes *how a future, separately-authorized release must be performed*.
It does not authorize any release, tag, asset upload or package publication.

Applies to candidate version: `0.1.0-preview.1` (GitHub Preview Path A, `private: true`).

---

## 0. Preconditions (must all be true before Phase 1)

| # | Precondition | How verified | Current |
| --- | --- | --- | --- |
| 0.1 | Release evidence independently reviewed against the **final** source commit | `A2.md` + independent audit | ✅ (R3 audit PASS, commit `a2f749f`) |
| 0.2 | Signing identity approved; public key + policy published on the independent channel | `https://trust.fnbapp.net/` | ✅ |
| 0.3 | GitHub **Immutable Releases enabled** for the repo | `GET /repos/FNB2026/fnb-open/immutable-releases` → `enabled` | ✅ `enabled: true` |
| 0.4 | Candidate tag name **not already used** | `git ls-remote --tags origin` | ✅ free |
| 0.5 | Explicit **publication authorization** (G16) for this exact version/SHA/tag/manifest/asset set | Human decision record | ❌ **NOT AUTHORIZED** |
| 0.6 | **gpg-agent passphrase cache is COLD** and a human is present to confirm the pinentry prompt | `gpgconf --kill all` + observe a prompt at Tag step | ⚠️ **enforce before signing** |

> **Phase 1 must not start while 0.5 is unmet.**

> **Finding (dry-run, 2026-10-14):** a rehearsal signature over the exact tag message was produced
> **without any pinentry prompt**, because `gpg-agent` had a warm passphrase cache. A real Phase 1
> tag could therefore be signed **silently with no human in the loop**. Precondition 0.6 must be
> actively enforced (clear the cache immediately before signing) and the prompt must be **recorded**
> as a Phase 2 confirmation item.

---

## Phase 0 — Pre-release freeze

Record the frozen values. Any change after freeze requires restarting this runbook.

| Frozen value | Value (reference) | Command |
| --- | --- | --- |
| `MAIN_SHA` (baseline) | *(read live)* | `git ls-remote origin refs/heads/main` |
| `TAG_TARGET` (reviewed source commit) | `a2f749f3e1193f586c6d870946894f1abff893fb` | `git cat-file -t "$TAG_TARGET"` |
| `TAG_NAME` | `object-exchange-ts-sdk-v0.1.0-preview.1` | `git ls-remote --tags origin "$TAG_NAME"` (expect empty) |
| `MANIFEST_SHA256` | `365156df8c9eeb567989b24cc737a378109fc043f00a3270838939268832d250` | `shasum -a 256 artifact-digests.json` |
| `SIGNING_KEY_FPR` | `1986135564B368B8DD3B5C6FB4D67D6F06FADC54` | `gpg --list-secret-keys` |
| `IMMUTABLE_ENABLED` | `true` | `gh api repos/FNB2026/fnb-open/immutable-releases` |
| `PACKAGE` | `fnb-object-exchange-sdk-workspace@0.1.0-preview.1`, `private: true` | `cat package.json` |

Freeze rules:
- `TAG_TARGET` must be the commit the **release evidence binds to** (`provenance.commit == manifest.commit == TAG_TARGET`).
- `MANIFEST_SHA256` must equal the digest bound into the tag message (Phase 1) and printed on the identity channel.
- Re-verify `MAIN_SHA` immediately before Phase 1; if main moved, re-check whether the frozen artifacts are still valid.

---

## Phase 1 — Create the signed tag

The tag is **annotated** and **signed** (OpenPGP, approved key). It is created locally and pushed
**only after** G16 authorization.

Canonical tag message (byte-exact; the file is the source of truth):

```text
FNB Object Exchange TypeScript SDK Preview

manifest-sha256: 365156df8c9eeb567989b24cc737a378109fc043f00a3270838939268832d250
```

Commands (do **not** run before authorization):

```bash
# 1) write the canonical message to a file (no trailing edits afterwards)
cat > /tmp/tag-message.txt <<'EOF'
FNB Object Exchange TypeScript SDK Preview

manifest-sha256: 365156df8c9eeb567989b24cc737a378109fc043f00a3270838939268832d250
EOF

# 2) FORCE A COLD CACHE so signing cannot happen silently.
#    A warm gpg-agent cache will sign WITHOUT any pinentry prompt (observed in dry run).
#    Clearing the cache forces the human confirmation to actually occur.
gpgconf --kill all        # or: gpg-connect-agent 'RELOADAGENT' /bye  +  wait for cache expiry

# 3) create an annotated, SIGNED tag on the frozen target.
#    -s = sign with the approved key. A HUMAN MUST SEE AND CONFIRM THE PINENTRY PROMPT.
#    Record the timestamp at which the prompt appeared (Phase 2 confirmation item).
git tag -s -a "$TAG_NAME" -F /tmp/tag-message.txt "$TAG_TARGET"

# 4) LOCAL verification (Phase 2a) — MUST PASS BEFORE ANY PUSH
git verify-tag "$TAG_NAME"            # good signature from the approved key
git cat-file -p "$TAG_NAME"           # annotated tag object + message
git rev-parse "$TAG_NAME^{commit}"    # == $TAG_TARGET

# 5) push ONLY the tag (never push a branch to main)
git push origin "refs/tags/$TAG_NAME"

# 6) REMOTE read-back re-verification (Phase 2b), independently, after the push
git ls-remote origin "refs/tags/$TAG_NAME"
# then re-verify in a clean clone / clean GNUPGHOME (see Phase 2b)
```

Order is **local sign → local verify → push → remote read-back**. Never push before Phase 2a passes.

Rules:
- **Annotated + signed** required. A lightweight or unsigned tag is **unacceptable**.
- **Signing must be human-attended.** Because the agent cache may be warm, clearing it (`gpgconf --kill all`)
  before `git tag -s` is **mandatory**; a signature produced without any visible prompt is a **process
  failure** and must be handled per the failure-state rules below.
- The tag must point at `TAG_TARGET` (the reviewed source commit), **not** at a merge commit —
  this keeps `provenance.commit == manifest.commit == tag target` without regenerating evidence.
- **Failure handling depends on whether the tag has been pushed — these are two distinct states:**
  - **State A — tag is still LOCAL (not pushed):** abortable. `git tag -d "$TAG_NAME"`, clear the cache,
    and redo from step 3. Nothing published has changed.
  - **State B — tag has been PUSHED:** **STOP and escalate to a human.** Do **not** delete, move or
    re-create a pushed tag — that rewrites published history, and immutability may already lock it.
    **There is no automated rollback for a pushed tag.** Correction requires an explicit human decision
    (a new version/tag), never rewriting the pushed tag.

---

## Phase 2 — Verify the tag

Two stages: **2a local** (before push — abortable) and **2b remote read-back** (after push — **no rollback**).

### Phase 2a — local verification (before push)

```bash
git verify-tag "$TAG_NAME"            # expect a good signature from the approved key
git cat-file -p "$TAG_NAME"           # tag object type, target commit, message
git rev-parse "$TAG_NAME^{commit}"    # expect == $TAG_TARGET
```

Confirm:
1. **Signer fingerprint** == `1986135564B368B8DD3B5C6FB4D67D6F06FADC54` (compare full fingerprint, out of band).
2. **Tag object** is `tag` (annotated), not `commit` (lightweight).
3. **Target commit** == `TAG_TARGET` == the commit bound in `artifact-digests.json` / provenance.
4. **Tag message** is the single line `manifest-sha256: 365156df…32d250`, and the digest equals the actual manifest file.
5. **Human-attended signing**: a pinentry prompt was actually observed and confirmed during Phase 1 (timestamp recorded).

If any check fails while the tag is **still local** (State A) → discard and redo:

```bash
git tag -d "$TAG_NAME"    # LOCAL ONLY — never run this for a pushed tag
gpgconf --kill all
# redo Phase 1 from step 2
```

### Phase 2b — remote read-back (after push)

Independently re-verify from the remote (fresh worktree/clone + clean `GNUPGHOME`):

```bash
git ls-remote origin "refs/tags/$TAG_NAME"   # expect the ANNOTATED TAG object id (not the commit)
git fetch --tags origin
git verify-tag "$TAG_NAME"
git cat-file -p "$TAG_NAME"
git rev-parse "$TAG_NAME^{commit}"
```

Confirm the remote tag object, signer fingerprint, target commit and message digest all match Phase 2a.

**If Phase 2b fails after the tag has been pushed (State B) → STOP and escalate to a human.
Do not delete, move or roll back the pushed tag.** There is no automated recovery; correction
requires an explicit human decision (a new version/tag), never rewriting a pushed tag.

---

## Phase 3 — GitHub Release (draft → assets → attestation → immutable → publish)

Order matters. Publish **last**, so all assets exist before immutability locks the release.

```bash
# 3.1 create a DRAFT release against the ALREADY-EXISTING signed tag
gh release create "$TAG_NAME" \
  --repo FNB2026/fnb-open \
  --draft \
  --verify-tag \
  --title "FNB Object Exchange TypeScript SDK Preview 0.1.0-preview.1" \
  --notes-file RELEASE-NOTES.md

# 3.2 attach the SIX assets (names must match the manifest exactly)
gh release upload "$TAG_NAME" \
  --repo FNB2026/fnb-open \
  fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz \
  release-provenance.json \
  release-sbom.spdx.json \
  RELEASE-NOTES.md \
  LICENSE-APACHE-2.0.txt \
  NOTICE.md

# 3.3 verify uploaded asset digests equal the manifest BEFORE publishing
gh release view "$TAG_NAME" --repo FNB2026/fnb-open --json assets \
  --jq '.assets[] | "\(.name) \(.size)"'
#    → compare each sha256/size against artifact-digests.json

# 3.4 publish (this triggers immutability + release attestation)
gh release edit "$TAG_NAME" --repo FNB2026/fnb-open --draft=false --prerelease
```

Post-publish verification (required):

```bash
# release is immutable + not a full release (preview/prerelease)
gh release view "$TAG_NAME" --repo FNB2026/fnb-open \
  --json isImmutable,isPrerelease,isDraft,tagName,assets
#   expect: isDraft=false, tagName locks to $TAG_TARGET, assets = 6

# release attestation (auto-generated for immutable releases)
gh attestation verify fnb-object-exchange-ts-sdk-0.1.0-preview.1.tgz \
  --repo FNB2026/fnb-open
```

Notes:
- `--verify-tag` prevents `gh` from creating an unsigned tag.
- **Asset set — OPEN QUESTION for A0 (frozen baseline unchanged).** The frozen baseline is **six**
  assets. A2 recommends that **A0 adjudicate** whether the GitHub Release should carry **seven** files:
  the six assets **plus** the self-excluding `artifact-digests.json`. A manifest not listing itself does
  **not** forbid it from being attached to the Release. **The six-asset baseline must not be changed
  unilaterally** — this is a scope-change request awaiting explicit A0 adjudication.
- `artifact-digests.json` is **self-excluding** and remains the authored manifest referenced by the
  tag message; it is not listed inside itself.
- Immutability locks the **tag** and the **assets** after publish. `title` / `notes` / the
  `prerelease` flag **remain editable**.
- Immutability protects **future** releases only; the pre-existing `v0.1.0-preview.1` is unaffected
  (verified `isImmutable:false`).

**Command applicability (verified read-only, 2026-10-15).** GitHub CLI in use: `gh` **2.95.0**.
`gh attestation verify` is available; `gh release view --json isImmutable,isPrerelease,isDraft,tagName`
is supported (confirmed against the existing release, which reported `isImmutable:false`).
These commands have **not been executed** for a real release — they remain **NOT RUN, not PASS**.

Rollback rules (see also Phase 1 State A/B and Phase 2b):
- A **pushed** tag has **no automated rollback** — correcting it requires an explicit human decision
  and a **new version/tag**; never rewrite a pushed tag.
- A **draft release** (not yet published) may be discarded before publish.
- **After publish → no rollback**: immutability locks the tag and assets; correction requires a
  **new version/tag**, never replacement of published bytes.

---

## Phase 4 — npm (only if a future, separate decision authorizes it)

**Not authorized. Not planned for this preview.** Requires its own approval covering:
package identity, registry/account, 2FA/token scope, provenance (`--provenance`), and whether the
GitHub asset set is identical. `private: true` must be resolved in the published manifest only if
that separate decision explicitly allows it. This runbook does not authorize any `npm publish`.

---

## Failure modes and required behavior

| Situation | Required action |
| --- | --- |
| `main` moved after freeze | Re-freeze; re-check whether evidence still binds; if artifacts changed, regenerate + independently review **before** proceeding |
| Tag already exists remotely | **Stop.** Never overwrite/force-move. Investigate provenance of the existing tag |
| **Local tag fails verification (State A, not pushed)** | Discard the local tag (`git tag -d`), clear cache, and redo. Nothing published has changed |
| **Pushed tag fails verification (State B)** | **Stop and escalate to a human.** No automated rollback; never delete/move/re-create a pushed tag. Correction = explicit human decision / new version-tag |
| Pushed tag needs correction | **Human decision only.** Never rewrite published history; immutability may already lock the tag |
| `git verify-tag` fails / unexpected signer | **Stop.** Do not create release. Investigate keys (branch by State A/B above) |
| Asset digest mismatch vs manifest | **Stop.** Do not publish. Fix the artifact, regenerate evidence, re-review |
| Immutable setting not enabled | **Stop.** Enable (repo-level) or obtain explicit reduced-guarantee approval; do not silently degrade |
| No one available for pinentry | **Stop.** Signing requires human confirmation; never automate the passphrase |
| Any CI/check red on the tagged commit | **Stop.** Release requires green checks on the frozen commit |

---

## Roles

| Step | Owner | Approver |
| --- | --- | --- |
| Freeze (Phase 0) | A2 | A0 |
| Tag + push (Phase 1–2) | A2 (human-present for pinentry) | G16 authorization |
| Draft release + assets (Phase 3) | A2 | A0 |
| Publish (Phase 3.4) | **Requires explicit G16 authorization** | A0 / human |
| npm (Phase 4) | separate authorization only | A0 / human |

## Change control

This runbook is a plan. Any deviation during a real release must be recorded in the A2 report with
the exact commands, output, SHAs and the reason for deviation.
