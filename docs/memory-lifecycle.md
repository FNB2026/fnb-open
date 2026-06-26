# Memory Lifecycle

Memory in FNB is a **first-class domain object** — not a side effect of content consumption or a byproduct of AI summarization.

## Memory Sources

Every Memory must have a traceable source:

| Source Type | Examples |
|-------------|----------|
| Imported chat | WeChat, Telegram, WhatsApp exports |
| Direct message | IM messages within FNB |
| Photo / media | Camera roll, album imports |
| Voice / audio | Voice messages, recordings, transcripts |
| System event | Location, calendar, device activity |
| AI inference | Model-generated suggestions, summaries |
| Manual entry | User-created notes, annotations |

## Memory States

```
raw → candidate → confirmed → archived → deleted
                → rejected → (remains as raw)
```

- **raw** — ingested but unprocessed
- **candidate** — AI-suggested, waiting for user review
- **confirmed** — user-approved, fully active
- **archived** — user-hidden but not deleted
- **deleted** — soft-deleted, recoverable for a period

## Memory Properties

| Property | Description |
|----------|-------------|
| source | Traceable origin (MemorySource reference) |
| owner | User who owns this memory |
| confidence | AI confidence score (if AI-generated) |
| visibility | Private, shared, or public scope |
| lifecycle | Current state in the lifecycle |
| scores | Relevance, recency, importance metrics |
| evidence | Supporting data or references |

## Memory Governance

- **Users can delete** any memory they own
- **AI cannot permanently delete** user memories
- **AI suggestions** require user confirmation before becoming canonical
- **Redaction** preserves the event but hides the content
- **Export** includes all memory metadata and sources
