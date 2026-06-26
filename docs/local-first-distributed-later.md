# Local-First, Distributed Later

FNB is designed as a **local-first** system. The default deployment is on the user's own device or local network.

## Local-First Principles

1. **Offline-capable** — all core functions work without internet
2. **Local storage default** — data lives on the user's device
3. **Sync is additive** — cloud sync is optional, not required
4. **No vendor lock-in** — users choose their storage backend
5. **Privacy by design** — no data leaves the device without explicit user action

## Supported Storage Backends (Planned)

- **Local filesystem** — default, works out of the box
- **NAS** — Synology, QNAP, TrueNAS via SMB/NFS
- **Private cloud** — MinIO, S3-compatible storage
- **Cloud sync** — optional encrypted sync (future)
- **P2P / edge** — distributed storage evaluation (future)

## Why Local-First?

For a personal memory operating system, cloud-only is unacceptable:

- Your memories should not depend on a company's servers
- Your relationship data should not leave your control
- Your AI inferences should run locally when possible
- Your data should survive platform shutdowns
- Your privacy should not depend on a privacy policy
