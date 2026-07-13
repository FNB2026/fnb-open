# Relationship Model

Relationships in FNB are not simple friend lists or connection graphs. They are **evidence-backed, user-governed, auditable domain objects**.

## Core Concepts

- **Relationship** — an evidence-backed context connecting two or more actors
- **RelationshipAssertion** — one participant's own relationship description and confirmation state
- **RelationshipEvidence** — the evidence supporting a relationship claim

## Evidence Requirements

Every relationship must have at least one piece of evidence:

| Evidence Type | Examples |
|---------------|----------|
| Direct message | Chat logs, conversation threads |
| Shared event | Meetings, trips, activities |
| Mutual contact | Introductions, referrals |
| AI inference | Model-suggested relationship (requires user confirmation) |
| Manual declaration | User explicitly states a relationship |

## Participant Assertions

FNB does not collapse every participant's view into one global relationship
label. Each assertion records:

- the participant making the assertion;
- that participant's relationship description;
- `candidate`, `confirmed`, `rejected`, or `contested` confirmation state;
- a confirmation event and timestamp for confirmed assertions;
- the assertion's own visibility scope.

The Relationship itself has only a retention/dispute lifecycle: `active`,
`contested`, or `redacted`. Two participants may legitimately hold different
private assertions about the same evidence.

## Permission Model

- Each participant controls their own assertion and visibility scope
- Participants can have different permission levels (view, infer, train, export)
- AI can propose candidate assertions but **cannot confirm an assertion** without that participant's decision
- Relationship evidence is auditable and cannot be silently deleted
