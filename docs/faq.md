# Frequently Asked Questions

## Is FNB production-ready?

Not yet. FNB is in Alpha / internal testing. The domain model is well-defined and the backend is functional, but the mobile app and web console are still under active development.

## Is FNB a blockchain project?

No. FNB is a local-first personal memory operating system. It does not require blockchain, tokens, mining, or any Web3 infrastructure. While it may incorporate cryptographic signatures and integrity verification, these do not depend on a blockchain.

## How is FNB different from a notes app?

Notes apps treat memories as static text. FNB treats memories as structured, source-tracked, relationship-aware domain objects with full audit and AI explainability. Memories have sources, evidence, confidence scores, and lifecycle states that notes apps don't support.

## How is FNB different from a CRM?

CRMs are designed for businesses to manage customer relationships. FNB is designed for individuals to manage their personal relationships. FNB focuses on evidence-backed relationship models, user-governed connections, and AI-assisted relationship discovery — not sales pipelines or contact scoring.

## Will FNB have a token or cryptocurrency?

No. FNB Credit (if implemented) would be a local accounting mechanism for usage tracking, not a tradable asset or investment vehicle.

## Can I contribute?

Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines. We welcome documentation, synthetic examples, protocol discussions, and privacy reviews.

## Does FNB use my data for AI training?

Not without your explicit consent. FNB's permission model has a specific "training" action that you must grant before any data is used for model training.

## Can I run FNB fully offline?

Eventually yes. The architecture is local-first, and offline-capable operation is a design goal. The current Alpha requires a local server for development.

## What license does FNB use?

- Documents: CC BY-NC-SA 4.0
- Protocol/SDK repos: Apache 2.0
- Official implementation (future public modules): AGPL v3

The current `fnb-open` repository is a public documentation and protocol-draft
repository. Because the documentation license includes a non-commercial term, it
should not be described as an OSI open-source code release.
