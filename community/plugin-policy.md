# Plugin Policy

## Overview

FNB supports a plugin ecosystem for extending functionality. This policy defines the rules, rights, and responsibilities of plugin authors.

## Plugin Categories

| Category | Examples |
|----------|----------|
| Import | WeChat, Telegram, Markdown, photo import |
| AI | OCR, ASR, captioning, summarization, relationship inference |
| Storage | Local FS, NAS, S3, MinIO, WebDAV |
| Visualization | Timeline, graph view, block board, relationship map |
| Privacy | Redaction, blur, anonymization, policy check |
| Export | Markdown, JSON, archive, personal data package |
| Device | Mobile, desktop, NAS, edge worker |

## Plugin Requirements

Every plugin must declare:
1. Data it reads
2. Objects it creates or modifies
3. External service connections
4. AI provider usage
5. Storage backends used
6. Audit behavior
7. Offline capability
8. User consent requirements

## Plugin Prohibitions

Plugins must NOT:
- Exfiltrate user data
- Train on user data without explicit permission
- Bypass permission boundaries
- Bypass audit records
- Bypass user correction
- Write final Relationship objects without Evidence
- Write final Memory objects without MemorySource
- Externalize FNB Credit into tradable assets
- Use FNB brand without authorization

## Plugin Certification Levels

| Level | Description |
|-------|-------------|
| Unverified | Not reviewed, user assumes risk |
| Reviewed | Code review completed |
| Privacy-Safe | Privacy boundary check passed |
| Local-First | Fully offline-capable |
| Official | Maintained or deep-certified by FNB team |
