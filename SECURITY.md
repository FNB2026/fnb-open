# Security Policy

## Reporting a Vulnerability

**Please do not create public GitHub issues for security vulnerabilities.**

Report vulnerabilities privately via one of the following channels:

1. **GitHub Security Advisory** — navigate to the repository's "Security" tab and click "Report a vulnerability"
2. **Contact the project maintainer directly** — via the contact information available in the commit history or repository profile

### What to include

- Repository name and branch
- Type of vulnerability (e.g., XSS, SQL injection, secret exposure, authentication bypass)
- Steps to reproduce (use synthetic data only — do not include real personal data in reports)
- Affected files or endpoints (if known)
- Impact assessment
- Suggested fix (optional)

### Response SLA

| Event | Target Time |
|-------|-------------|
| Initial acknowledgment | Within 48 hours |
| Preliminary assessment | Within 7 days |
| Fix or mitigation plan | Within 30 days (or explanation of delay) |
| Public disclosure (after fix) | Coordinated with reporter |

---

## Sensitive Data Policy

**Do not submit the following to any public repository or issue tracker:**

| Category | Examples |
|----------|----------|
| Real chat logs | Any private conversation content |
| Real photos or media | User photos, videos, audio recordings |
| Real contact lists | Names, phone numbers, email addresses |
| Real relationship data | Relationship graphs with real identities |
| Real tokens | JWT, OAuth tokens, session tokens |
| Real API keys | Cloud service keys, access keys |
| Real database URLs | Connection strings with credentials |
| Real NAS paths | Local or network storage paths with real user names |
| Real device identifiers | IMEI, device serials, MAC addresses |

If you discover any of the above in a public repository, report it via the vulnerability channels above — do not discuss it in public issues.

---

## AI Safety and Data Sovereignty

FNB is built on the principle that **AI should not silently own, rewrite, or trade human memory and relationships**.

Any change that allows AI-generated results to modify user-owned memory, relationship, permission, or identity objects must include:

1. **Input reference** — what input data was used
2. **Model identity** — which model produced the output
3. **Confidence score** — how confident the model is
4. **AIInference record** — structured inference ledger entry
5. **Explanation record** — human-readable explanation of the inference
6. **User correction path** — how the user can confirm, reject, or rewrite
7. **Audit trail** — full event history of the inference and its consequences

---

## Plugin Security

Plugins must declare:

- **Data read scope** — what data the plugin reads
- **Data write scope** — what objects the plugin creates or modifies
- **External network behavior** — whether the plugin contacts external services
- **AI provider behavior** — whether the plugin uses external AI models
- **Storage behavior** — whether the plugin stores data externally
- **Audit behavior** — whether the plugin writes audit records

### Plugin Prohibitions

Plugins must NOT:

- Exfiltrate user data without consent
- Train on user data by default
- Bypass permission boundaries
- Bypass audit records
- Bypass user correction (confirm/reject/rewrite)
- Write final Relationship objects without Evidence
- Write final Memory objects without MemorySource
- Externalize FNB Credit into tradable assets
- Use the FNB official brand identity without authorization

---

## Supply Chain Security

- All dependencies are scanned via Dependabot or GitHub dependency graph
- Pull requests that introduce new dependencies require maintainer review
- Unmaintained or abandoned dependencies should be replaced
- Lock files (`go.sum`, `package-lock.json`) must be kept in version control

---

## Scope

This security policy covers:

- The `FNB2026/fnb-open` public showcase repository
- The `FNB2026/fnb-protocol` protocol and SDK repository
- Future selectively open-sourced engineering modules

It does **not** cover the private official implementation repository (`FNB2026/FNB`). Security issues related to the private repository should be communicated through established internal channels.
