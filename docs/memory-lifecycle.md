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
source material → candidate → confirmed
                          ↘ rejected
```

- **candidate** — AI-suggested, waiting for user review
- **confirmed** — user-approved, fully active
- **rejected** — reviewed and rejected; remains auditable but is not canonical

Raw imported material is a source object, not a Memory status. Memory confirmation
is independent from its retention lifecycle:

- **active** — available under its current permissions
- **archived** — user-hidden but retained
- **redacted** — content hidden while an audit record remains
- **deleted** — soft-deleted and recoverable only under the implementation's policy

## Memory Properties

| Property | Description |
|----------|-------------|
| source | Traceable origin (MemorySource reference) |
| owner | User who owns this memory |
| confidence | AI confidence score (if AI-generated) |
| visibility | Private, shared, or public scope |
| status | Candidate, confirmed, or rejected user-governance state |
| lifecycle_state | Active, archived, redacted, or deleted retention state |
| scores | Relevance, recency, importance metrics |
| evidence | Supporting data or references |

## Memory Governance

- **Users can delete** any memory they own
- **AI cannot permanently delete** user memories
- **AI suggestions** require user confirmation before becoming canonical
- **Redaction** preserves the event but hides the content
- **Export** includes all memory metadata and sources
