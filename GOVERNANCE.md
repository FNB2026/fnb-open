# FNB Governance

This document describes the governance model of the FNB open-source ecosystem.

FNB is not just a software project — it is a protocol and philosophy around **data sovereignty, personal memory, explainable AI, and user-governed relationships**. Its governance must reflect these values.

---

## Governance Principles

1. **User sovereignty first** — governance decisions must never weaken user data control
2. **Protocol integrity** — the core protocol must not be fragmented by incompatible forks
3. **Transparency** — major decisions are made through RFCs and public discussion
4. **Inclusion** — contributions are welcome from all who respect the philosophy

---

## Project Steward

The project has a single **Steward** (the founder/creator) who holds the following reserved powers:

| Power | Purpose |
|-------|---------|
| FNB name and definition authority | Ensure "FNB" means what it was designed to mean |
| Official roadmap final decision | Protect long-term vision from short-term pressure |
| Main protocol version release | Prevent protocol fragmentation |
| Official repository merge right | Audit and quality control on the canonical implementation |
| Official compatibility certification | Define what "FNB-compatible" means |
| Security incident handling | Fast response without governance delays |
| Brand and logo usage | Prevent impersonation and brand dilution |
| Economic system activation | Prevent premature or exploitative economic mechanisms |
| Data sovereignty veto | Override any change that weakens user data control |

These powers are not for arbitrary use — they exist to **protect the project's founding philosophy** from being diluted by short-term commercial, technical, or community pressure.

---

## Maintainer Hierarchy

```
Project Steward
├── Core Maintainers
│   ├── Protocol Maintainers      — schema, RFC, conformance
│   ├── SDK Maintainers           — TypeScript, Go SDKs
│   ├── Docs Maintainers          — documentation, translations
│   ├── Security Reviewers        — vulnerability assessment
│   ├── Plugin Reviewers          — plugin ecosystem
│   └── Community Moderators      — discussions, conduct enforcement
└── Contributors
```

### Core Maintainers

- Appointed by the Project Steward
- Responsible for the overall health of the project
- Vote on protocol RFCs (Steward has final say)
- Can veto changes that violate project philosophy

### Maintainer Types

- **Protocol Maintainers**: Review and merge changes to spec/, schema/, and RFCs
- **SDK Maintainers**: Review and merge changes to packages/ and SDK code
- **Docs Maintainers**: Review and merge documentation and translation PRs
- **Security Reviewers**: Review security-sensitive changes; handle vulnerability reports
- **Plugin Reviewers**: Review plugin ecosystem contributions
- **Community Moderators**: Enforce Code of Conduct; manage Discussions

### Becoming a Maintainer

1. Consistently contribute high-quality PRs
2. Demonstrate understanding of FNB philosophy
3. Be nominated by an existing maintainer or self-nominate
4. Approved by the Project Steward or Core Maintainer vote

---

## Community Member Types

### Type A: Philosophy Aligners

Contributions: Discussions, philosophy reviews, translations, articles
Permissions: Discussions, doc PRs, RFC comments

### Type B: Protocol Contributors

Contributions: Schema design, OpenAPI drafts, type definitions, conformance tests
Permissions: `fnb-protocol` PRs, RFC proposals

### Type C: Engineering Contributors

Contributions: SDK, Mock server, synthetic importer, UI shell, plugin starters
Permissions: Module-level maintenance (no private repo access)

### Type D: Privacy & Security Researchers

Contributions: Permission model review, audit mechanism review, data deletion review
Permissions: Security advisory, private vulnerability reports

### Type E: Plugin Authors

Contributions: Import plugins, album plugins, AI plugins, storage plugins
Permissions: Plugin repository, review process, compatibility certification

---

## Decision-Making Process

| Change Type | Process | Approval |
|-------------|---------|----------|
| Documentation fix | Direct PR | Maintainer review |
| Synthetic examples | Direct PR | Maintainer review |
| Protocol minor change | Issue + discussion | Maintainer review |
| Protocol major change | RFC | Core Maintainer + Steward |
| Security change | Security review | Security Reviewer + Steward |
| Data sovereignty change | RFC + Steward review | Steward must approve |
| Economic system change | RFC + public discussion | Steward must approve |
| Governance change | RFC + public discussion | Steward must approve |

### RFC Lifecycle

```
Draft → Discussion → Revision → Accepted/Rejected/Superseded
```

See [rfcs/0000-rfc-process.md](./rfcs/0000-rfc-process.md) for the full RFC process.

---

## Compatibility and Forking

### Official FNB

- Maintained by the Project Steward and Core Maintainers
- The only implementation that can use the "Official FNB" designation
- Must pass all conformance tests

### Third-Party Implementations

- Can implement the FNB protocol independently
- Must pass conformance tests to claim "FNB-compatible"
- Must not use the FNB brand, logo, or "Official" designation without authorization

### Forks

- Are permitted (AGPL v3 allows it)
- Must clearly state they are a fork and not "Official FNB"
- Must not use the FNB brand assets
- Are encouraged to contribute improvements upstream via PRs or RFCs

---

## License

- **Documents** (MANIFESTO, docs/): CC BY-NC-SA 4.0
- **Protocol schemas** (specs/, openapi/): CC BY 4.0 or Apache 2.0
- **SDKs and tools** (packages/): Apache 2.0
- **Official implementation** (future public modules): AGPL v3
- **Brand and logo**: Reserved to the Project Steward — see [TRADEMARK.md](./TRADEMARK.md)

---

## Amendments

This governance document can be amended through:

1. An RFC with "Governance" type
2. Public discussion period (minimum 14 days)
3. Approval by the Project Steward

Minor clarifications and typo fixes do not require the full process.
