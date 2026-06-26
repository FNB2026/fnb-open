# Relationship Model

Relationships in FNB are not simple friend lists or connection graphs. They are **evidence-backed, user-governed, auditable domain objects**.

## Core Concepts

- **Relationship** — a declared connection between two or more actors
- **RelationshipParticipant** — an actor's role within a relationship
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

## Relationship States

```
suggested → confirmed → active → archived → dissolved
         → rejected
```

- **suggested** — AI-detected, waiting for user review
- **confirmed** — user-approved relationship
- **active** — currently relevant and used
- **archived** — preserved but inactive
- **dissolved** — relationship formally ended

## Permission Model

- Each relationship has an owner (the user)
- Participants can have different permission levels (view, infer, train, export)
- AI can suggest relationships but **cannot create confirmed relationships** without user approval
- Relationship evidence is auditable and cannot be silently deleted
