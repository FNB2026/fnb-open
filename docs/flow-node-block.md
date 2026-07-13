# Flow / Node / Block

FNB's core data model is built on a three-layer abstraction:

## Flow

A **Flow** is the continuous stream of life — events, messages, activities, and changes over time.

- Every message, upload, import, or system event belongs to a Flow
- Flows are append-only: nothing is deleted from a Flow
- Flows provide the raw material for higher-level objects

Think of Flow as **runtime** — it's what happens.

## Node

A **Node** is a stable object extracted or derived from a Flow.

Nodes represent:
- People (actors, contacts, participants)
- Conversations (threads, rooms, sessions)
- Events (meetings, trips, milestones)
- Compute units (processing jobs, inferences)

Nodes have identity, state, and relationships. They are the **entities** that persist across time.

## Block

A **Block** is an aggregated, curated, or computed view built from Flow Events and Nodes.

Blocks represent:
- Knowledge summaries extracted from conversations
- Memory snapshots curated from events
- Asset collections grouped by theme or relationship
- Relationship evidence bundles

Blocks are the **high-value artifacts** — what the user ultimately owns and controls.

## Data Flow

```
Messages / Events → Flow → Node candidates → BlockDraft → User confirms → Block
                              ↓
                        Relationship evidence
                        Memory source tracking
                        Asset processing
```

Key principle: **AI output must not directly become a Block.** It must first
become a BlockDraft, then be confirmed, rejected, or rewritten by the user. A
durable AI-derived Block records the confirming actor, confirmation event,
operation, timestamp, and the source Draft; rewrites also retain the Correction.
