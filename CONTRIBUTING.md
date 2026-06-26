# Contributing to FNB Open

Thank you for your interest in FNB.

FNB is not just a software project. It is a **local-first personal memory operating system and AI social protocol** centered on data sovereignty, explainable AI, and user-governed relationships.

Before contributing, please read:
- [MANIFESTO.zh-CN.md](./MANIFESTO.zh-CN.md) — understand the philosophy
- [docs/open-source-boundary.md](./docs/open-source-boundary.md) — understand what is and isn't public
- [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) — community guidelines

---

## What We Welcome

- Documentation improvements and translations
- Synthetic examples and demo scenarios
- Domain model discussions and schema proposals
- Protocol RFCs
- SDK improvements (TypeScript, Go)
- Privacy and security reviews
- Accessibility reviews
- Local-first design feedback
- Bug reports with synthetic reproduction steps

## What We Do NOT Accept

PRs and contributions that:

- Include **real personal data** (names, chat logs, photos, audio, contacts)
- **Bypass user confirmation** for AI-generated content
- **Weaken auditability** of data operations
- **Turn FNB Credit into tradable tokens** or speculative assets
- **Default to cloud-only storage** without local-first fallback
- **Treat relationships as simple friend lists** without evidence
- Add **opaque AI mutation** without AIInference and Explanation records
- Include **production secrets, API keys, tokens, or private keys**

Such contributions will be rejected without review.

---

## Contribution Workflow

### 1. Start with a Discussion or Issue

For minor fixes (typos, example corrections), open an Issue directly.

For protocol changes, new features, or architecture discussions, start a **GitHub Discussion** first.

### 2. Create an RFC (for major changes)

All protocol-level changes, new domain objects, or changes affecting data sovereignty must go through the RFC process. See [rfcs/0000-rfc-process.md](./rfcs/0000-rfc-process.md).

### 3. Use Synthetic Data Only

**Never** submit real personal data — not in examples, tests, screenshots, or documentation.

Use our synthetic personas:
- **Alice Chen**
- **Ben Lin**
- **Mira Zhou**
- **System Agent**
- **Local Device**

### 4. Code Standards

**Go backend:**
- Run `go test ./...` and `go vet ./...` before submitting
- Follow [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- Domain logic belongs in `domain/`, not in services or handlers

**TypeScript/React:**
- Run `npx tsc --noEmit` before submitting
- Follow the existing code style (Prettier + ESLint)

**Documentation:**
- Write in clear, plain language
- For Chinese translations, match the original tone and structure

### 5. Submit a Pull Request

1. Fork the repository
2. Create a feature branch from `main`
3. Commit your changes (use clear, descriptive commit messages)
4. Push and open a PR against `main`
5. Fill out the PR template, including the **Data Sovereignty Checklist**
6. Wait for maintainer review

---

## Data Sovereignty Requirement

Every protocol or code contribution must answer:

- **Who owns the data?**
- **Who can read it?**
- **Who can infer from it?**
- **Who can train on it?**
- **How can the user revoke it?**
- **How is the operation audited?**
- **How can the user correct AI mistakes?**

If your change affects any of these, it must be explicitly documented in the PR or RFC.

---

## Review Process

| Type | Process | Expected Time |
|------|---------|---------------|
| Typo / formatting fix | Direct PR merge | 1-3 days |
| Documentation | PR review by maintainer | 3-7 days |
| Synthetic examples | PR review by maintainer | 3-7 days |
| SDK improvement | PR review + conformance check | 1-2 weeks |
| Protocol schema change | RFC + maintainer review | 2-4 weeks |
| Security-sensitive change | Security review required | depends |
| Data sovereignty change | Founder / Core Maintainer must approve | depends |

---

## Communication Channels

- **GitHub Discussions**: General Q&A, philosophy, feature ideas
- **GitHub Issues**: Bug reports, documentation issues
- **Security Advisories**: Private vulnerability reports only (see [SECURITY.md](./SECURITY.md))

---

## License

By contributing, you agree that your contributions will be licensed under the repository's applicable license:
- **Documents**: CC BY-NC-SA 4.0
- **Protocol/SDK repositories**: Apache 2.0 or as stated
- **Official implementation (future)**: AGPL v3

This repository currently accepts documentation, governance, RFC, and synthetic
example contributions. It is not a general-purpose open-source code release;
future code repositories or directories will state their own license.
